#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';
use lib "/d4m/ears/releases/runjobs4/R2019_03_29/lib";
use runjobs4;

use Cwd 'abs_path';

use File::Basename;
use File::Path;
use File::Copy;

package main;

##### Start copied from main script

my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G');

# Parameter loading
if (scalar(@ARGV) != 1) {
    die "run.pl takes in one argument -- a config file";
}
my $config_file = $ARGV[0];
my $params = load_params($config_file); # $params is a hash reference
my $JOB_NAME = get_param($params, "job_name");
my $LINUX_QUEUE = get_param($params, "cpu_queue", "nongale-sl6");
my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-centos7");
my $BATCH_SIZE = get_param($params, "batch_size", 250);
my $processing_dir = make_output_dir("$exp_root/expts/$JOB_NAME");


my $hume_repo_root = abs_path("$exp_root");
my $dependencies_root = "$hume_repo_root/resource/dependencies";
my $external_dependencies_root = "/nfs/raid87/u10/shared/Hume";
my $unmanaged_external_dependencies_root = "/nfs/raid87/u11/users/hqiu/external_dependencies_unmanaged";


# Python commands
my $PYTHON2 = "/opt/Python-2.7.8-x86_64/bin/python -u";
my $PYTHON3 = "/opt/Python-3.5.2-x86_64/bin/python3.5 -u";
my $ANACONDA_ROOT = "";
if (get_param($params, "nn_events_use_pre_installed_anaconda_path", "None") eq "None") {
    $ANACONDA_ROOT = "$unmanaged_external_dependencies_root/anaconda";
}
else {
    $ANACONDA_ROOT = get_param($params, "nn_events_use_pre_installed_anaconda_path");
}

my $CREATE_FILE_LIST_SCRIPT = "$PYTHON3 $hume_repo_root/src/python/pipeline/scripts/create_filelist.py";
my $PY_SERIFXML_PATH = "$ENV{'SVN_PROJECT_ROOT'}/SERIF/python";


##### End copied from main script

##### User provided programs
my $GENERATE_SEGMENT_SCRIPT = "$hume_repo_root/src/python/fuzzy_search/prepare_corpus.py";
my $PREPARE_LEXICAL_TRANSLATION_TABLE_SCRIPT = "$hume_repo_root/src/python/fuzzy_search/prepare_lexical_translation_table.py";
my $PARSE_STRUCTURE_QUERY_SCRIPT = "$hume_repo_root/src/python/fuzzy_search/parse_queries_based_on_structured_queries.py";
my $CONDA_ENV_FOR_FUZZY_SEARCH = "py3-ml-general";
#####




##### Start main

create_clir_corpus(get_param($params,"input_clir_corpus_serif_list"),make_output_dir("$processing_dir/clir_corpus"));
endjobs();

##### End main

##### Start copied from main script

sub load_params {
    my %params = ();
    $config_file = $_[0];

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

sub make_output_dir {
    my $dir = $_[0];
    mkpath($dir);
    return abs_path($dir);
}


sub split_file_for_processing {
    my $split_jobname = $_[0];
    my $bf = $_[1];
    my $bp = $_[2];
    my $bs = $_[3];
    open my $fh, "<", $bf or die "could not open $bf: $!";
    my $num_files = 0;
    $num_files++ while <$fh>;
    my $njobs = int($num_files / $bs) + 1;
    if ($num_files % $bs == 0) {
        $njobs--;
    }
    print "File $bf will be broken into $njobs batches of approximate size $bs\n";
    my $jobid = runjobs([], "$split_jobname",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SCRIPT      => 1,
        },
        "/usr/bin/split -d -a 5 -l $bs $bf $bp");

    return($njobs, $jobid);
}

sub generate_file_list {
    my @job_dependencies = @{$_[0]};
    my $create_list_job_name = $_[1];
    my $unix_path_str = $_[2];
    my $output_file_path = $_[3];
    return runjobs(
        \@job_dependencies, $create_list_job_name,
        {
            SCRIPT => 1
        },
        [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$unix_path_str\" --output_list_path $output_file_path" ]
    );
}

##### End copied from main script

sub create_clir_corpus{
    my $input_serif_list_path = $_[0];
    my $stage_processing_dir = $_[1];


    my $OUTPUT_WORDLIST_PATH = "$stage_processing_dir/wordlist.list";
    my $OUTPUT_CLIR_CORPUS_LIST_PATH = "$stage_processing_dir/segments.list";
    my $OUTPUT_LEXICAL_TRANSLATION_TABLE_PATH = "$stage_processing_dir/lexical_translation_table";

    my $ontology_root = "$hume_repo_root/resource/ontologies/internal/causeex";
    my $ontology_flag = "CAUSEEX";
    my $stage_name = "create_clir_corpus";
    my $structure_query_json_path = get_param($params,"structure_query_path");
    my $parse_query_jobid = runjobs(
        [],"$JOB_NAME/$stage_name/parse_query",
        {
            BATCH_QUEUE => $LINUX_QUEUE
        },
        ["$ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $PARSE_STRUCTURE_QUERY_SCRIPT --input_structure_query_json $structure_query_json_path --output_path $stage_processing_dir/query.tsv"]
    );


    my $batch_file_dir = make_output_dir("$stage_processing_dir/batch_files");
    my ($NUM_JOBS, $split_serif_list_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_serif_batch_files", $input_serif_list_path, "$batch_file_dir/", $BATCH_SIZE);
    my @create_clir_segment_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_dir/$job_batch_num";

        my $batch_processing_dir = make_output_dir("$stage_processing_dir/clir_corpus/$job_batch_num");
        my $batch_output_dir = make_output_dir("$batch_processing_dir/output");
        my $create_clir_sgement_id = runjobs(
            [$split_serif_list_jobid],"$JOB_NAME/$stage_name/create_clir_segment_$job_batch_num",
            {
                BATCH_QUEUE                      => $LINUX_QUEUE,
            },
            ["env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $GENERATE_SEGMENT_SCRIPT --input_serif_list $batch_file --input_structure_query_json $structure_query_json_path --output_dir $batch_output_dir"]
        );
        push(@create_clir_segment_jobs, $create_clir_sgement_id);
    }
    my $list_word_list_jobid = generate_file_list(\@create_clir_segment_jobs, "$JOB_NAME/$stage_name/list_word_list", "$stage_processing_dir/clir_corpus/*/output/word.list", $OUTPUT_WORDLIST_PATH);
    my $list_segments_jobid = generate_file_list(\@create_clir_segment_jobs, "$JOB_NAME/$stage_name/list_segments", "$stage_processing_dir/clir_corpus/*/output/segments", $OUTPUT_CLIR_CORPUS_LIST_PATH);
    my $generate_translation_table_jobid = runjobs(
        [$list_word_list_jobid],"$JOB_NAME/$stage_name/generate_translation_table",
        {
            BATCH_QUEUE => $LINUX_QUEUE
        },
        ["$ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $PREPARE_LEXICAL_TRANSLATION_TABLE_SCRIPT --ontology_root $ontology_root --ontology_flag $ontology_flag --additional_word_list $OUTPUT_WORDLIST_PATH --embedding_npz_path /nfs/raid87/u14/CauseEx/nn_event_models/shared/EN-wform.w.5.cbow.neg10.400.subsmpl.txt.spaceSep.utf8 --output_path $OUTPUT_LEXICAL_TRANSLATION_TABLE_PATH"]
    );
    return $generate_translation_table_jobid;
}