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
my $MAIN_SCRIPT = "$hume_repo_root/src/python/fuzzy_search/similarity/bert_pairwise_entity_filter/run.py";
my $CONDA_ENV_FOR_FUZZY_SEARCH = "py3-ml-general";
#####


##### Start main


# S1 Extra corpus and queries
my $stage_name = "corpus_features";
my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
my $batch_file_dir = make_output_dir("$stage_processing_dir/batch_files");
my $input_corpus_serif_list = get_param($params, "input_corpus_serif_list");
my $input_corpus_npz_list = get_param($params, "input_serif_npz_list");
my ($NUM_JOBS, $split_serif_list_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_batch_files", $input_corpus_serif_list, "$batch_file_dir/", 1);

my @extract_corpus_feature_jobs = ();
for (my $n = 0; $n < $NUM_JOBS; $n++) {
    my $job_batch_num = sprintf("%05d", $n);
    my $batch_file = "$batch_file_dir/$job_batch_num";

    my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num");
    my $batch_output_dir = make_output_dir("$batch_processing_dir/output");
    my $extract_corpus_feature_id = runjobs(
        [ $split_serif_list_jobid ], "$JOB_NAME/$stage_name/extract_corpus_feature_$job_batch_num",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $MAIN_SCRIPT --mode BUILD_FEATURE_FOR_CORPUS --input_serif_list $batch_file --input_serif_npz_list $input_corpus_npz_list --output_path $batch_output_dir" ]
    );
    push(@extract_corpus_feature_jobs, $extract_corpus_feature_id);
}
my $corpus_feature_simple_list = $stage_processing_dir . "/simple.list";
my $corpus_feature_complex_list = $stage_processing_dir . "/complex.list";
my $list_corpus_feature_jobid1 = generate_file_list(\@extract_corpus_feature_jobs, "$JOB_NAME/$stage_name/list_corpus_feature1", "$stage_processing_dir/*/output/*_complex.json", $corpus_feature_complex_list);
my $list_corpus_feature_jobid2 = generate_file_list(\@extract_corpus_feature_jobs, "$JOB_NAME/$stage_name/list_corpus_feature2", "$stage_processing_dir/*/output/*_simple.json", $corpus_feature_simple_list);

$stage_name = "query_features";
$stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
my $stage_processing_output_dir = make_output_dir("$stage_processing_dir/output");
my $input_query_serif_list = get_param($params, "input_query_serif_list");
my $input_query_npz_list = get_param($params, "input_query_npz_list");

my $extract_query_feature_id = runjobs(
    [], "$JOB_NAME/$stage_name/extract_query_feature",
    {
        BATCH_QUEUE => $LINUX_QUEUE,
    },
    [ "env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $MAIN_SCRIPT --mode BUILD_FEATURE_FOR_QUERY --input_query_serif_list $input_query_serif_list --input_query_npz_list $input_query_npz_list --output_path $stage_processing_output_dir" ]
);

my $query_feature_complex_list = $stage_processing_dir . "/complex.list";
my $list_query_feature_jobid = generate_file_list([ $extract_query_feature_id ], "$JOB_NAME/$stage_name/list_query_feature", "$stage_processing_output_dir/*.json", $query_feature_complex_list);

dojobs();

$stage_name = "calculate_cosine_similarity_and_filter";
$stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
$stage_processing_output_dir = make_output_dir("$stage_processing_dir/output");
($NUM_JOBS, $split_serif_list_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_batch_files", $query_feature_complex_list, "$batch_file_dir/", 1);

my $metric = get_param($params,"metric");
my $n_trees = get_param($params,"n_trees");

my @cosine_similarity_filtered_report_jobs = ();
for (my $n = 0; $n < $NUM_JOBS; $n++) {
    my $job_batch_num = sprintf("%05d", $n);
    my $batch_file = "$batch_file_dir/$job_batch_num";

    my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num");
    my $batch_output_dir = make_output_dir("$batch_processing_dir/output");

    my $cosine_similarity_result_path = "$batch_output_dir/$job_batch_num" . "_similarity.p";

    my $cosine_similarity_id = runjobs(
        [ $split_serif_list_jobid, $list_corpus_feature_jobid2 ], "$JOB_NAME/$stage_name/cosine_similarity_$job_batch_num",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "64G",
        },
        [ "env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $MAIN_SCRIPT --mode CALCULATE_SIMILARITY --input_query_feature_list $batch_file --input_doc_feature_list $corpus_feature_simple_list --output_path $cosine_similarity_result_path --metric $metric --n_trees $n_trees" ]
    );
    my $entity_filtered_result_path = "$batch_output_dir/$job_batch_num" . "_filtered.p";
    my $post_filtering_id = runjobs(
        [ $cosine_similarity_id ], "$JOB_NAME/$stage_name/post_filtering_$job_batch_num",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "64G",
        },
        [ "env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $MAIN_SCRIPT --mode ENTITY_FILTER --query_result $cosine_similarity_result_path  --input_query_feature_list $batch_file --input_doc_feature_list $corpus_feature_complex_list --output_path $entity_filtered_result_path" ]
    );
    my $report_file_path = "$batch_output_dir/$job_batch_num" . "_report.json";
    my $report_generating_id = runjobs(
        [ $post_filtering_id ], "$JOB_NAME/$stage_name/generate_report_$job_batch_num",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "64G",
        },
        [ "env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python $MAIN_SCRIPT --mode DUMP_REPORT --query_result $entity_filtered_result_path  --input_query_feature_list $batch_file --input_doc_feature_list $corpus_feature_complex_list --output_path $report_file_path --metric $metric --n_trees $n_trees" ]
    );
    push(@cosine_similarity_filtered_report_jobs, $report_generating_id);
}

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
