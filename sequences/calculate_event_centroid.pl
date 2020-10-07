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
my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-sl610");
my $BATCH_SIZE = get_param($params, "batch_size", 5);
my $processing_dir = make_output_dir("$exp_root/expts/$JOB_NAME");
max_jobs("$JOB_NAME/bert" => 400,);

my $hume_repo_root = abs_path("$exp_root");
my $git_repo = abs_path("$exp_root/..");
my $NLPLINGO_ROOT = "$git_repo/nlplingo";
my $textopen_root = "$git_repo/text-open";

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
my $BERT_REPO_PATH = "/nfs/raid84/u12/ychan/repos/bert";
my $BERT_PYTHON_PATH = "$textopen_root/src/python:$NLPLINGO_ROOT:$BERT_REPO_PATH";
my $BERT_TOKENIZER_PATH = "$hume_repo_root/src/python/bert/do_bert_tokenization.py";
my $BERT_NPZ_EMBEDDING = "$hume_repo_root/src/python/bert/do_npz_embeddings.py";
my $CONDA_ENV_NAME_FOR_BERT = "py3-tf1.11";
my $BERT_MODEL_PATH = "/nfs/raid88/u10/users/ychan/repos/bert/model_data/uncased_L-12_H-768_A-12";
my $BERT_VOCAB_FILE = "$BERT_MODEL_PATH/vocab.txt";
my $CALCULATE_CENTROID_SCRIPT = "$hume_repo_root/src/python/bert/extract_centroid.py";

##### End copied from main script


print "Calculate centroid!\n";
my $stage_processing_dir = make_output_dir("$processing_dir/bert");
my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_files");
my $input_serifxml_list = get_param($params, "bert_input_serifxml_list");
my $input_labeled_mappings_path = get_param($params, "labeled_mappings_path");
my $stage_name = "bert";
my $GENERATED_BERT_NPZ_LIST = "$stage_processing_dir/bert_npz.list";
my ($NUM_JOBS, $split_bert_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_bert_batch_files", $input_serifxml_list, "$batch_file_directory/bert_batch_file_", $BATCH_SIZE);
my $BERT_layers =
    get_param($params, "bert_layers") eq "DEFAULT"
        ? "-1"
        : get_param($params, "bert_layers");
my @bert_split_jobs = ();

for (my $n = 0; $n < $NUM_JOBS; $n++) {
    my $job_batch_num = sprintf("%05d", $n);
    my $batch_file = "$batch_file_directory/bert_batch_file_$job_batch_num";
    my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num");
    my $batch_tmp_dir = make_output_dir("$batch_processing_dir/tmp");
    my $tokens_dir = make_output_dir("$batch_tmp_dir/tokens");
    my $bert_embeddings_dir = make_output_dir("$batch_tmp_dir/embeddings");
    my $output_npz_dir = make_output_dir("$batch_processing_dir/output");
    my $maximum_allowed_bert_tokens_per_sentence = 500; # Maximum is 512 from @ychan
    my $add_prefix_to_serifxml_in_list_jobid =
        runjobs(
            [ $split_bert_jobid ], "$JOB_NAME/$stage_name/atomic_$job_batch_num/make_bert_batch_files_add_prefix",
            {
                BATCH_QUEUE      => $SINGULARITY_GPU_QUEUE,
                SGE_VIRTUAL_FREE => "2G",
                SCRIPT           => 1
            },
            [ "cat $batch_file | awk '{print \"SERIF:\"\$0}' > $batch_file\.with_type" ]
        );
    my $producing_bert_tokens = runjobs(
        [ $add_prefix_to_serifxml_in_list_jobid ], "$JOB_NAME/$stage_name/atomic_$job_batch_num/bert_tokens",
        {
            SGE_VIRTUAL_FREE => "16G",
            BATCH_QUEUE      => $SINGULARITY_GPU_QUEUE,
            job_retries      => 1
        },
        [ "env PYTHONPATH=$BERT_PYTHON_PATH $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT/bin/python $BERT_TOKENIZER_PATH --filelist $batch_file\.with_type --bert_vocabfile $BERT_VOCAB_FILE --outdir $tokens_dir --maximum_allowed_bert_tokens_per_sentence $maximum_allowed_bert_tokens_per_sentence" ]
    );

    my $run_bert_jobid = runjobs(
        [ $producing_bert_tokens ], "$JOB_NAME/$stage_name/atomic_$job_batch_num/run_bert",
        {
            SGE_VIRTUAL_FREE => "24G",
            BATCH_QUEUE      => $SINGULARITY_GPU_QUEUE,
            bert_repo        => $BERT_REPO_PATH,
            python           => "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT/bin/python",
            indir            => $tokens_dir,
            outdir           => $bert_embeddings_dir,
            bert_model       => $BERT_MODEL_PATH,
            bert_layers      => $BERT_layers,
            job_retries      => 1
        },
        [ "/bin/bash", "run_bert_embeddings.sh" ]
    );
    my $combine_npz_jobid = runjobs(
        [ $run_bert_jobid ], "$JOB_NAME/$stage_name/atomic_$job_batch_num/generate_npz_output",
        {
            SGE_VIRTUAL_FREE => "24G",
            BATCH_QUEUE      => $LINUX_QUEUE,
            job_retries      => 1
        },
        [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT/bin/python $BERT_NPZ_EMBEDDING --embeddings_dir $bert_embeddings_dir --token_dir $tokens_dir --token_map_dir $tokens_dir --outdir $output_npz_dir" ]
    );
    my $clean_intermediate_file_jobid = runjobs(
        [ $combine_npz_jobid ], "$JOB_NAME/$stage_name/atomic_$job_batch_num/cleaning_tmp",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SCRIPT      => 1
        },
        [ "/bin/rm -rf $batch_tmp_dir" ]
    );
    push(@bert_split_jobs, $clean_intermediate_file_jobid);
}

# Compine results into one list
my $list_results_jobid = generate_file_list(\@bert_split_jobs, "$JOB_NAME/$stage_name/list-bert-results", "$stage_processing_dir/*/output/*.npz", $GENERATED_BERT_NPZ_LIST);

my $output_json_path = "$stage_processing_dir/centroid.json";

my $calculate_centriod_jobid = runjobs(
    [ $list_results_jobid ], "$JOB_NAME/$stage_name/calculate_centroid",
    {
        BATCH_QUEUE => $LINUX_QUEUE,
        SGE_VIRTUAL_FREE => "24G"
    },
    [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT/bin/python $CALCULATE_CENTROID_SCRIPT --labeled_mappings_path $input_labeled_mappings_path --npz_list_path $GENERATED_BERT_NPZ_LIST --output_json_path $output_json_path" ]
);

endjobs();


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