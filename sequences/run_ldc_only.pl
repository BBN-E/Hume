#!/bin/env perl

# Requirements:
#
# Run with /opt/perl-5.20.0-x86_64/bin/perl or similar
# Use Java 8 -- export JAVA_HOME="/opt/jdk1.8.0_20-x86_64"
# environment variable SVN_PROJECT_ROOT (in .bashrc) should point to Active/Projects where SERIF/python, SERIF/par, W-ICEWS/lib are checked out
# If you have a "# Stop here for an non-interactive shell." section in your .bashrc file, make sure the relevant environment variables (above) are above that section to make sure runjobs can see them
#
# git clone text-open
# cd text-open/src/java/serif ; mvn clean install
# 
# git clone jserif
# cd jserif ; mvn clean install
# 
# cd Hume/src/java/serif-util ; mvn clean install -DskipTests
#
# git clone learnit
# cd learnit ; mvn clean install
#
# git clone kbp
# git clone deepinsight
# git clone nlplingo
#


use strict;
use warnings;

use lib "/d4m/ears/releases/runjobs4/R2019_03_29/lib";
use runjobs4;

use Cwd 'abs_path';

use File::Basename;
use File::Path;
use File::Copy;

package main;



my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G');

# Parameter loading
if (scalar(@ARGV) != 1) {
    die "run.pl takes in one argument -- a config file";
}
my $config_file = $ARGV[0];
my $params = load_params($config_file); # $params is a hash reference
my @stages = split(/,/, get_param($params, "stages_to_run"));
@stages = grep (s/\s*//g, @stages); # remove leading/trailing whitespaces from stage names

my %stages = map {$_ => 1} @stages;
my $JOB_NAME = get_param($params, "job_name");

my $LINUX_QUEUE = get_param($params, "cpu_queue", "nongale-sl6");
#my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-sl69-non-k10s");
my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-sl610");

my $git_repo = abs_path("$exp_root/..");
my $hume_repo_root = abs_path("$exp_root");
my $learnit_root = "$git_repo/learnit";
my $deepinsight_root = "$git_repo/deepinsight";
my $textopen_root = "$git_repo/text-open";
my $dependencies_root = "$hume_repo_root/resource/dependencies";
my $external_dependencies_root = "/nfs/raid87/u10/shared/Hume";
my $unmanaged_external_dependencies_root = "/nfs/raid87/u11/users/hqiu/external_dependencies_unmanaged";

# Location of all the output of this sequence
my $processing_dir = make_output_dir("$exp_root/expts/$JOB_NAME");

# Make copy of config file for debugging purposes
copy($config_file, $processing_dir . "/" . get_current_time() . "-" . basename($config_file));

# Python commands
my $PYTHON3 = "/opt/Python-3.5.2-x86_64/bin/python3.5 -u";
my $ANACONDA_ROOT = "";
if (get_param($params, "nn_events_use_pre_installed_anaconda_path", "None") eq "None") {
    $ANACONDA_ROOT = "$unmanaged_external_dependencies_root/anaconda";
}
else {
    $ANACONDA_ROOT = get_param($params, "nn_events_use_pre_installed_anaconda_path");
}
my $CONDA_ENV_NAME_FOR_NLPLINGO = "tensorflow-1.5";
my $CONDA_ENV_NAME_FOR_PROBABILISTIC_GROUNDER = "tensorflow-1.5";
my $CONDA_ENV_NAME_FOR_BERT_CENTROID_GROUNDING = "py3-ml-general";

my $ANACONDA_PY2_ROOT_FOR_NN_EVENT_TYPING = "$unmanaged_external_dependencies_root/nn_event_typing/anaconda2";
my $CONDA_ENV_NAME_FOR_NN_EVENT_TYPING = "python-tf0.11-cpu";

my $NLPLINGO_ROOT = "$git_repo/nlplingo";

# Please change this
my $JCAI_PT_CPU = "/nfs/mercury-05/u35/D3M/jcai/anaconda3/envs/pt-cpu/bin/python3";
# End please change this

# Scripts
my $COPY_FILES_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/copy_serifxml_by_document_type.py";
my $KB_CONSTRUCTOR_SCRIPT = "$hume_repo_root/src/python/knowledge_base/kb_constructor.py";
my $COMBINE_NN_EVENTS_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/merge_event_mentions_in_json.py";
my $LEARNIT_JSON_AGGREGATOR_SCRIPT = "$learnit_root/scripts/decoder_list_of_json_output_aggregator.py";
my $LEARNIT_DECODER_SCRIPT = "$hume_repo_root/scripts/run_EventEventRelationPatternDecoder.sh";
my $NNEVENT_DECODE_SCRIPT = "$NLPLINGO_ROOT/nlplingo/event/train_test.py";
my $FACTFINDER_TO_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/factfinder_output_to_json.py";
my $EVENT_COUNT_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/count_triggers_in_causal_relations.py";
my $PROB_GROUNDING_SCRIPT = "$hume_repo_root/src/python/misc/ground_serifxml.py";
my $ADD_BERT_TO_FILELIST_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/add_bert_to_filelist.py";
##my $NN_MAPPING_SCRIPT = "$hume_repo_root/src/python/misc/map_nn_output.py";
my $CREATE_FILE_LIST_SCRIPT = "$PYTHON3 $hume_repo_root/src/python/pipeline/scripts/create_filelist.py";
my $PREPARE_SERIF_EMBEDDING_FILELIST_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/prepare_serif_embedding_filelist.py";

my $NEURAL_RELATION_DECODER_SCRIPT_LDC = "$hume_repo_root/scripts/run_EventEventRelationNeuralDecoder_ldc.sh";
my $NEURAL_RELATION_DECODER_SCRIPT_OLD = "$hume_repo_root/scripts/run_EventEventRelationNeuralDecoder_old.sh";

my $nre_model_root = "$external_dependencies_root/common/event_event_relation/models/042219";
my $ldc_model_root = "/nfs/raid88/u10/users/jcai/expts/46692_ldc_unified_12_6_2019/ckpt_train_ldc-unified_E82_E70_E61_E48_20191206_07_39_27";
# my $ldc_model_root = "/nfs/raid88/u10/users/jcai/expts/46692_ldc_11_21_2019/ckpt_train_ldc-E82_20191125_13_24_55";
my $NRE_POSTPROCESSING = "$deepinsight_root/relations/src/postprocess.py";
my $NRE_RESCALE_FREQ = "$deepinsight_root/relations/src/rescale_freq.py";
my $NRE_STRIP_LOW_CONF = "$deepinsight_root/relations/src/strip_low_conf.py";
my $NRE_UNIFY = "$deepinsight_root/relations/src/filter/unify_predictions.py";

# my $SINGULARITY_WRAPPER = "$hume_repo_root/scripts/run-in-singularity-container.sh";

my $SERIF_SERVER_MODE_CLIENT_SCRIPT = "$hume_repo_root/experiments/service_mode/serif_client.py";
my $NLPLINGO_SERVER_MODE_CLIENT_SCRIPT = "$hume_repo_root/experiments/service_mode/nlplingo_client.py";
my $GROUP_EVENTMENTION_IN_TIMELINE_BUCKET_SCRIPT = "$hume_repo_root/src/python/util/group_event_mention_in_timeline_bucket.py";


# Exes
my $BASH = "/bin/bash";
my $SERIF_EXE = "$hume_repo_root/bin/Serif";
my $JSERIF_ROOT = "$git_repo/jserif/";
my $KBP_EVENT_FINDER_EXE = "$JSERIF_ROOT/serif-events-graveyard/target/appassembler/bin/eventFinderHighMem";
my $LEARNIT_INSTANCE_EXTRACTOR_EXE = "$learnit_root/neolearnit/target/appassembler/bin/InstanceExtractor";
my $STRIP_EVENTS_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/StripEvents2";
my $EVENT_EVENT_RELATION_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/EventEventRelationCreator";
my $PROB_GROUNDING_INJECTION_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/GroundEventTypeFromJson";
my $EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/CalibrateConfidences";
my $EXTRACT_TIMELINE_FROM_SERIFXML_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/DumpEventMentionForEventTimeline";
my $ADD_EVENT_MENTION_BY_POS_TAGS_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/AddEventMentionByPOSTags";
my $ADD_EVENT_MENTION_FROM_JSON_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/AddEventMentionFromJson";
##my $ADD_EVENT_MENTION_FACTORS_FROM_JSON_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/AddEventMentionFactorsFromJson";
my $DOCTHEORY_RESOLVER_EXE = "$hume_repo_root/src/java/serif-util/target/appassembler/bin/DocTheoryResolver";
# Libraries
my $NNEVENT_PYTHON_PATH = "$textopen_root/src/python:" . "$NLPLINGO_ROOT";
my $BERT_REPO_PATH = "/nfs/raid84/u12/ychan/repos/bert";
my $BERT_PYTHON_PATH = "$NLPLINGO_ROOT:$BERT_REPO_PATH:$textopen_root/src/python";
my $BERT_TOKENIZER_PATH = "$hume_repo_root/src/python/bert/do_bert_tokenization.py";
my $BERT_NPZ_EMBEDDING = "$hume_repo_root/src/python/bert/do_npz_embeddings.py";
my $CONDA_ENV_NAME_FOR_BERT = "py3-tf1.11";
my $BERT_MODEL_PATH = "/nfs/raid88/u10/users/ychan/repos/bert/model_data/uncased_L-12_H-768_A-12";
my $BERT_VOCAB_FILE = "$BERT_MODEL_PATH/vocab.txt";

# Please let @hqiu know if you want to change $SERIF_DATA
my $SERIF_DATA = "/d4m/serif/data";

my $BATCH_SIZE = get_param($params, "batch_size", 100);
my $mode = get_param($params, "mode");
my $internal_ontology_dir;
my $open_ontology_dir = "$hume_repo_root/resource/ontologies/open/";
my $external_ontology_dir;
if ($mode eq "CauseEx") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/causeex/";
}
elsif ($mode eq "WorldModelers") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/hume/";
    $external_ontology_dir = "/nfs/raid85/u13/users/criley/repos/WM_Ontologies/";
}
else {
    die "mode has to be CauseEx or WorldModelers";
}

# Batch files
# my $batch_file_directory = make_output_dir("$processing_dir/batch_files");

check_requirements();

# Max jobs setting
max_jobs("$JOB_NAME/serif" => 200,);
max_jobs("$JOB_NAME/bert" => 400,);
max_jobs("$JOB_NAME/kbp" => 200,);
max_jobs("$JOB_NAME/generic_events" => 200,);
max_jobs("$JOB_NAME/learnit" => 200,);
max_jobs("$JOB_NAME/nn_events" => 300,);
##max_jobs("$JOB_NAME/nn_factors" => 300,);
max_jobs("$JOB_NAME/probabilistic_grounding" => 300,);
max_jobs("$JOB_NAME/event_consolidation" => 50,);
max_jobs("$JOB_NAME/learnit" => 200,);
max_jobs("$JOB_NAME/event_event_relation" => 400,);
max_jobs("$JOB_NAME/grounding_serialize" => 200,);

########
# Serif
########
my $GENERATED_SERIF_SERIFXML = "$processing_dir/serif_serifxml.list";
my $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR = "$processing_dir/serif_cause_effect_json";
my $GENERATED_FACTFINDER_JSON_FILE = "$processing_dir/serif/facts.json";
if (exists $stages{"serif"}) {
    print "Serif stage\n";

    # Run Serif in parallel
    my $input_sgm_list = get_param($params, "serif_input_sgm_list");
    my $master_serif_output_dir = make_output_dir("$processing_dir/serif");
    my $batch_file_dir = make_output_dir("$master_serif_output_dir/batch_files");
    my $stage_name = "serif";

    my ($NUM_JOBS, $split_serif_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_serif_batch_files", $input_sgm_list, "$batch_file_dir/", $BATCH_SIZE);
    my $par_dir = $ENV{"SVN_PROJECT_ROOT"} . "/SERIF/par";

    my $should_track_files_read = get_param($params, "track_serif_files_read", "true");
    my $use_basic_cipher_stream = get_param($params, "use_basic_cipher_stream", "false");
    my $serif_cause_effect_patterns_dir = "$hume_repo_root/resource/serif_cause_effect_patterns";

    my @serif_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $serif_job_name = "$JOB_NAME/$stage_name/$job_batch_num";
        my $experiment_dir = "$master_serif_output_dir/$job_batch_num";
        my $batch_file = "$batch_file_dir/$job_batch_num";

        if (get_param($params, "serif_server_mode_endpoint", "None") eq "None") {
            if ($mode eq "CauseEx") {
                my $serif_par = "serif_causeex.par";
                my $icews_lib_dir = $ENV{"SVN_PROJECT_ROOT"} . "/W-ICEWS/lib";
                my $project_specific_serif_data_root = "$hume_repo_root/resource/serif_data_causeex";
                my $serif_jobid =
                    runjobs(
                        [ $split_serif_jobid ], $serif_job_name,
                        {
                            par_dir                          => $par_dir,
                            experiment_dir                   => $experiment_dir,
                            batch_file                       => $batch_file,
                            icews_lib_dir                    => $icews_lib_dir,
                            bbn_actor_db                     => get_param($params, "serif_input_awake_db"),
                            project_specific_serif_data_root => $project_specific_serif_data_root,
                            cause_effect_output_dir          => $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR,
                            SERIF_DATA                       => $SERIF_DATA,
                            SGE_VIRTUAL_FREE                 => "16G",
                            BATCH_QUEUE                      => $LINUX_QUEUE,
                            serif_cause_effect_patterns_dir  => $serif_cause_effect_patterns_dir,
                            should_track_files_read          => $should_track_files_read,
                            use_basic_cipher_stream          => $use_basic_cipher_stream
                        },
                        [ "$SERIF_EXE", $serif_par ]
                    );
                push(@serif_jobs, $serif_jobid);
            }
            else {
                my $serif_par = "serif_wm.par";
                my $project_specific_serif_data_root = "$hume_repo_root/resource/serif_data_wm";
                my $serif_jobid =
                    runjobs(
                        [ $split_serif_jobid ], $serif_job_name,
                        {
                            par_dir                          => $par_dir,
                            experiment_dir                   => $experiment_dir,
                            batch_file                       => $batch_file,
                            bbn_actor_db                     => get_param($params, "serif_input_awake_db"),
                            project_specific_serif_data_root => $project_specific_serif_data_root,
                            cause_effect_output_dir          => $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR,
                            SERIF_DATA                       => $SERIF_DATA,
                            SGE_VIRTUAL_FREE                 => "16G",
                            BATCH_QUEUE                      => $LINUX_QUEUE,
                            serif_cause_effect_patterns_dir  => $serif_cause_effect_patterns_dir,
                            should_track_files_read          => $should_track_files_read,
                            use_basic_cipher_stream          => $use_basic_cipher_stream
                        },
                        [ "$SERIF_EXE", $serif_par ]
                    );
                push(@serif_jobs, $serif_jobid);
            }

        }
        else {
            my $serif_uri = get_param($params, "serif_server_mode_endpoint");
            my $serif_jobid =
                runjobs(
                    [ $split_serif_jobid ], $serif_job_name,
                    {
                        SGE_VIRTUAL_FREE => "1G",
                        BATCH_QUEUE      => $LINUX_QUEUE,
                    },
                    [ "$PYTHON3 $SERIF_SERVER_MODE_CLIENT_SCRIPT --file_list_path $batch_file --output_directory_path $experiment_dir --server_http_endpoint $serif_uri" ]
                );
            push(@serif_jobs, $serif_jobid);
        }
    }

    # convert factfinder results into json file that the
    # serialize stage will use
    if ((get_param($params, "serif_server_mode_endpoint", "None") eq "None") and ($mode eq "CauseEx")) {
        my $process_factfinder_results_job_name = "$JOB_NAME/$stage_name/process_factfinder_results";
        my $process_factfinder_results_jobid =
            runjobs(
                \@serif_jobs, $process_factfinder_results_job_name,
                {
                    BATCH_QUEUE => $LINUX_QUEUE,
                },
                [ "$PYTHON3 $FACTFINDER_TO_JSON_SCRIPT $master_serif_output_dir $GENERATED_FACTFINDER_JSON_FILE" ]
            );
    }
    else {
        # @hqiu: Logic here is convoluted !!!
        make_output_dir($GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR);
    }
    # Compine results into one list
    my $list_results_jobid = generate_file_list(\@serif_jobs, "$JOB_NAME/$stage_name/list-serif-results", "$master_serif_output_dir/*/output/*.xml", $GENERATED_SERIF_SERIFXML);
}

dojobs();


#######
# BERT
#######
my $GENERATED_BERT_NPZ_LIST = "NONE";
if (exists $stages{"bert"}) {
    print "bert stage\n";
    my $stage_processing_dir = make_output_dir("$processing_dir/bert");
    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_files");
    my $input_serifxml_list =
        get_param($params, "bert_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_SERIF_SERIFXML
            : get_param($params, "bert_input_serifxml_list");
    my $BERT_layers =
        get_param($params, "bert_layers") eq "DEFAULT"
            ? "-1"
            : get_param($params, "bert_layers");
    my $stage_name = "bert";
    $GENERATED_BERT_NPZ_LIST = "$stage_processing_dir/bert_npz.list";
    my ($NUM_JOBS, $split_bert_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_bert_batch_files", $input_serifxml_list, "$batch_file_directory/bert_batch_file_", $BATCH_SIZE);

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
}

dojobs();

######
# KBP
######
my $GENERATED_KBP_SERIFXML = $GENERATED_SERIF_SERIFXML;
if (exists $stages{"kbp"}) {
    print "KBP stage\n";
    $GENERATED_KBP_SERIFXML = "$processing_dir/kbp_serifxml.list";

    my $input_serifxml_list =
        get_param($params, "kbp_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_SERIF_SERIFXML
            : get_param($params, "kbp_input_serifxml_list");
    my $stage_name = "kbp";
    my $master_kbp_output_dir = make_output_dir("$processing_dir/kbp");
    my $batch_file_directory = make_output_dir("$master_kbp_output_dir/batch_files");
    # Run KBP event finding in parallel

    my ($NUM_JOBS, $split_kbp_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_kbp_batch_files", $input_serifxml_list, "$batch_file_directory/kbp_batch_file_", $BATCH_SIZE);

    my @kbp_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_processing_dir = make_output_dir("$master_kbp_output_dir/$job_batch_num");
        my $strip_event_serif_out_dir = make_output_dir("$batch_processing_dir/strip_events/");
        my $batch_input_file = "$batch_file_directory/kbp_batch_file_$job_batch_num";
        my $stripped_events_serifxml_list = "$batch_file_directory/stripped_$job_batch_num.list";
        my $strip_events_jobid =
            runjobs(
                [ $split_kbp_jobid ], "$JOB_NAME/$stage_name/strip_events-$job_batch_num",
                {
                    input_file_list  => $batch_input_file,
                    output_dir       => $strip_event_serif_out_dir,
                    output_file_list => $stripped_events_serifxml_list,
                    BATCH_QUEUE      => $LINUX_QUEUE,
                },
                [ "$STRIP_EVENTS_EXE", "strip_events.par" ]
            );

        my $kbp_output_dir = "$master_kbp_output_dir/$job_batch_num/output";
        my $kbp_output_serifxml_list = "$master_kbp_output_dir/$job_batch_num/serifxml.list";
        my $kbp_job_name = "$JOB_NAME/$stage_name/kbp-$job_batch_num";
        my $kbp_jobid =
            runjobs(
                [ $strip_events_jobid ], $kbp_job_name,
                {
                    git_repo                   => $git_repo,
                    output_file_list           => $kbp_output_serifxml_list,
                    input_file_list            => $stripped_events_serifxml_list,
                    output_directory           => $kbp_output_dir,
                    SERIF_DATA                 => $SERIF_DATA,
                    BATCH_QUEUE                => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE           => "16G",
                    dependencies_root          => $dependencies_root,
                    external_dependencies_root => $external_dependencies_root
                },
                [ "$KBP_EVENT_FINDER_EXE", "kbp_event_finder.par" ]
            );
        push(@kbp_jobs, $kbp_jobid);
    }

    # Compine results into one list
    my $list_results_jobid = generate_file_list(\@kbp_jobs, "$JOB_NAME/$stage_name/list-kbp-results", "$master_kbp_output_dir/*/output/*.xml", $GENERATED_KBP_SERIFXML);
}

dojobs();

##################
## Generic events
##################
my $GENERATED_GENERIC_EVENTS_SERIFXML = $GENERATED_KBP_SERIFXML;
if (exists $stages{"generic-events"}) {
    print "Generic events stage\n";

    my $input_serifxml_list =
        get_param($params, "generic_events_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_KBP_SERIFXML
            : get_param($params, "generic_events_input_serifxml_list");
    my $stage_name = "generic_events";
    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_files");
    $GENERATED_GENERIC_EVENTS_SERIFXML = "$processing_dir/generic_events_serifxml_out.list";

    my ($NUM_JOBS, $split_generic_events_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_generic_events_batch_files", $input_serifxml_list, "$batch_file_directory/generic_events_batch_file_", $BATCH_SIZE);
    my @generic_events_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/generic_events_batch_file_$job_batch_num";
        my $output_serifxml_dir = make_output_dir("$stage_processing_dir/$job_batch_num/output/");
        my $add_event_mentions_from_propositions_jobid =
            runjobs(
                [ $split_generic_events_jobid ], "$JOB_NAME/generic_events/add_event_mentions_from_propositions_$job_batch_num",
                {
                    bin                  => $ADD_EVENT_MENTION_BY_POS_TAGS_EXE,
                    strListSerifXmlFiles => $batch_file,
                    strOutputDir         => $output_serifxml_dir,
                    file_whitelist       => "$hume_repo_root/resource/generic_events/generic_event.whitelist.wn-fn.variants",
                    file_blacklist       => "$hume_repo_root/resource/generic_events/modal_aux.verbs.list",
                    SGE_VIRTUAL_FREE     => "32G",
                    BATCH_QUEUE          => $LINUX_QUEUE,
                },
                [ "sh", "add_event_mentions_by_pos_tags.sh" ]
            );
        push(@generic_events_split_jobs, $add_event_mentions_from_propositions_jobid);
    }

    my $list_results_jobid = generate_file_list(\@generic_events_split_jobs, "$JOB_NAME/$stage_name/list-generic-events-results", "$stage_processing_dir/*/output/*.xml", $GENERATED_GENERIC_EVENTS_SERIFXML);
}

dojobs();


###################################
# LearnIt  UnaryEvent and EventArg
###################################
my $LEARNIT_DECODING_EVENT_AND_EVENT_ARG_SERIFXML = $GENERATED_GENERIC_EVENTS_SERIFXML;
if (exists $stages{"learnit-decoding-event-and-eventarg"}) {
    print "LearnIt event and event arg stage\n";
    my $learnit_event_and_event_arg_pattern_dir = get_param($params, "learnit_event_and_event_arg_pattern_dir") eq "DEFAULT"
        ? "$hume_repo_root/resource/learnit_patterns/event_and_event_arg"
        : get_param("learnit_event_and_event_arg_pattern_dir");
    my $input_serifxml_list =
        get_param($params, "learnit_decoding_event_and_event_arg_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_GENERIC_EVENTS_SERIFXML
            : get_param($params, "learnit_decoding_event_and_event_arg_input_serifxml_list");
    $LEARNIT_DECODING_EVENT_AND_EVENT_ARG_SERIFXML = "$processing_dir/learnit_decoding_event_and_event_arg.list";
    my $stage_name = "learnit_event_and_eventarg";
    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
    my $batch_file_folder = make_output_dir("$stage_processing_dir/batch_file");
    my ($NUM_JOBS, $split_serifxml_list_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_" . $stage_name . "_batch_file", $input_serifxml_list, "$batch_file_folder/", $BATCH_SIZE);
    my @learnit_decoder_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_processing_folder = make_output_dir("$stage_processing_dir/$job_batch_num");
        my $learnit_decoder_batch_jobid = learnit_decoder([ $split_serifxml_list_jobid ], $batch_file_folder, $job_batch_num, $batch_processing_folder, "unary_event_or_event_arg", "EventAndEventArgument", $learnit_event_and_event_arg_pattern_dir, "$JOB_NAME/$stage_name");
        push(@learnit_decoder_jobs, $learnit_decoder_batch_jobid);
    }
    my $generate_new_serifxml_filelist_jobid = runjobs(
        \@learnit_decoder_jobs, "$JOB_NAME/$stage_name/result_job_list",
        {
            SCRIPT      => 1,
            BATCH_QUEUE => $LINUX_QUEUE
        },
        [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$stage_processing_dir/*/output/*.xml\" --output_list_path $LEARNIT_DECODING_EVENT_AND_EVENT_ARG_SERIFXML" ]
    );
}
dojobs();

##################
# NN Event Typing 
##################
my $GENERATED_NN_EVENT_SERIFXML = $LEARNIT_DECODING_EVENT_AND_EVENT_ARG_SERIFXML;

if (exists $stages{"nn-event-typing"}) {
    print "NN Event Typing stage\n";

    my $input_serifxml_list =
        get_param($params, "nn_event_typing_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_GENERIC_EVENTS_SERIFXML
            : get_param($params, "nn_event_typing_input_serifxml_list");

    my $nn_event_typing_processing_dir = make_output_dir("$processing_dir/nn_event_typing");
    my $nn_event_typing_prefix = "nn_event_typing";

    # create_nn_decoder_input
    my $nn_type_decoder_output_dir = make_output_dir("$nn_event_typing_processing_dir/nn_type_decoder_output/");
    my $serif_instances = "$nn_type_decoder_output_dir/serif_instances.tsv";
    my $serif_instances_mapper = "$nn_type_decoder_output_dir/serif_instances_mapper.tsv";
    my $nn_type_decoding_dataset = "$nn_type_decoder_output_dir/decoding_dataset.pkl";
    my $create_nn_type_decoder_input_job_id =
        runjobs(
            [], "$JOB_NAME/nn_event_typing/1_nn_types/create_nn_type_decoder_input",
            {
                serifxml_list             => $input_serifxml_list,
                serif_instances           => $serif_instances,
                instance_to_source_mapper => $serif_instances_mapper,
                decoding_dataset          => $nn_type_decoding_dataset,
                nn_typing_code_root       => "$hume_repo_root/util/python/nn_entity_typing",
                ANACONDA_ROOT             => $ANACONDA_PY2_ROOT_FOR_NN_EVENT_TYPING,
                CONDA_ENV_NAME            => $CONDA_ENV_NAME_FOR_NN_EVENT_TYPING,
                SGE_VIRTUAL_FREE          => "75G",
                BATCH_QUEUE               => $LINUX_QUEUE,
                model_dir                 => "$dependencies_root/nn_event_typing/nn_entity_models/m15_20181115/model"
            },
            [ "sh ", "prepare_nn_event_type_decoding_input.sh" ]
        );
    dojobs();

    # nn_type_decoding
    my $nn_type_predictions = "$nn_type_decoder_output_dir/nn_type_predictions.tsv";
    my $run_nn_type_decoding_job_id =
        runjobs(
            [ $create_nn_type_decoder_input_job_id ], "$JOB_NAME/nn_event_typing/1_nn_types/run_nn_type_decoding",
            {
                decoding_dataset        => $nn_type_decoding_dataset,
                predicted_labels_output => $nn_type_predictions,
                nn_typing_code_root     => "$hume_repo_root/util/python/nn_entity_typing",
                ANACONDA_ROOT           => $ANACONDA_PY2_ROOT_FOR_NN_EVENT_TYPING,
                CONDA_ENV_NAME          => $CONDA_ENV_NAME_FOR_NN_EVENT_TYPING,
                SGE_VIRTUAL_FREE        => "128G",
                BATCH_QUEUE             => $LINUX_QUEUE,
                model_dir               => "$dependencies_root/nn_event_typing/nn_entity_models/m15_20181115/model"
            },
            [ "sh ", "run_nn_event_type_decoding.sh" ]
        );
    dojobs();

    my $nn_event_typing_serifxml_dir = "$processing_dir/serifxml_out_nn_event_typing/";
    my $nn_event_typing_serifxml_list = "$processing_dir/serifxml_out_nn_event_typing.list";

    my $update_serifxml_with_event_typing_job_id =
        runjobs(
            [ $run_nn_type_decoding_job_id ], "$JOB_NAME/nn_event_typing/2_update_serif/update_serifxml_with_event_typing",
            {
                serifxml_list         => $input_serifxml_list,
                output_dir            => $nn_event_typing_serifxml_dir,
                output_list           => $nn_event_typing_serifxml_list,
                serif_instance_mapper => $serif_instances_mapper,
                nn_type_predictions   => $nn_type_predictions,
                SGE_VIRTUAL_FREE      => "32G",
                BATCH_QUEUE           => $LINUX_QUEUE,
            },
            [ "sh", "update_serifxml_with_event_typing.sh" ]
        );

    dojobs();

    $GENERATED_NN_EVENT_SERIFXML = $nn_event_typing_serifxml_list;
}

dojobs();


######################
# NN event extraction
######################
my $GENERATED_NN_EVENTS_SERIFXML = $GENERATED_NN_EVENT_SERIFXML;
if (exists $stages{"nn-events"}) {
    print "NN events stage\n";
    # NN models directory path for nlplingo
    $GENERATED_NN_EVENTS_SERIFXML = "$processing_dir/nn_events_serifxml.list";
    my $nn_events_model_list = "";

    if (get_param($params, "nn_events_model_list") eq "DEFAULT") {
        if ($mode eq "CauseEx") {
            $nn_events_model_list = "$external_dependencies_root/cx/nlplingo/nn_models.list";
        }
        else {
            $nn_events_model_list = "$external_dependencies_root/wm/nlplingo/nn_models.list";
        }
    }
    else {
        $nn_events_model_list = get_param($params, "nn_events_model_list");
    }

    my $input_serifxml_list =
        get_param($params, "nn_events_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_NN_EVENT_SERIFXML
            : get_param($params, "nn_events_input_serifxml_list");
    my $stage_name = "nn_events";
    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_file");
    # Run NN event finding in parallel
    my ($NUM_JOBS, $split_nn_events_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_nn_events_batch_files", $input_serifxml_list, "$batch_file_directory/nn_events_batch_file_", $BATCH_SIZE);

    my @nn_add_events_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/nn_events_batch_file_$job_batch_num";

        my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num");
        my $nn_events_batch_output = make_output_dir("$batch_processing_dir/output");
        my $genericity_added_batch_output = make_output_dir("$batch_processing_dir/genericity_output");
        my $nn_events_batch_output_list = "$batch_file_directory/nn_events_genericity_batch_file_$job_batch_num";
        my $nn_events_genericity_output_list = "$batch_processing_dir/nn_events_genericity.DONOTUSE"; # DO NOT USE THIS JUST A PLACEHOLDER

        my $batch_predictions_file = "$batch_processing_dir/predictions.json";
        my $merge_nn_output_jobid;

        if (get_param($params, "nn_event_server_mode_endpoint", "None") eq "None") {
            my $add_prefix_to_serifxml_in_list =
                runjobs(
                    [ $split_nn_events_jobid ], "$JOB_NAME/$stage_name/add_prefix_$job_batch_num",
                    {
                        BATCH_QUEUE      => $LINUX_QUEUE,
                        SGE_VIRTUAL_FREE => "4G",
                        SCRIPT           => 1,
                    },
                    [ "$PYTHON3 $PREPARE_SERIF_EMBEDDING_FILELIST_SCRIPT $batch_file $GENERATED_BERT_NPZ_LIST $batch_file.with_type" ]
                    #[ "cat $batch_file | awk '{print \"SERIF:\"\$0}' > $batch_file\.with_type" ]
                );

            open my $handle, '<', $nn_events_model_list or die "Cannot open $nn_events_model_list: $!";;
            chomp(my @nn_models = <$handle>);
            close $handle;

            my @nn_events_jobs = ();
            my @nn_prediction_files = ();
            foreach my $nn_model (@nn_models) {
                my ($nn_model_name, $nn_model_path) = ($nn_model =~ m/([^\0\ \/]+)\ ([^\0]+)/);

                my $nn_events_batch_model_dir = "$batch_processing_dir/$nn_model_name";
                my $nn_events_batch_model_output_dir = "$nn_events_batch_model_dir/output";

                make_output_dir($nn_events_batch_model_dir);
                make_output_dir($nn_events_batch_model_output_dir);

                my $nn_events_job_name = "$JOB_NAME/$stage_name/$job_batch_num" . "_" . $nn_model_name;
                my $bash_file = "$nn_events_batch_model_output_dir/run.sh";
                my $main_command = "PYTHONPATH=$NNEVENT_PYTHON_PATH " .
                    "KERAS_BACKEND=tensorflow " .
                    "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_NLPLINGO/bin/python " .
                    "$NNEVENT_DECODE_SCRIPT --params \$1 --mode decode_trigger_argument";
                open OUT, ">$bash_file";
                print OUT $main_command . "\n";
                print OUT "exit \$status\n";
                close OUT;

                my $cmd = "chmod +x $bash_file";
                `$cmd`;

                $cmd = "$bash_file";
                if ($mode eq "CauseEx") {
                    my $nn_events_jobid =
                        runjobs(
                            [ $add_prefix_to_serifxml_in_list ], $nn_events_job_name,
                            {
                                filelist_input             => "$batch_file\.with_type",
                                output_dir                 => $nn_events_batch_model_output_dir,
                                nn_model_dir               => $nn_model_path,
                                job_retries                => 1,
                                BATCH_QUEUE                => $LINUX_QUEUE,
                                SGE_VIRTUAL_FREE           => "32G",
                                ATOMIC                     => 1,
                                dependencies_root          => $dependencies_root,
                                external_dependencies_root => $external_dependencies_root
                            },
                            [ "/bin/bash $bash_file", "nlplingo_decode.par.cx.json" ]
                        );
                    push(@nn_events_jobs, $nn_events_jobid);
                }
                elsif ($mode eq "WorldModelers") {
                    my $nn_events_jobid =
                        runjobs(
                            [ $add_prefix_to_serifxml_in_list ], $nn_events_job_name,
                            {
                                filelist_input             => "$batch_file\.with_type",
                                output_dir                 => $nn_events_batch_model_output_dir,
                                nn_model_dir               => $nn_model_path,
                                job_retries                => 1,
                                BATCH_QUEUE                => $LINUX_QUEUE,
                                SGE_VIRTUAL_FREE           => "32G",
                                ATOMIC                     => 1,
                                dependencies_root          => $dependencies_root,
                                external_dependencies_root => $external_dependencies_root
                            },
                            [ "/bin/bash $bash_file", "nlplingo_decode.par.wm.json" ]
                        );
                    push(@nn_events_jobs, $nn_events_jobid);
                }
                else {
                    die "Not supported mode";
                }
                my $nn_prediction_file = $nn_events_batch_model_output_dir . "/prediction.json";
                push(@nn_prediction_files, $nn_prediction_file);
            }
            my $batch_predictions_list = "$batch_processing_dir/predictions.list";

            open my $fh, '>', $batch_predictions_list or die "Cannot open $batch_predictions_list: $!";
            print $fh join("\n", @nn_prediction_files);
            close $fh;

            $merge_nn_output_jobid = runjobs(
                \@nn_events_jobs, "$JOB_NAME/$stage_name/merge_nn_output_$job_batch_num",
                {
                    BATCH_QUEUE => $LINUX_QUEUE,
                    SCRIPT      => 1,
                },
                [ "$PYTHON3 $COMBINE_NN_EVENTS_JSON_SCRIPT $batch_predictions_list $batch_predictions_file" ]
            );
        }
        else {
            die "Nlplingo online decoding mode is broken";
            #			@hqiu. We have to update this later.
            #				my $nn_event_uri = get_param($params,"nn_event_server_mode_endpoint");
            #				my $nn_events_job_name = "$JOB_NAME/nn_events/$job_batch_num";
            #				my @nn_events_jobs = ();
            #				my $nn_events_jobid =
            #				$merge_nn_output_jobid = runjobs(
            #					[$split_nn_events_jobid], $nn_events_job_name,
            #					{
            #						SGE_VIRTUAL_FREE => "2G",
            #						BATCH_QUEUE => $LINUX_QUEUE,
            #					},
            #					["PYTHONPATH=$NLPLINGO_ROOT $PYTHON3 $NLPLINGO_SERVER_MODE_CLIENT_SCRIPT --file_list_path $batch_file --output_json_path $nn_events_batch_dir/predictions.json --server_http_endpoint $nn_event_uri"]
            #				);
            #				push(@nn_events_jobs, $nn_events_jobid);
        }


        # dojobs();

        # add decoded events from JSON to SerifXmls (as EventMentions)
        my $add_event_mentions_in_json_to_serifxmls_jobid =
            runjobs(
                [ $merge_nn_output_jobid ], "$JOB_NAME/$stage_name/add_em_$job_batch_num",
                {
                    bin                => $ADD_EVENT_MENTION_FROM_JSON_EXE,
                    inputFileJson      => $batch_predictions_file,
                    inputListSerifXmls => $batch_file,
                    outputDir          => $nn_events_batch_output,
                    BATCH_QUEUE        => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE   => "16G",
                    ATOMIC             => 1,
                },
                [ "sh", "add_event_mentions_in_json_to_serifxmls.sh" ]
            );
        my $list_nn_batch_results_jobid = generate_file_list([ $add_event_mentions_in_json_to_serifxmls_jobid ], "$JOB_NAME/$stage_name/list_results_$job_batch_num", "$nn_events_batch_output/*.serifxml", $nn_events_batch_output_list);

        push(@nn_add_events_jobs, $list_nn_batch_results_jobid);

        if (exists $stages{"kbp"}) {
            # run genericity classifier
            my $nn_event_genericity_job_name = "$JOB_NAME/$stage_name/genericity_$job_batch_num";
            my $nn_event_genericity_jobid =
                runjobs(
                    [ $list_nn_batch_results_jobid ], $nn_event_genericity_job_name,
                    {
                        git_repo                   => $git_repo,
                        dependencies_root          => $dependencies_root,
                        external_dependencies_root => $external_dependencies_root,
                        output_file_list           => $nn_events_genericity_output_list,
                        input_file_list            => $nn_events_batch_output_list,
                        output_directory           => $genericity_added_batch_output,
                        SERIF_DATA                 => $SERIF_DATA,
                        BATCH_QUEUE                => $LINUX_QUEUE,
                        SGE_VIRTUAL_FREE           => "8G",
                    },
                    [ "$KBP_EVENT_FINDER_EXE", "kbp_genericity_only.par" ]
                );
            push(@nn_add_events_jobs, $nn_event_genericity_jobid);
        }
    }

    # Combine results into one list
    if (exists $stages{"kbp"}) {
        my $list_results_jobid = generate_file_list(\@nn_add_events_jobs, "$JOB_NAME/$stage_name/list-nn-events-results", "$stage_processing_dir/*/genericity_output/*.serifxml", $GENERATED_NN_EVENTS_SERIFXML);
    }
    else {
        my $list_results_jobid = generate_file_list(\@nn_add_events_jobs, "$JOB_NAME/$stage_name/list-nn-events-results", "$stage_processing_dir/*/output/*.serifxml", $GENERATED_NN_EVENTS_SERIFXML);

    }
}

dojobs();


######################
# NN factor extraction
######################
#my $GENERATED_NN_FACTORS_SERIFXML = $GENERATED_NN_EVENTS_SERIFXML;
#if (exists $stages{"nn-factors"}) {
#    print "NN factors stage\n";
#    # NN models directory path for nlplingo
#    my $nn_factors_model_list = "";
#
#    if (get_param($params, "nn_factors_model_list") eq "DEFAULT") {
#        if ($mode eq "CauseEx") {
#            $nn_factors_model_list = "$external_dependencies_root/cx/nlplingo/nn_factor_models.list";
#        }
#        else {
#            $nn_factors_model_list = "$external_dependencies_root/wm/nlplingo/nn_factor_models.list";
#        }
#    }
#    else {
#        $nn_factors_model_list = get_param($params, "nn_factors_model_list");
#    }
#
#    my $input_serifxml_list =
#        get_param($params, "nn_factors_input_serifxml_list") eq "GENERATED"
#            ? $GENERATED_NN_FACTORS_SERIFXML
#            : get_param($params, "nn_factors_input_serifxml_list");
#    my $input_bert_npz_filelist =
#        get_param($params, "nn_factors_input_bert_npz_list") eq "GENERATED"
#            ? $GENERATED_BERT_NPZ_LIST
#            : get_param($params, "nn_factors_input_bert_npz_list");
#
#    $GENERATED_NN_FACTORS_SERIFXML = "$processing_dir/nn_factors_serifxml.list";
#    my $stage_name = "nn_factors";
#
#    my $MAPPING_PYPATH = "$hume_repo_root/src/python/knowledge_base/internal_ontology/";
#    my $factor_ontology;
#    my $which_ontology;
#    if ($mode eq "CauseEx") {
#        $which_ontology = "ICM";
#        $factor_ontology = "$internal_ontology_dir/icms/event_ontology.bae.yaml"
#    }
#    else {
#        $which_ontology = "WM";
#    }
#
#    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
#    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_file");
#    # Run NN event finding in parallel
#    my ($NUM_JOBS, $split_nn_factors_jobid) = split_file_for_processing(
#        "$JOB_NAME/$stage_name/make_nn_factors_batch_files",
#        $input_serifxml_list,
#        "$batch_file_directory/nn_factors_batch_file_",
#        $BATCH_SIZE);
#
#    my @nn_add_factors_jobs = ();
#
#    for (my $n = 0; $n < $NUM_JOBS; $n++) {
#        my $job_batch_num = sprintf("%05d", $n);
#        my $batch_file = "$batch_file_directory/nn_factors_batch_file_$job_batch_num";
#
#        my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num");
#        my $nn_factors_batch_output = make_output_dir("$batch_processing_dir/output");
#
#        my $nn_factors_batch_output_list = "$batch_file_directory/nn_factors_genericity_batch_file_$job_batch_num";
#
#        my $batch_predictions_file = "$batch_processing_dir/predictions.json";
#        my $merge_nn_output_jobid;
#
#        if (get_param($params, "nn_factor_server_mode_endpoint", "None") eq "None") {
#            my $add_prefix_to_serifxml_in_list =
#                runjobs(
#                    [ $split_nn_factors_jobid ], "$JOB_NAME/$stage_name/add_prefix_$job_batch_num",
#                    {
#                        BATCH_QUEUE      => $LINUX_QUEUE,
#                        SGE_VIRTUAL_FREE => "4G",
#                        SCRIPT           => 1,
#                    },
#                    [ "cat $batch_file | awk '{print \"SERIF:\"\$0}' > $batch_file\.with_type" ]
#                );
#
#            my $add_bert_to_serifxml_in_list =
#                runjobs(
#                    [ $add_prefix_to_serifxml_in_list ],
#                    "$JOB_NAME/$stage_name/add_bert_$job_batch_num",
#                    {
#                        BATCH_QUEUE      => $LINUX_QUEUE,
#                        SGE_VIRTUAL_FREE => "4G",
#                    },
#                    [ "$PYTHON3 $ADD_BERT_TO_FILELIST_SCRIPT "
#                      . "$batch_file\.with_type "
#                      . "$input_bert_npz_filelist "
#                      . "> $batch_file\.with_bert" ]
#                );
#
#            open my $handle, '<', $nn_factors_model_list or die "Cannot open $nn_factors_model_list: $!";;
#            chomp(my @nn_models = <$handle>);
#            close $handle;
#
#            my @nn_factors_jobs = ();
#            my @nn_prediction_files = ();
#            foreach my $nn_model (@nn_models) {
#                my ($nn_model_name, $nn_model_path) = ($nn_model =~ m/([^\0\ \/]+)\ ([^\0]+)/);
#
#                my $nn_factors_batch_model_dir = "$batch_processing_dir/$nn_model_name";
#                my $nn_factors_batch_model_output_dir = "$nn_factors_batch_model_dir/output";
#
#                make_output_dir($nn_factors_batch_model_dir);
#                make_output_dir($nn_factors_batch_model_output_dir);
#
#                my $nn_factors_job_name = "$JOB_NAME/$stage_name/$job_batch_num" . "_" . $nn_model_name;
#                my $bash_file = "$nn_factors_batch_model_output_dir/run.sh";
#                my $main_command = "PYTHONPATH=$NNEVENT_PYTHON_PATH " .
#                    "KERAS_BACKEND=tensorflow " .
#                    "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_NLPLINGO/bin/python " .
#                    "$NNEVENT_DECODE_SCRIPT --params \$1 --mode decode_trigger_argument";
#                open OUT, ">$bash_file";
#                print OUT $main_command . "\n";
#                print OUT "exit \$status\n";
#                close OUT;
#
#                my $cmd = "chmod +x $bash_file";
#                `$cmd`;
#
#                $cmd = "$bash_file";
#                if ($mode eq "CauseEx") {
#                    my $nn_factors_jobid =
#                        runjobs(
#                            [ $add_bert_to_serifxml_in_list ],
#                            $nn_factors_job_name,
#                            {
#                                filelist_input             => "$batch_file\.with_bert",
#                                output_dir                 => $nn_factors_batch_model_output_dir,
#                                nn_model_dir               => $nn_model_path,
#                                job_retries                => 1,
#                                BATCH_QUEUE                => $LINUX_QUEUE,
#                                SGE_VIRTUAL_FREE           => "32G",
#                                ATOMIC                     => 1,
#                                dependencies_root          => $dependencies_root,
#                                external_dependencies_root => $external_dependencies_root
#                            },
#                            [ "/bin/bash $bash_file", "nlplingo_decode.par.cx.icms.json" ]
#                        );
#                    push(@nn_factors_jobs, $nn_factors_jobid);
#                }
#                else {
#                    die "Not supported mode";
#                }
#                my $nn_prediction_file = $nn_factors_batch_model_output_dir . "/prediction.json";
#                push(@nn_prediction_files, $nn_prediction_file);
#            }
#            my $batch_predictions_list = "$batch_processing_dir/predictions.list";
#
#            open my $fh, '>', $batch_predictions_list or die "Cannot open $batch_predictions_list: $!";
#            print $fh join("\n", @nn_prediction_files);
#            close $fh;
#
#            $merge_nn_output_jobid = runjobs(
#                \@nn_factors_jobs, "$JOB_NAME/$stage_name/merge_nn_output_$job_batch_num",
#                {
#                    BATCH_QUEUE => $LINUX_QUEUE,
#                    SCRIPT      => 1,
#                },
#                [ "$PYTHON3 $COMBINE_NN_EVENTS_JSON_SCRIPT $batch_predictions_list $batch_predictions_file" ]
#            );
#        }
#        else {
#            die "Nlplingo online decoding mode is broken";
#            # see nn-events stage
#        }
#
#        # map to external sources
#        my $factor_mapping_jobid =
#            runjobs(
#                [ $merge_nn_output_jobid ],
#                "$JOB_NAME/$stage_name/map_to_external_$job_batch_num",
#                {
#                    BATCH_QUEUE      => $LINUX_QUEUE,
#                    SGE_VIRTUAL_FREE => "32G"
#                },
#                [ "env PYTHONPATH=$MAPPING_PYPATH "
#                    . "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_NLPLINGO"
#                    . "/bin/python $NN_MAPPING_SCRIPT "
#                    . "$batch_predictions_file "
#                    . "$factor_ontology "
#                    . "$which_ontology"
#                ]
#            );
#
#        # add decoded events from JSON to SerifXmls (as EventMentions)
#        my $add_event_mentions_in_json_to_serifxmls_jobid =
#            runjobs(
#                [ $factor_mapping_jobid ], "$JOB_NAME/$stage_name/add_em_$job_batch_num",
#                {
#                    bin                => $ADD_EVENT_MENTION_FACTORS_FROM_JSON_EXE,
#                    inputFileJson      => "$batch_predictions_file.mapped",
#                    inputListSerifXmls => $batch_file,
#                    outputDir          => $nn_factors_batch_output,
#                    BATCH_QUEUE        => $LINUX_QUEUE,
#                    SGE_VIRTUAL_FREE   => "16G",
#                    ATOMIC             => 1,
#                },
#                [ "sh", "add_event_mentions_in_json_to_serifxmls.sh" ]
#            );
#        my $list_nn_batch_results_jobid = generate_file_list([ $add_event_mentions_in_json_to_serifxmls_jobid ], "$JOB_NAME/$stage_name/list_results_$job_batch_num", "$nn_factors_batch_output/*.serifxml", $nn_factors_batch_output_list);
#
#        push(@nn_add_factors_jobs, $list_nn_batch_results_jobid);
#    }
#
#    my $list_results_jobid = generate_file_list(
#        \@nn_add_factors_jobs,
#        "$JOB_NAME/$stage_name/list-nn-factors-results",
#        "$stage_processing_dir/*/output/*.serifxml",
#        $GENERATED_NN_FACTORS_SERIFXML);
#}
#
#dojobs();


#######################################
# Bert centroid grounding for factors #
#######################################

my $GENERATED_BERT_CENTROID_GROUNDING_SERIFXML = $GENERATED_NN_EVENTS_SERIFXML;
if (exists $stages{"bert-centroid-grounding"}){
    print "BERT centroid grounding stage\n";

    my $input_serifxml_list =
        get_param($params,"bert_centroid_grounding_input_serifxml_list") eq "GENERATED"?
    $GENERATED_BERT_CENTROID_GROUNDING_SERIFXML:
            get_param($params,"bert_centroid_grounding_input_serifxml_list");
    my $input_bert_npz_list = get_param($params,"bert_centroid_grounding_bert_npz_list") eq "GENERATED"?
    $GENERATED_BERT_NPZ_LIST:get_param($params,"bert_centroid_grounding_bert_npz_list");

    $GENERATED_BERT_CENTROID_GROUNDING_SERIFXML = "$processing_dir/bert_centroid_grounding_serifxml_out.list";
    my $input_centroid_file = get_param($params,"bert_centroid_file");
    my $stage_name = "bert_centroid_grounding";
    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_files");
    my @bert_centroid_grounding_jobs = ();
    my ($NUM_JOBS, $split_bert_centroid_grounding_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_bert_centroid_grounding_batch_files", $input_serifxml_list, "$batch_file_directory/", $BATCH_SIZE);
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/$job_batch_num";
        my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num/output");
        my $bert_centroid_grounding_jobid = runjobs(
            [$split_bert_centroid_grounding_jobid],"$JOB_NAME/$stage_name/bert_centroid_batch_$job_batch_num",
            {
                BATCH_QUEUE                => $LINUX_QUEUE,
                SGE_VIRTUAL_FREE           => "8G",
            },
            ["env PYTHONPATH=$BERT_PYTHON_PATH $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT_CENTROID_GROUNDING/bin/python $BERT_CENTROID_GROUNDING_SCRIPT --file_centroid $input_centroid_file --serif_file_list $batch_file --npz_file_list $input_bert_npz_list --output_serif_folder $batch_processing_dir"]
        );
        push(@bert_centroid_grounding_jobs,$bert_centroid_grounding_jobid);
    }
    my $generate_event_consolidation_serifxml_list_jobid = generate_file_list(\@bert_centroid_grounding_jobs, "$JOB_NAME/$stage_name/list_bert_centroid_grounding_results", "$stage_processing_dir/*/output/*.xml", $GENERATED_BERT_CENTROID_GROUNDING_SERIFXML);
}
dojobs();

######################
# Event consolidation
######################
my $GENERATED_EVENT_CONSOLIDATION_SERIFXML = $GENERATED_BERT_CENTROID_GROUNDING_SERIFXML;
if (exists $stages{"event-consolidation"}) {
    print "Event consolidation stage\n";

    my $input_serifxml_list =
        get_param($params, "event_consolidation_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_EVENT_CONSOLIDATION_SERIFXML
            : get_param($params, "event_consolidation_input_serifxml_list");
    
    my $input_metadata_file = get_param($params, "event_consolidation_input_metadata_file");
    my $copyArgumentSentenceWindow = get_param($params, "copyArgumentSentenceWindow");

    $GENERATED_EVENT_CONSOLIDATION_SERIFXML = "$processing_dir/event_consolidation_serifxml_out.list";

    my $stage_name = "event_consolidation";
    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_files");
    my $argumentRoleEntityTypeFile = "";
    my $lemmaFile = "$external_dependencies_root/common/lemma.nv";

    my $ec_resource_dir = $mode eq "CauseEx" ? 
	"$hume_repo_root/resource/event_consolidation/causeex" :
	"$hume_repo_root/resource/event_consolidation/wm";

    my $ec_template = $mode eq "CauseEx" ?
	 "event_consolidation_cx.par" :
	 "event_consolidation_wm.par";
    
    my $eventOntologyYAMLFilePath = "$internal_ontology_dir/event_ontology.yaml";

    my $adverbFile = "$hume_repo_root/resource/event_consolidation/adverb.list";
    my $prepositionFile = "$hume_repo_root/resource/event_consolidation/prepositions.list";
    my $verbFile = "$hume_repo_root/resource/event_consolidation/verbs.wn-fn.variants.filtered";

    my $lightVerbFile = "$hume_repo_root/resource/event_consolidation/common/light_verbs.txt";
    my $interventionJson = "$hume_repo_root/resource/event_consolidation/wm/intervention.json";

    my $roleOntologyFile = "$hume_repo_root/resource/ontologies/internal/common/role_ontology.yaml";

    my ($NUM_JOBS, $split_event_consolidation_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_event_consolidation_batch_files", $input_serifxml_list, "$batch_file_directory/event_consolidation_batch_file_", $BATCH_SIZE);
    # $output_serifxml_dir = make_output_dir($output_serifxml_dir);
    my @event_consolidation_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/event_consolidation_batch_file_$job_batch_num";
        my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num/output");
        my $event_consolidation_jobid = runjobs(
            [ $split_event_consolidation_jobid ], "$JOB_NAME/$stage_name/run_event_consolidation_$job_batch_num",
            {
                strListSerifXmlFiles       => $batch_file,
                strOutputDir               => $batch_processing_dir,
                strInputMetadataFile       => $input_metadata_file,
                ontologyFile               => $eventOntologyYAMLFilePath,
                argumentRoleEntityTypeFile => "$ec_resource_dir/event_typerole.entity_type.constraints",
                keywordFile                => "$ec_resource_dir/event_type.keywords",
                blacklistFile              => "$ec_resource_dir/event_type.blacklist",
                lemmaFile                  => $lemmaFile, 
                polarityFile               => "$hume_repo_root/resource/event_consolidation/common/polarity_modifiers.txt",
                kbpEventMappingFile        => "$ec_resource_dir/KBP_events.json",
                accentEventMappingFile     => "$hume_repo_root/resource/event_consolidation/accent_event_mapping.json",
                accentCodeToEventTypeFile  => "$hume_repo_root/resource/event_consolidation/cameo_code_to_event_type.txt",
                adverbFile                 => $adverbFile,
                prepositionFile            => $prepositionFile,
                verbFile                   => $verbFile,
                roleOntologyFile           => $roleOntologyFile,
                lightVerbFile              => $lightVerbFile,
                interventionJson           => $interventionJson,
		copyArgumentSentenceWindow => $copyArgumentSentenceWindow,
	    
		BATCH_QUEUE                => $LINUX_QUEUE,
                SGE_VIRTUAL_FREE           => "32G",
            },
            [ $DOCTHEORY_RESOLVER_EXE, $ec_template ]
        );
        push(@event_consolidation_jobs, $event_consolidation_jobid)
    }

    my $generate_event_consolidation_serifxml_list_jobid = generate_file_list(\@event_consolidation_jobs, "$JOB_NAME/$stage_name/list_event_consolidation_results", "$stage_processing_dir/*/output/*.xml", $GENERATED_EVENT_CONSOLIDATION_SERIFXML);
}

dojobs();

##########################
# Probabilistic grounding
##########################

my $GENERATED_GROUNDING_SERIFXML = $GENERATED_EVENT_CONSOLIDATION_SERIFXML;
if (exists $stages{"probabilistic-grounding"}) {
    print "Probabilistic Grounding stage\n";
    my $stage_processing_dir = make_output_dir("$processing_dir/probabilistic-grounding");
    my $batch_file_directory = make_output_dir("$stage_processing_dir/batch_files");
    my $input_serifxml_list =
        get_param($params, "grounding_input") eq "GENERATED"
            ? $GENERATED_GROUNDING_SERIFXML
            : get_param($params, "grounding_input");
    $GENERATED_GROUNDING_SERIFXML = "$processing_dir/grounded_serifxml.list";
    my $stage_name = "probabilistic_grounding";
    my $PG_DIR = "$hume_repo_root/src/python/knowledge_base/internal_ontology/";
    my $event_ontology = "$internal_ontology_dir/event_ontology.yaml";
    my $exemplars = "$internal_ontology_dir/data_example_events.json";
    my $embeddings = "$external_dependencies_root/common/glove.6B.50d.p";
    my $lemmas = "$external_dependencies_root/common/lemma.nv";
    my $stopwords = "$internal_ontology_dir/stopwords.list";
    my $threshold = "0.7";
    my $n_best = 5;
    my $which_ontology = "";
    my $internal_ontology_yaml = "NONE";
    my $internal_ontology_bert_centroids = "$internal_ontology_dir/event_centroid.json";
    my $grounding_blacklist = "NONE";
    my $keywords = "$internal_ontology_dir/keywords-anchor_annotation.txt";
    if ($mode eq "CauseEx") {
        $which_ontology = "CAUSEEX";
    }
    else {
        $which_ontology = "WM";
        $internal_ontology_yaml = $event_ontology;
        $event_ontology = "$external_ontology_dir/wm_metadata.yml";
        $grounding_blacklist = "$external_dependencies_root/wm/wm.blacklist.json";
    }

    $which_ontology =  # replace default ontology flag if specified
        get_param($params, "grounding_flag", "DEFAULT") eq "DEFAULT"
        ? $which_ontology
        : get_param($params, "grounding_flag");
    $threshold =  # replace default threshold if specified
        get_param($params, "grounding_threshold", "DEFAULT") eq "DEFAULT"
        ? $threshold
        : get_param($params, "grounding_threshold");
    $n_best =  # replace default n_best if specified
        get_param($params, "grounding_n_best", "DEFAULT") eq "DEFAULT"
        ? $n_best
        : get_param($params, "grounding_n_best");

    # "NONE" acceptable for when not using BERT
    my $bert_npz_file_list =
        get_param($params, "grounding_bert_npz_filelist") eq "GENERATED"
            ? $GENERATED_BERT_NPZ_LIST
            : get_param($params, "grounding_bert_npz_filelist");

    my ($NUM_JOBS, $split_probabilistic_grounding_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_probabilistic_grounding_batch_files", $input_serifxml_list, "$batch_file_directory/probabilistic_grounding_batch_file_", $BATCH_SIZE);

    my @probabilistic_grounding_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/probabilistic_grounding_batch_file_$job_batch_num";
        my $batch_processing_dir = make_output_dir("$stage_processing_dir/$job_batch_num");
        my $batch_output_dir = make_output_dir("$batch_processing_dir/output");
        my $GENERATED_GROUNDING_CACHE = "$batch_processing_dir/$job_batch_num.json";
        # 1. run grounder over input to produce cache
        my $grounding_generation_jobid =
            runjobs(
                [ $split_probabilistic_grounding_jobid ],
                "$JOB_NAME/$stage_name/generate_cache_$job_batch_num",
                {
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE => "32G"
                },
                [ "env PYTHONPATH=$PG_DIR "
                    . "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_NLPLINGO/bin/python $PROB_GROUNDING_SCRIPT "
                    . "--event_ontology_yaml $event_ontology "
                    . "--internal_ontology_yaml $internal_ontology_yaml "
                    . "--exemplars $exemplars "
                    . "--bert_centroids $internal_ontology_bert_centroids "
                    . "--bert_npz_file_list $bert_npz_file_list "
                    . "--embeddings $embeddings "
                    . "--lemmas $lemmas "
                    . "--stopwords $stopwords "
                    . "--keywords $keywords "
                    . "--threshold $threshold "
                    . "--which_ontology $which_ontology "
                    . "--n_best $n_best "
                    . "--blacklist $grounding_blacklist "
                    . "--serifxmls $batch_file "
                    . "--output $GENERATED_GROUNDING_CACHE "
                ]
            );

        # 2. inject groundings into new serifxmls
        my $grounding_injection_jobid =
            runjobs(
                [ $grounding_generation_jobid ],
                "$JOB_NAME/$stage_name/add_grounded_types_from_cache_$job_batch_num",
                {
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE => "32G"
                },
                [ "$PROB_GROUNDING_INJECTION_EXE "
                    . "$GENERATED_GROUNDING_CACHE "
                    . "$batch_file "
                    . "$batch_output_dir" ]
            );
        push(@probabilistic_grounding_split_jobs, $grounding_injection_jobid);
    }

    # 3. save new serifxmls as filelist
    my $list_grounding_results_jobid = generate_file_list(\@probabilistic_grounding_split_jobs, "$JOB_NAME/$stage_name/list_grounding_serifxml", "$stage_processing_dir/*/output/*.xml", $GENERATED_GROUNDING_SERIFXML);

}

dojobs();

#################
# Event timeline
#################

if (exists $stages{"event-timeline"}) {
    my $event_timeline_input_serifxml_list =
        get_param($params, "event_timeline_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_GROUNDING_SERIFXML
            : get_param($params, "event_timeline_input_serifxml_list");
    my $output_event_timeline_dir = make_output_dir("$processing_dir/event_timeline_output");
    my $extract_event_timestamp_info_jobid = runjobs(
        [], "$JOB_NAME/event_timeline/1_extract_event_timestamp",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "32G"
        },
        [ "$EXTRACT_TIMELINE_FROM_SERIFXML_EXE $event_timeline_input_serifxml_list $output_event_timeline_dir/event_timeline.ljson" ]
    );
    my $group_eventmention_in_timeline_bucket = runjobs(
        [ $extract_event_timestamp_info_jobid ], "$JOB_NAME/event_timeline/2_group_into_bucket",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "2G"
        },
        [ "$PYTHON3 $GROUP_EVENTMENTION_IN_TIMELINE_BUCKET_SCRIPT $output_event_timeline_dir/event_timeline.ljson > $output_event_timeline_dir/event_timeline.table" ]
    );
}

dojobs();


########################
# Event-Event Relations
########################

my $GENERATED_EVENT_EVENT_RELATION_SERIFXML = $GENERATED_GROUNDING_SERIFXML;

if (exists $stages{"event-event-relations"}) {
    print "Event-Event relations stage\n";

    $GENERATED_EVENT_EVENT_RELATION_SERIFXML = "$processing_dir/event_event_relations_serifxml.list";
    my $input_serifxml_list =
        get_param($params, "eer_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_GROUNDING_SERIFXML
            : get_param($params, "eer_input_serifxml_list");

    my $input_serif_cause_effect_json_dir =
        get_param($params, "eer_input_serif_cause_effect_relations_dir") eq "GENERATED"
            ? $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR
            : get_param($params, "eer_input_serif_cause_effect_relations_dir");

    my $stage_name = "event_event_relation";
    my $stage_processing_dir = make_output_dir("$processing_dir/$stage_name");
    my $batch_file_dir = make_output_dir("$stage_processing_dir/batch_files");
    my $useOnlyPropPatterns = "all";
    my $USE_TRIPLE_WHITE_LIST = "na";
    my $learnit_pattern_dir = get_param($params, "learnit_pattern_dir") eq "DEFAULT"
        ? "$hume_repo_root/resource/learnit_patterns/binary_event_event"
        : get_param("learnit_input_pattern_dir");
    my $str_file_triple_relation_event_pairs = "na";

    my $MIN_FREQ_EVENT_PAIRS = get_param($params, "learnit_min_freq_event_pairs");
    my $learnit_relations_file = "$stage_processing_dir/learnit_event_event_relations_file.json";
    my $nre_relations_file_old = "$stage_processing_dir/nre_event_event_relations_file_old.json";
    my $nre_relations_file_ldc = "$stage_processing_dir/nre_event_event_relations_file_ldc.json";
    my $nre_relations_file_unified = "$stage_processing_dir/nre_event_event_relations_file.json";
    my $GENERATED_LEARNIT_EVENT_COUNT_FILE = "$stage_processing_dir/event_triggers_in_causal_relations.txt";

    my ($NUM_JOBS, $split_learnit_jobid) = split_file_for_processing("$JOB_NAME/$stage_name/make_run_learnit_batch_files", $input_serifxml_list, "$batch_file_dir/", $BATCH_SIZE);

    my @learnit_decoding_jobs = ();
    my @nre_decoding_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_processing_folder = make_output_dir("$stage_processing_dir/$job_batch_num");

        my $input_batch_file = "$batch_file_dir/$job_batch_num";
        my $mappings_output_file = "$batch_processing_folder/mappings.sjson";

        # mappings creation
        my $learnit_mappings_jobid =
            runjobs(
                [ $split_learnit_jobid ], "$JOB_NAME/$stage_name/InstanceExtractor-$job_batch_num",
                {
                    SGE_VIRTUAL_FREE => "25G",
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    learnit_root     => $learnit_root,
                    source_lists     => $batch_file_dir,
                    corpus_name      => $JOB_NAME
                },
                [ "$LEARNIT_INSTANCE_EXTRACTOR_EXE", "learnit_minimal.par", "binary_event_event $input_batch_file $mappings_output_file" ]
            );

        #LearnIt Decoding
        my $learnit_out_dir = make_output_dir("$batch_processing_folder/LearnIt");
        my $decoding_output_file = "$learnit_out_dir/learnit_decoding.json";
        my $decoding_log_file = "$learnit_out_dir/learnit_decoding.log";

        my $learnit_decoding_jobid =
            runjobs(
                [ $learnit_mappings_jobid ], "$JOB_NAME/$stage_name/LearnItDecoding-$job_batch_num",
                {
                    SGE_VIRTUAL_FREE => "25G",
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    learnit_root     => $learnit_root,
                    source_lists     => $batch_file_dir,
                    corpus_name      => $JOB_NAME
                },
                [ "$LEARNIT_DECODER_SCRIPT", "learnit_minimal.par", "$mappings_output_file $learnit_root $decoding_output_file $useOnlyPropPatterns $MIN_FREQ_EVENT_PAIRS $USE_TRIPLE_WHITE_LIST $str_file_triple_relation_event_pairs $learnit_pattern_dir $decoding_log_file" ]
            );

        push(@learnit_decoding_jobs, $learnit_decoding_jobid);

        # NRE Decoding

        my $nre_output_folder = make_output_dir("$batch_processing_folder/NRE");
        my $nre_decoding_jobid_ldc = runjobs(
            [ $learnit_mappings_jobid ], "$JOB_NAME/$stage_name/NRE-LDC-$job_batch_num",
            {
                SGE_VIRTUAL_FREE => "25G",
                BATCH_QUEUE      => $LINUX_QUEUE,
                job_retries      => 1,
                ATOMIC           => 1,
                learnit_root     => $learnit_root,
                source_lists     => $batch_file_dir,
                corpus_name      => $JOB_NAME
            },
            [ "$NEURAL_RELATION_DECODER_SCRIPT_LDC", "learnit_minimal.par", "$mappings_output_file $nre_output_folder $learnit_root $deepinsight_root $nre_model_root $ANACONDA_ROOT py2-tf1 $JCAI_PT_CPU $ldc_model_root" ]
        );

        push(@nre_decoding_jobs, $nre_decoding_jobid_ldc);
    }

    # Combine LearnIt decoding result.
    my $generate_learnit_decoding_result_list_jobid = generate_file_list(\@learnit_decoding_jobs, "$JOB_NAME/$stage_name/list_learnit_decoding_result", "$stage_processing_dir/*/LearnIt/learnit_decoding.json", "$stage_processing_dir/list_learnit_decoding_result.list");
    my $combine_learnit_decoding_result_jobid = runjobs(
        [ $generate_learnit_decoding_result_list_jobid ], "$JOB_NAME/$stage_name/combine_learnit_decoding_result",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "$PYTHON3 $LEARNIT_JSON_AGGREGATOR_SCRIPT $stage_processing_dir/list_learnit_decoding_result.list $learnit_relations_file" ]
    );

    # Combine NRE decoding result for LDC.
    my $generate_nre_decoding_result_list_jobid_ldc = generate_file_list(\@nre_decoding_jobs, "$JOB_NAME/$stage_name/list_nre_decoding_result_ldc", "$stage_processing_dir/*/NRE/bag_predictions_ldc.json", "$stage_processing_dir/list_nre_decoding_result_ldc.list");
    my $combine_nre_decoding_result_jobid_ldc = runjobs(
        [ $generate_nre_decoding_result_list_jobid_ldc ], "$JOB_NAME/$stage_name/combine_nre_decoding_result_ldc",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "$PYTHON3 $LEARNIT_JSON_AGGREGATOR_SCRIPT $stage_processing_dir/list_nre_decoding_result_ldc.list $nre_relations_file_ldc.aggr" ]
    );

    my $nre_postprocessing_job_id_ldc =
        runjobs(
            [ $combine_nre_decoding_result_jobid_ldc ], "$JOB_NAME/$stage_name/nre_postprocessing_ldc",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $NRE_POSTPROCESSING $nre_relations_file_ldc.aggr $nre_relations_file_ldc.filtered" ]
        );

    my $nre_rescale_freq_job_id_ldc =
        runjobs(
            [ $nre_postprocessing_job_id_ldc ], "$JOB_NAME/$stage_name/nre_rescale_freq_ldc",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $NRE_RESCALE_FREQ $nre_relations_file_ldc.filtered $nre_relations_file_ldc.rescaled" ]
        );

    my $nre_strip_low_conf_job_id_ldc =
        runjobs(
            [ $nre_rescale_freq_job_id_ldc ], "$JOB_NAME/$stage_name/nre_strip_low_conf_ldc",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $NRE_STRIP_LOW_CONF $nre_relations_file_ldc.rescaled $nre_relations_file_ldc" ]
        );

    my $nre_decode_unify =         runjobs(
            [ $nre_strip_low_conf_job_id_ldc, $nre_strip_low_conf_job_id_ldc ], "$JOB_NAME/$stage_name/nre_decode_unify",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $NRE_UNIFY $nre_relations_file_old $nre_relations_file_ldc $nre_relations_file_unified" ]
        );

    # generate event count file
    my $generate_event_count_file_jobid =
        runjobs(
            [ $combine_learnit_decoding_result_jobid ], "$JOB_NAME/$stage_name/generate_event_count_file",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $EVENT_COUNT_SCRIPT $learnit_relations_file $GENERATED_LEARNIT_EVENT_COUNT_FILE" ],
        );

    # Add causal relations to serifxml
    my $input_json_list = "$input_serif_cause_effect_json_dir,$learnit_relations_file,$nre_relations_file_unified";

    my @create_event_event_relations_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_processing_folder = make_output_dir("$stage_processing_dir/$job_batch_num/serifxml_uncalibrated");
        my $input_batch_file = "$batch_file_dir/$job_batch_num";
        my $create_event_event_relations_jobid =
            runjobs(
                [ $nre_decode_unify, $combine_learnit_decoding_result_jobid ], "$JOB_NAME/$stage_name/add_causal_relations_$job_batch_num",
                {
                    input_serifxml_list       => $input_batch_file,
                    output_serifxml_directory => $batch_processing_folder,
                    input_json_list           => $input_json_list,
                    BATCH_QUEUE               => $LINUX_QUEUE,
                },
                [ "$EVENT_EVENT_RELATION_EXE", "event_event_relations.par" ],
            );
        push(@create_event_event_relations_split_jobs, $create_event_event_relations_jobid);
    }

    my $list_uncalibrate_eer_serif_jobid = generate_file_list(\@create_event_event_relations_split_jobs, "$JOB_NAME/$stage_name/list_uncalibrate_serifxml", "$stage_processing_dir/*/serifxml_uncalibrated/*.xml", "$stage_processing_dir/uncalibrated_serif.list");
    make_output_dir("$stage_processing_dir/output");
    my $calibrate_eer_score_jobid = runjobs(
        [ $list_uncalibrate_eer_serif_jobid ], "$JOB_NAME/$stage_name/calibrate_causal_relations",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "32G",
        },
        [ "$EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE $stage_processing_dir/uncalibrated_serif.list $stage_processing_dir/output" ]
    );

    my $list_eer_results_jobid = generate_file_list([ $calibrate_eer_score_jobid ], "$JOB_NAME/$stage_name/list_eer_serifxml", "$stage_processing_dir/output/*.xml", $GENERATED_EVENT_EVENT_RELATION_SERIFXML);

}

dojobs();

###################
# KB Serialization
###################
my $GENERATED_SERIALIZATION_DIR = "$processing_dir/serialization";
if (exists $stages{"serialization"}) {
    print "Serialization stage\n";

    my $input_serifxml_list =
        get_param($params, "serialization_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_EVENT_EVENT_RELATION_SERIFXML
            : get_param($params, "serialization_input_serifxml_list");

    my $input_factfinder_json_file =
        get_param($params, "serialization_input_factfinder_json_file") eq "GENERATED"
            ? $GENERATED_FACTFINDER_JSON_FILE
            : get_param($params, "serialization_input_factfinder_json_file");

    my $metadata_file = get_param($params, "serialization_input_metadata_file");
    my $awake_db = get_param($params, "serialization_input_awake_db", "NA");

    my $template_filename;
    my $ontology_flags;
    my $bbn_namespace;
    my $should_go_up_instead_of_using_backup_namespaces;
    if ($mode eq "CauseEx") {
        if (get_param($params, "serialization_also_output_jsonld", "NA") eq "True") {
            $template_filename = "kb_constructor_rdf_jsonld.par";
        }
        else {
            $template_filename = "kb_constructor_rdf.par";
        }
        $ontology_flags = "CAUSEEX";
        $should_go_up_instead_of_using_backup_namespaces = "false";
        $bbn_namespace = "http://graph.causeex.com/bbn#";
    }
    elsif ($mode eq "WorldModelers") {
        $template_filename = "kb_constructor_json_ld.par";
        $ontology_flags = "WM,WM_INDICATOR";
        $should_go_up_instead_of_using_backup_namespaces = "true,false";
        $bbn_namespace = "DO_NOT_USE_BACKUP_NAMESPACE,DO_NOT_USE_BACKUP_NAMESPACE";
    }

    my $serifxml_dir = "$processing_dir/final_serifxml";
    my $copy_serifxml_jobname = "$JOB_NAME/serialize/copy_final_serifxml";
    my $copy_serifxml_jobid =
        runjobs(
            [], $copy_serifxml_jobname,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $COPY_FILES_SCRIPT $input_serifxml_list $serifxml_dir \"$metadata_file\"" ]
        );
    dojobs();

    # Serialize!
    opendir(my $dh, $serifxml_dir);
    my @document_types = grep {-d "$serifxml_dir/$_" && !/^\.{1,2}$/} readdir($dh);
    make_output_dir($GENERATED_SERIALIZATION_DIR);
    foreach my $document_type (@document_types) {
        my $serializer_output_dir = make_output_dir("$GENERATED_SERIALIZATION_DIR/$document_type");

        my $input_serifxml_dir = "$serifxml_dir/$document_type";
        my $ttl_output_file = "$serializer_output_dir/$JOB_NAME";
        my $nt_output_file = "$serializer_output_dir/$JOB_NAME";
        my $jsonld_output_file = "$serializer_output_dir/$JOB_NAME";
        if ($mode eq "WorldModelers") {
            $jsonld_output_file = $jsonld_output_file . ".json-ld";
        }
        my $json_output_file = "$serializer_output_dir/$JOB_NAME.json";
        my $pickle_output_file = "$serializer_output_dir/$JOB_NAME.p";
        my $json_graph_file = "$serializer_output_dir/$JOB_NAME.graph.json";
        my $tabular_output_file = "$serializer_output_dir/$JOB_NAME.tsv";
        my $relation_tsv_file = "$serializer_output_dir/$JOB_NAME.relations.tsv";
        my $unification_output_dir = "$serializer_output_dir/unification_json";
        my $serialize_job_name = "$JOB_NAME/serialize/kb-$document_type";

        #	my $grounding_cache_dir = make_output_dir("$processing_dir/grounding_cache");

        # Use robust settings for serialization
        my $batch_queue = "gale-nongale-sl6";
        my $mem = "128G";

        if ($document_type eq "abstract" || $document_type eq "intel" || $document_type eq "strategicguidance") {
            # Less memory required
            $mem = "32G";
        }

        if ($document_type eq "analytic") {
            # Less memory required
            $mem = "64G";
        }

        my $serialize_jobid =
            runjobs(
                [ $copy_serifxml_jobid ], $serialize_job_name,
                {
                    serif_accent_event_type                         => "$hume_repo_root/resource/serif_data_causeex/accent/event_types.txt",
                    event_coreference_file                          => "NULL",
                    serifxml_dir                                    => $input_serifxml_dir,
                    metadata_file                                   => $metadata_file,
                    factfinder_json_file                            => $input_factfinder_json_file,
                    awake_db                                        => $awake_db,
                    pickle_output_file                              => $pickle_output_file,
                    jsonld_output_file                              => $jsonld_output_file,
                    json_output_file                                => $json_output_file,
                    json_graph_file                                 => $json_graph_file,
                    tabular_output_file                             => $tabular_output_file,
                    relation_tsv_file                               => $relation_tsv_file,
                    ttl_output_file                                 => $ttl_output_file,
                    nt_output_file                                  => $nt_output_file,
                    unification_output_dir                          => $unification_output_dir,
                    event_yaml                                      => "$internal_ontology_dir/event_ontology.yaml",
                    external_ontology_flags                         => $ontology_flags,
                    should_go_up_instead_of_using_backup_namespaces => $should_go_up_instead_of_using_backup_namespaces,
                    bbn_namespace             => $bbn_namespace,
                    mode                      => $mode,
                    seed_milestone            => "m17",
                    seed_type                 => $document_type,
                    seed_version              => "v1",
                    SGE_VIRTUAL_FREE          => $mem,
                    BATCH_QUEUE               => $batch_queue,
                    geoname_with_gdam_woredas => "$external_dependencies_root/wm/geoname_with_gdam_woredas.txt",
                    ontology_turtle_folder    => "$hume_repo_root/resource/ontologies/causeex/190206"
                },
                [ "$PYTHON3 $KB_CONSTRUCTOR_SCRIPT", $template_filename ]
            );
    }
}

dojobs();

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

sub check_requirements {

    my @required_git_repos = ();
    if (exists $stages{"kbp"}) {
        push(@required_git_repos, "$git_repo/kbp");
    }
    if (exists $stages{"event-event-relations"}) {
        push(@required_git_repos, "$git_repo/learnit");
        push(@required_git_repos, "$git_repo/deepinsight");
    }

    if (exists $stages{"nn-events"}) {
        push(@required_git_repos, "$git_repo/nlplingo");
    }

    # push(@required_git_repos, "$git_repo/jserif");

    for my $git_repo (@required_git_repos) {
        if (!-e $git_repo) {
            die "You must have the git repo: " . $git_repo . " cloned\n";

        }
        # get the required branch name for this repo
        # my $repo_name = substr $git_repo, (rindex($git_repo,'/')+1) ;
        # my $expected_branch_name = get_param($params, $repo_name."_branch", "master");

        # verify that the branch is correct
        # read the repo-name from .git/HEAD file
        # open(my $headFile, '<', $git_repo."/.git/HEAD") or die "Cannot verify branch of $repo_name; .git/HEAD file not found";
        # my @lines = <$headFile>;
        # my $branch_name = substr $lines[0], (rindex($lines[0],'/')+1) , -1;
        #if ($branch_name ne $expected_branch_name){
        #    die "The current branch of repo $repo_name ($branch_name) does not match the expected branch ($expected_branch_name)"
        # }
    }

    my @required_git_files = ();
    if (exists $stages{"nn-event-typing"}) {
        push(@required_git_files, "$hume_repo_root/src/java/serif-util/target/appassembler/bin/NeuralNamesModelInputOutputMapper");
    }
    if (exists $stages{"kbp"}) {
        push(@required_git_files, "$STRIP_EVENTS_EXE");
        push(@required_git_files, "$KBP_EVENT_FINDER_EXE");
    }

    if (exists $stages{"event-event-relations"}) {
        push(@required_git_files, "$git_repo/learnit/neolearnit/target/appassembler/bin/InstanceExtractor");
        push(@required_git_files, "$git_repo/learnit/neolearnit/target/appassembler/bin/EventEventRelationPatternDecoder");
        push(@required_git_files, "$EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE");
    }

    for my $git_file (@required_git_files) {
        if (!-e $git_file) {
            die "You must have the file: " . $git_file . " . You may need to mvn install a git repo\n";

        }
    }

    if (!defined $ENV{'SVN_PROJECT_ROOT'}) {
        die "You must set the environment variable SVN_PROJECT_ROOT in .bashrc to a Projects directory in an svn checkout\n";

    }

    my @required_svn_files = (
        $ENV{'SVN_PROJECT_ROOT'} . "/SERIF/par"
    );
    if ($mode eq "CauseEx") {
        push(@required_svn_files, "$ENV{'SVN_PROJECT_ROOT'}/W-ICEWS/lib");
    }
    for my $svn_file (@required_svn_files) {
        if (!-e $svn_file) {
            die "You must have $svn_file checked out from svn\n";

        }
    }
}

sub get_current_time {
    my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
    my $nice_timestamp = sprintf("%04d%02d%02d-%02d%02d%02d",
        $year + 1900, $mon + 1, $mday, $hour, $min, $sec);
    return $nice_timestamp;
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

sub learnit_decoder {
    my @previous_batch_task = @{$_[0]};
    my $batch_file_folder = $_[1];
    my $job_batch_num = $_[2];
    my $batch_processing_folder = $_[3];
    my $learnit_target = $_[4];
    my $stage_name = $_[5];
    my $learnit_extractor_dir = $_[6];
    my $JOB_PREFIX = $_[7];

    my $batch_file = "$batch_file_folder/$job_batch_num";
    my $serif_output_dir = make_output_dir("$batch_processing_folder/output");

    my $learnit_extractor_job_name = "$JOB_PREFIX/InstanceExtractor-$job_batch_num";
    my $output_learnit_autogenerated_mappings_path = "$batch_processing_folder/mappings.sjson";

    my $learnit_extractor_job_id = runjobs(
        \@previous_batch_task, $learnit_extractor_job_name,
        {
            SGE_VIRTUAL_FREE => "32G",
            BATCH_QUEUE      => $LINUX_QUEUE,
            learnit_root     => $learnit_root,
            source_lists     => $batch_file_folder,
            corpus_name      => $JOB_NAME
        },
        [ "$learnit_root/neolearnit/target/appassembler/bin/InstanceExtractor", "learnit_minimal.par", "$learnit_target $batch_file $output_learnit_autogenerated_mappings_path" ]
    );
    if ($stage_name eq "EventAndEventArgument" || $stage_name eq "EventEventRelation") {
        # Need attach LowRank Patterns as well
        my $learnit_extractor_attach_low_rank_job_name = "$JOB_PREFIX/AttachLowerRankPatternAtHigherRankTarget-$job_batch_num";
        # Reuse learnit_extractor_job_id is desired
        $learnit_extractor_job_id = runjobs(
            [ $learnit_extractor_job_id ], $learnit_extractor_attach_low_rank_job_name,
            {
                SGE_VIRTUAL_FREE => "32G",
                BATCH_QUEUE      => $LINUX_QUEUE,
                learnit_root     => $learnit_root,
                source_lists     => $batch_file_folder,
                corpus_name      => $JOB_NAME
            },
            [ "$learnit_root/neolearnit/target/appassembler/bin/AttachLowerRankPatternAtHigherRankTarget", "learnit_minimal.par", "$output_learnit_autogenerated_mappings_path $output_learnit_autogenerated_mappings_path" ]
        );
    }
    my $input_learnit_mappings_path = $output_learnit_autogenerated_mappings_path;
    my $output_learnit_mappings_labeled_path = "$batch_processing_folder/labeled.sjson";

    my $learnit_label_job_name = "$JOB_PREFIX/labeled/TargetAndScoreTableLabeler-$job_batch_num";
    my $learnit_label_jobid = runjobs(
        [ $learnit_extractor_job_id ], $learnit_label_job_name,
        {
            SGE_VIRTUAL_FREE => "32G",
            BATCH_QUEUE      => $LINUX_QUEUE,
            learnit_root     => $learnit_root,
            source_lists     => $batch_file_folder,
            corpus_name      => $JOB_NAME
        },
        [ "$learnit_root/neolearnit/target/appassembler/bin/TargetAndScoreTableLabeler", "learnit_minimal.par", "$learnit_extractor_dir $input_learnit_mappings_path $output_learnit_mappings_labeled_path" ]
    );
    my $learnit_serialize_job_name = "$JOB_PREFIX/SerifXMLSerializer-$job_batch_num";
    my $learnit_serifxml_jobid = runjobs(
        [ $learnit_label_jobid ], $learnit_serialize_job_name,
        {
            SGE_VIRTUAL_FREE => "32G",
            BATCH_QUEUE      => $LINUX_QUEUE,
            learnit_root     => $learnit_root,
            source_lists     => $batch_file_folder,
            corpus_name      => $JOB_NAME
        },
        [ "$learnit_root/neolearnit/target/appassembler/bin/SerifXMLSerializer", "learnit_minimal.par", "$batch_file $output_learnit_mappings_labeled_path $stage_name $serif_output_dir" ]
    );
    return $learnit_serifxml_jobid;

}
