#!/bin/env perl

use strict;
use warnings FATAL => 'all';


# This should be used at first, due to we want to use a new enough runjobs4
use FindBin qw($Bin $Script);
use Cwd;

use File::Basename;
use File::Path;
use File::Copy;

package main;

my $textopen_root;
my $hume_repo_root;

BEGIN{
    $textopen_root = "/d4m/nlp/releases/text-open/R2020_08_21"; #BBN_MAGIC2
    $hume_repo_root = "/d4m/nlp/releases/Hume/R2022_03_21"; #BBN_MAGIC1
    # $hume_repo_root = Cwd::abs_path(__FILE__ . "/../..");
    unshift(@INC, "/d4m/ears/releases/runjobs4/R2019_03_29/lib"); #BBN_MAGIC3
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
}

use runjobs4;
use Utils;

my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = startjobs("queue_mem_limit" => '7G', "max_memory_over" => '0.5G', "queue_priority" => $QUEUE_PRIO);

# Parameter loading
my $params = {};
my @stages = ();
if (scalar(@ARGV) < 1) {
    print "Input args that we got is EMPTY!!!!!!!!!";
    die "run.pl takes in one argument -- a config file";
}
else {
    print "Input args that we got is :";
    print join(" ", @ARGV), "\n";
    my $config_file = $ARGV[0];
    $params = load_params($config_file); # $params is a hash reference
    @stages = split(/,/, get_param($params, "stages_to_run"));
    @stages = grep (s/\s*//g, @stages); # remove leading/trailing whitespaces from stage names
}

my %stages = map {$_ => 1} @stages;
my $JOB_NAME = get_param($params, "job_name");

my $LINUX_QUEUE = get_param($params, "cpu_queue", "cpunodes");
my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "gpu-8G");

# Location of all the output of this sequence
(my $processing_dir, undef) = Utils::make_output_dir("$exp_root/expts/$JOB_NAME", "$JOB_NAME/mkdir_job_directory", []);

# Python commands
my $ANACONDA_ROOT = "";
if (get_param($params, "ANACONDA_ROOT", "None") eq "None") {
    $ANACONDA_ROOT = "/nfs/raid87/u11/users/hqiu/miniconda_prod";
}
else {
    $ANACONDA_ROOT = get_param($params, "ANACONDA_ROOT");
}

my $CONDA_ENV_NAME_FOR_CPU = "hat_new";
my $CONDA_ENV_NAME_FOR_GPU = "hat_new";

# Scripts
my $GENERATE_CANDIDATES_SCRIPT = "$hume_repo_root/src/python/concept_discovery/generate_all_verbs_and_name_nouns_ljson.py";
my $CORPUS_CACHE_SCRIPT = "$hume_repo_root/src/python/concept_discovery/generate_bert_cache.py";
my $SIMILARITY_SCRIPT = "$hume_repo_root/src/python/concept_discovery/generate_pairwise_and_vocab_for_cbc.py";
my $GENERATE_CBC_PARAMS_SCRIPT = "$hume_repo_root/src/python/concept_discovery/generate_cbc_params.py";
my $RUN_CBC_COMMAND = "java -cp $hume_repo_root/src/java/novel-events/necd-cluster/target/necd-cluster-1.0.0-SNAPSHOT-jar-with-dependencies.jar com.bbn.necd.cluster.bin.RunCBC";
my $EMBEDDING_FINDER_SCRIPT = "$hume_repo_root/src/python/ontology_centroid_helpers/embedding_finder.py";
my $MAP_TO_ONTOLOGY_SCRIPT = "$hume_repo_root/src/python/concept_discovery/find_nearest_ontology_neighbors.py";
my $GENERATE_JSON_SCRIPT = "$hume_repo_root/src/python/concept_discovery/run.py";

my $INPUT_NPZ_LIST = get_param($params, "input_npz_list", "NON_EXISTED");
my $EMBEDDING_TYPE = get_param($params, "embedding_type", "distilbert");

# Max jobs setting
max_jobs("$JOB_NAME" => 200,);

######################
# Generate Candidates
######################
my $GENERATED_TRIGGER_JSON = "None";
my $GENERATED_SENTENCE_JSON = "None";
if (exists $stages{"generate-candidates"}) {
    print "Generate Candidates stage\n";
    my $stage_name = "generate_candidates";
    my $input_serifxml_list = get_param($params, "input_serifxml_list");
    my $saliency_list = get_param($params, "saliency_list");


    (my $candidates_output_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $generate_candidates_job = runjobs(
        $mkdir_stage_jobid, "$JOB_NAME/generate_candidates",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "16G",
        },
        [ "env PYTHONPATH=$textopen_root/src/python $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $GENERATE_CANDIDATES_SCRIPT --serif-list $input_serifxml_list --filter-wordlist $saliency_list --outdir $candidates_output_dir" ]
    );
    $GENERATED_TRIGGER_JSON = "$candidates_output_dir/trigger.ljson";
    $GENERATED_SENTENCE_JSON = "$candidates_output_dir/sentence.ljson";
}

dojobs();



#####################
# Create Corpus Cache
#####################
my $GENERATED_CORPUS_CACHE = "None";
if (exists $stages{"build-corpus-cache"}) {
    print "Corpus Cache stage\n";
    my $stage_name = "corpus_cache";
    my $trigger_jsonl = $GENERATED_TRIGGER_JSON;

    (my $corpus_output_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $corpus_cache_jobid = runjobs(
      $mkdir_stage_jobid, "$JOB_NAME/corpus_cache",
          {
              BATCH_QUEUE => $LINUX_QUEUE,
          },
        [ "env PYTHONPATH=$hume_repo_root $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $CORPUS_CACHE_SCRIPT --trigger-jsonl $trigger_jsonl --npz-list $INPUT_NPZ_LIST --outdir $corpus_output_dir"]
    );
    $GENERATED_CORPUS_CACHE = $corpus_output_dir;
}

dojobs();

######################
# Calculate Similarity
######################
my $GENERATED_SIM_DIR = "None";
if (exists $stages{"similarity"}) {
    print "Calculate Similarity stage\n";
    my $stage_name = "similarity";
    my $corpus_cache =
        get_param($params, "corpus_cache", "GENERATED") eq "GENERATED"
            ? $GENERATED_CORPUS_CACHE
            : get_param($params, "corpus_cache");

    (my $similarity_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $similarity_jobid = runjobs(
      $mkdir_stage_jobid, "$JOB_NAME/similarity",
          {
              BATCH_QUEUE => $LINUX_QUEUE,
          },
        [ "env PYTHONPATH=$textopen_root/src/python:$hume_repo_root $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $SIMILARITY_SCRIPT --corpus-cache $corpus_cache --npz-list $INPUT_NPZ_LIST --outdir $similarity_dir" ]
    );
    $GENERATED_SIM_DIR = $similarity_dir;
}

dojobs();

##########
# Run CBC
##########
my $GENERATED_CLUSTER_FILE = "None";
if (exists $stages{"cbc"}) {
    print "CBC stage\n";
    my $stage_name = "cbc";
    my $similarity_dir =
        get_param($params, "similarity_dir", "GENERATED") eq "GENERATED"
            ? $GENERATED_SIM_DIR
            : get_param($params, "similarity_dir");
    my $vocab_file = "$similarity_dir/vocab";
    my $sim_file = "$similarity_dir/sim";

    (my $cbc_stage_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    my $cbc_params = "$cbc_stage_dir/cbc.params";

    my $salient_terms_arg =
	    get_param($params, "saliency_list", "None") eq "None"
            ? ""
            : "--salient-terms " . get_param($params, "saliency_list");

    my $cbc_params_jobid = runjobs(
      $mkdir_stage_jobid, "$JOB_NAME/generate_params",
          {
              BATCH_QUEUE => $LINUX_QUEUE,
          },
        [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $GENERATE_CBC_PARAMS_SCRIPT --vocab $vocab_file --similarities $sim_file $salient_terms_arg --outdir $cbc_stage_dir" ]
    );

    my $cbc_jobid = runjobs(
      $cbc_params_jobid, "$JOB_NAME/cbc",
          {
              BATCH_QUEUE      => $LINUX_QUEUE,
              SGE_VIRTUAL_FREE => '16G',
          },
        [ "$RUN_CBC_COMMAND $cbc_params" ]
    );
    $GENERATED_CLUSTER_FILE = "$cbc_stage_dir/cbc.finalClustering";
}

dojobs();

######################
# Build Ontology Cache
######################
my $GENERATED_ONTOLOGY_CACHE = "None";
if (exists $stages{"build-ontology-cache"}) {
    print "Build Ontology Cache stage\n";
    my $stage_name = "build_ontology_cache";
    my $averaged_embeddings = get_param($params, "averaged_embeddings");
    my $ontology_metadata_path = get_param($params, "ontology_metadata_path");
    my $trimmed_annotation_npz = get_param($params, "trimmed_annotation_npz");
    my $annotation_event_jsonl = get_param($params, "annotation_event_jsonl");
    my $existing_ontology_cache = get_param($params, "existing_ontology_cache", "None");

    my $existing_ontology_cache_arg = "";
    if ($existing_ontology_cache ne "None") {
        $existing_ontology_cache_arg = "--existing-cache $existing_ontology_cache";
    }

    (my $ontology_output_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    my $ontology_cache_job = runjobs(
        $mkdir_stage_jobid, "$JOB_NAME/build_ontology_cache",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "env PYTHONPATH=$textopen_root/src/python:$hume_repo_root $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $EMBEDDING_FINDER_SCRIPT --embtype distilbert --ontology-metadata-path $ontology_metadata_path --averaged-embeddings $averaged_embeddings --trimmed-annotation-npz $trimmed_annotation_npz --annotation-event-jsonl $annotation_event_jsonl --outdir $ontology_output_dir $existing_ontology_cache_arg" ]
    );
    $GENERATED_ONTOLOGY_CACHE = "$ontology_output_dir";

}

dojobs();

################################
# Map Clusters to Ontology Nodes
################################
my $GENERATED_NEIGHBORS_FILE = "None";
if (exists $stages{"map-to-ontology"}) {
    print "Map to ontology stage\n";
    my $stage_name = "map_to_ontology";
    my $ontology_cache = $GENERATED_ONTOLOGY_CACHE;
    my $corpus_cache =
        get_param($params, "corpus_cache", "GENERATED") eq "GENERATED"
            ? $GENERATED_CORPUS_CACHE
            : get_param($params, "corpus_cache");
    my $cluster_file =
        get_param($params, "cluster_file", "GENERATED") eq "GENERATED"
            ? $GENERATED_CLUSTER_FILE
            : get_param($params, "cluster_file");

    (my $map_to_ontology_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    my $outfile = "$map_to_ontology_dir/neighbors.csv";

    my $map_to_ontology_jobid = runjobs(
      $mkdir_stage_jobid, "$JOB_NAME/ontology",
          {
              BATCH_QUEUE => $LINUX_QUEUE,
          },
        [ "env PYTHONPATH=$hume_repo_root $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $MAP_TO_ONTOLOGY_SCRIPT --cbc_cluster $cluster_file --corpus_cache $corpus_cache --ontology_cache $ontology_cache --embtype $EMBEDDING_TYPE --embedding_path $INPUT_NPZ_LIST --output_file $outfile" ]
    );
    $GENERATED_NEIGHBORS_FILE = $outfile;
}

dojobs();

################
# Generate JSON
################
my $GENERATED_JSON_FILE = "None";
if (exists $stages{"json"}) {
    print "Generate JSON stage\n";
    my $stage_name = "json";
    my $cluster_file =
        get_param($params, "cluster_file", "GENERATED") eq "GENERATED"
            ? $GENERATED_CLUSTER_FILE
            : get_param($params, "cluster_file");

    my $sentence_jsonl =
        get_param($params, "sentence_jsonl", "GENERATED") eq "GENERATED"
            ? $GENERATED_SENTENCE_JSON
            : get_param($params, "sentence_jsonl");

    my $neighbors_file =
        get_param($params, "neighbors_file", "GENERATED") eq "GENERATED"
            ? $GENERATED_NEIGHBORS_FILE
            : get_param($params, "neighbors_file", "None");

    my $ontology_neighbors_arg = "";
    if ($neighbors_file ne "None") {
        $ontology_neighbors_arg = "--cluster-to-ontology-sim-file $neighbors_file";
    }

    my $remaining_clusters_file = get_param($params, "remaining_clusters_file", "None");
    my $remaining_clusters_arg = "";
    if ($remaining_clusters_file ne "None") {
        $remaining_clusters_arg = "--remaining_clusters_file $remaining_clusters_file";
    }

    my $filter_clusters_by_example_file = get_param($params, "filter_clusters_by_example_file", "None");
    my $filter_clusters_by_example_arg = "";
    if ($filter_clusters_by_example_file ne "None") {
        $filter_clusters_by_example_arg = "--filter_clusters_by_example_file $filter_clusters_by_example_file";
    }

    (my $json_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    my $outfile = "$json_dir/cluster_topn_annotation.json";

    my $json_jobid = runjobs(
      $mkdir_stage_jobid, "$JOB_NAME/json",
          {
              BATCH_QUEUE      => $LINUX_QUEUE,
              SGE_VIRTUAL_FREE => ["15G"]
          },
        [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $GENERATE_JSON_SCRIPT --mode cluster_to_topn_annotation_file --cluster-file $cluster_file --sentence-file $sentence_jsonl $ontology_neighbors_arg $remaining_clusters_arg $filter_clusters_by_example_arg --filter_clusters_by_heuristic --outfile $outfile" ]
    );
    $GENERATED_JSON_FILE = $outfile;
}

endjobs();

sub load_params {
    my %params = ();
    my $config_file = $_[0];

    open(my $fh, '<', $config_file) or die "Could not open config file: $config_file";
    while (my $line = <$fh>) {
        $line =~ s/^\s+|\s+$//g;
        next if length($line) == 0;
        next if substr($line, 0, 1) eq '#';
        my @pieces = split(/:/, $line, 2);
        if (scalar(@pieces) != 2) {
            die "Could not find key: value pair in config file line: $line\n";
        }
        my $param_name = $pieces[0];
        my $param_value = $pieces[1];
        $param_name =~ s/^\s+|\s+$//g;
        $param_value =~ s/^\s+|\s+$//g;
        $params{$param_name} = $param_value;
    }

    close($fh);

    return \%params;
}

sub get_param {
    my $params_ref = $_[0];
    my $param_key = $_[1];
    my $default_value;

    if (scalar(@_) > 2) {
        $default_value = $_[2];
    }

    if (!defined($params_ref->{$param_key})) {
        if (defined($default_value)) {
            return $default_value;
        }
        else {
            die "Required parameter: $param_key not set";
        }
    }

    return $params_ref->{$param_key};
}


