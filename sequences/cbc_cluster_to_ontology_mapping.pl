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
    die "cbc_cluster_to_ontology_mapping.pl takes in one argument -- a config file";
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
my $SAMPLE_AVG_EMBEDDINGS_SCRIPT = "$hume_repo_root/src/python/ontology_centroid_helpers/sample_embeddings_for_words.py";
my $EMBEDDING_FINDER_SCRIPT = "$hume_repo_root/src/python/ontology_centroid_helpers/embedding_finder.py";
my $FIND_NEAREST_NEIGHBORS_SCRIPT = "$hume_repo_root/src/python/concept_discovery/find_nearest_ontology_neighbors.py";

# Max jobs setting
max_jobs("$JOB_NAME" => 200,);

######################
# Generate Candidates
######################
my $GENERATED_TRIGGER_JSON = "NONE";
my $GENERATED_SENTENCE_JSON = "NONE";
if (exists $stages{"generate-candidates"}) {
    print "Generate Candidates stage\n";
    my $stage_name = "generate_candidates";
    my $input_serifxml_list = get_param($params, "input_serifxml_list");

    (my $candidates_output_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $generate_candidates_job = runjobs(
        $mkdir_stage_jobid, "$JOB_NAME/generate_candidates",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "16G",
        },
        [ "env PYTHONPATH=$textopen_root/src/python $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $GENERATE_CANDIDATES_SCRIPT --serif-list $input_serifxml_list --outdir $candidates_output_dir" ]
    );
    $GENERATED_TRIGGER_JSON = "$candidates_output_dir/trigger.ljson";
    $GENERATED_SENTENCE_JSON = "$candidates_output_dir/sentence.ljson";
}

dojobs();

#######################
# Sample Avg Embeddings
#######################
my $GENERATED_AVG_EMBEDDINGS = "NONE";
if (exists $stages{"sample-avg-embeddings"}) {
    print "Sample avg embeddings stage\n";
    my $stage_name = "sample_avg_embeddings";
    my $npz_list = get_param($params, "input_npz_list");
    my $trigger_jsonl =
        get_param($params, "trigger_jsonl", "GENERATED") eq "GENERATED"
            ? $GENERATED_TRIGGER_JSON
            : get_param($params, "trigger_jsonl");

    (my $avg_embeddings_output_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $sample_avg_embeddings_jobid = runjobs(
      $mkdir_stage_jobid, "$JOB_NAME/sample_avg_embeddings",
          {
              BATCH_QUEUE => $LINUX_QUEUE,
              SGE_VIRTUAL_FREE => "16G",
          },
        [ "env PYTHONPATH=$textopen_root/src/python:$hume_repo_root $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $SAMPLE_AVG_EMBEDDINGS_SCRIPT --trigger-jsonl $trigger_jsonl --npz-list $npz_list --outdir $avg_embeddings_output_dir"]
    );
    $GENERATED_AVG_EMBEDDINGS = "$avg_embeddings_output_dir/word_to_ave_emb.npz";
}

dojobs();

######################
# Build Ontology Cache
######################
my $GENERATED_ONTOLOGY_CACHE = "NONE";
if (exists $stages{"build-ontology-cache"}) {
    print "Build Ontology Cache stage\n";
    my $stage_name = "build_ontology_cache";
    my $averaged_embeddings =
        get_param($params, "averaged_embeddings", "GENERATED") eq "GENERATED"
            ? $GENERATED_AVG_EMBEDDINGS
            : get_param($params, "averaged_embeddings");
    my $ontology_path = get_param($params, "ontology_path");
    my $ontology_metadata_path = get_param($params, "ontology_metadata_path");
    my $annotation_npz_list = get_param($params, "annotation_npz_list");
    my $annotation_event_jsonl = get_param($params, "annotation_event_jsonl");

    (my $ontology_output_dir, my $mkdir_stage_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $ontology_cache_job = runjobs(
        $mkdir_stage_jobid, "$JOB_NAME/build_ontology_cache",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "env PYTHONPATH=$textopen_root/src/python:$hume_repo_root $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_CPU/bin/python3 $EMBEDDING_FINDER_SCRIPT --embtype distilbert --ontology-path $ontology_path --ontology-metadata-path $ontology_metadata_path --averaged-embeddings $averaged_embeddings --annotation-npz-list $annotation_npz_list --annotation-event-jsonl $annotation_event_jsonl --outdir $ontology_output_dir" ]
    );
    $GENERATED_ONTOLOGY_CACHE = "$ontology_output_dir";

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


