#!/bin/env perl

# Requirements:
#
# Run with /opt/perl-5.20.0-x86_64/bin/perl or similar
# Use Java 8 -- export JAVA_HOME="/opt/jdk1.8.0_20-x86_64"
# environment variable SVN_PROJECT_ROOT (in .bashrc) should point to Active/Projects where SERIF/python, SERIF/par, W-ICEWS/lib are checked out
# If you have a "# Stop here for an non-interactive shell." section in your .bashrc file, make sure the relevant environment variables (above) are above that section to make sure runjobs can see them
# git clone jserif (branch: 364-add-event-from-json) 
# cd jserif/serif-util; mvn clean install
# git clone and mvn clean install learnit
# git clone kbp
# git clone deepinsight
# pip install rdflib-jsonld --user
# create a ~/.keras/keras.json file that matches: /d4m/home/azamania/.keras/keras.json
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
my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-sl69-non-k10s");

my $git_repo = abs_path("$exp_root/..");
my $hume_repo_root = abs_path("$exp_root");
my $learnit_root = "$git_repo/learnit";
my $deepinsight_root = "$git_repo/deepinsight";
my $dependencies_root = "$hume_repo_root/resource/dependencies";
my $external_dependencies_root = "/nfs/raid87/u10/shared/Hume";
my $unmanaged_external_dependencies_root = "/nfs/raid87/u11/users/hqiu/external_dependencies_unmanaged";

# Location of all the output of this sequence
my $processing_dir = make_output_dir("$exp_root/expts/$JOB_NAME");

# Make copy of config file for debugging purposes
copy($config_file, $processing_dir . "/" . get_current_time() . "-" . basename($config_file));

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
my $CONDA_ENV_NAME_FOR_NLPLINGO = "tensorflow-1.5";

my $ANACONDA_PY2_ROOT_FOR_NN_EVENT_TYPING = "$unmanaged_external_dependencies_root/nn_event_typing/anaconda2";
my $CONDA_ENV_NAME_FOR_NN_EVENT_TYPING = "python-tf0.11-cpu";

my $NLPLINGO_ROOT = "$dependencies_root/nlplingo/nlplingo_bert";

# Scripts
my $COPY_FILES_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/copy_serifxml_by_document_type.py";
my $KB_CONSTRUCTOR_SCRIPT = "$hume_repo_root/src/python/knowledge_base/kb_constructor.py";
my $COMBINE_NN_EVENTS_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/merge_event_mentions_in_json.py";
my $LEARNIT_JSON_AGGREGATOR_SCRIPT = "$learnit_root/scripts/decoder_learnit_output_aggregator.py";
my $LEARNIT_DECODER_SCRIPT = "$learnit_root/scripts/run_EventEventRelationPatternDecoder.sh";
my $LEARNIT_SCORER_SCRIPT = "$learnit_root/scripts/score_extracted_event_event_relations.py";
my $NNEVENT_DECODE_SCRIPT = "$NLPLINGO_ROOT/nlplingo/event/train_test.py";
my $FACTFINDER_TO_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/factfinder_output_to_json.py";
my $EVENT_COUNT_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/count_triggers_in_causal_relations.py";
my $PROB_GROUNDING_SCRIPT = "$hume_repo_root/src/python/misc/ground_serifxml.py";
my $CREATE_FILE_LIST_SCRIPT = "$PYTHON3 $hume_repo_root/src/python/pipeline/scripts/create_filelist.py";

my $NRE_JSON_AGGREGATOR_SCRIPT = "$learnit_root/scripts/decoder_nre_output_aggregator.py";
my $NEURAL_RELATION_DECODER_SCRIPT = "$learnit_root/scripts/run_EventEventRelationNeuralDecoder.sh";

my $nre_model_root = "$external_dependencies_root/common/event_event_relation/models/042219";
my $NRE_POSTPROCESSING = "$deepinsight_root/relations/src/postprocess.py";
my $NRE_RESCALE_FREQ = "$deepinsight_root/relations/src/rescale_freq.py";
my $NRE_STRIP_LOW_CONF = "$deepinsight_root/relations/src/strip_low_conf.py";

# my $SINGULARITY_WRAPPER = "$hume_repo_root/scripts/run-in-singularity-container.sh";

my $CAUSEEX_RELEASE_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/causeex_release.py";

my $SERIF_SERVER_MODE_CLIENT_SCRIPT = "$hume_repo_root/experiments/service_mode/serif_client.py";
my $NLPLINGO_SERVER_MODE_CLIENT_SCRIPT = "$hume_repo_root/experiments/service_mode/nlplingo_client.py";
my $GROUP_EVENTMENTION_IN_TIMELINE_BUCKET_SCRIPT = "$hume_repo_root/src/python/util/group_event_mention_in_timeline_bucket.py";

# Exes
my $BASH = "/bin/bash";
my $SERIF_EXE = "$hume_repo_root/bin/Serif";
my $JSERIF_ROOT = "$git_repo/jserif/";
my $STRIP_EVENTS_EXE = "$JSERIF_ROOT/serif-core-bin/target/appassembler/bin/stripEvents";
my $KBP_EVENT_FINDER_EXE = "$JSERIF_ROOT/serif-events-graveyard/target/appassembler/bin/eventFinderHighMem";
my $EVENT_EVENT_RELATION_EXE = "$JSERIF_ROOT/serif-util/target/appassembler/bin/EventEventRelationCreator";
my $LEARNIT_INSTANCE_EXTRACTOR_EXE = "$learnit_root/neolearnit/target/appassembler/bin/InstanceExtractor";
my $PROB_GROUNDING_INJECTION_EXE = "$JSERIF_ROOT/serif-util/target/appassembler/bin/GroundEventTypeFromJson";
my $EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE = "$JSERIF_ROOT/serif-util/target/appassembler/bin/CalibrateConfidences";
my $EXTRACT_TIMELINE_FROM_SERIFXML_EXE = "$JSERIF_ROOT/serif-util/target/appassembler/bin/DumpEventMentionForEventTimeline";

# Libraries
my $NNEVENT_PYTHON_PATH = "$dependencies_root/nlplingo/serifxml_py3_tmp:" . "$NLPLINGO_ROOT";

# Please let @hqiu know if you want to change $SERIF_DATA
my $SERIF_DATA = "/d4m/serif/data";

my $BATCH_SIZE = get_param($params, "batch_size", 100);
my $NN_EVENTS_BATCH_SIZE = get_param($params, "nn_events_batch_size", 150);
my $mode = get_param($params, "mode");
my $internal_ontology_dir;
if ($mode eq "CauseEx") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/causeex/";
}
elsif ($mode eq "WorldModelers") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/hume/";
}
else {
    die "mode has to be CauseEx or WorldModelers";
}

# Batch files
my $batch_file_directory = make_output_dir("$processing_dir/batch_files");

die "check_requirements failed!\n" unless check_requirements();

# Max jobs setting
max_jobs("$JOB_NAME/serif" => 200,);
max_jobs("$JOB_NAME/kbp" => 200,);
max_jobs("$JOB_NAME/generic_events" => 200,);
max_jobs("$JOB_NAME/learnit" => 200,);
max_jobs("$JOB_NAME/nn_events" => 300,);
max_jobs("$JOB_NAME/probabilistic_grounding" => 300,);
max_jobs("$JOB_NAME/event_consolidation" => 200,);
max_jobs("$JOB_NAME/learnit" => 200,);
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
    my ($NUM_JOBS, $split_serif_jobid) = split_file_for_processing("make_serif_batch_files", $input_sgm_list, "$batch_file_directory/serif_batch_file_", $BATCH_SIZE);
    my $par_dir = $ENV{"SVN_PROJECT_ROOT"} . "/SERIF/par";
    my $master_serif_output_dir = make_output_dir("$processing_dir/serif");
    my $should_track_files_read = get_param($params, "track_serif_files_read", "true");
    my $use_basic_cipher_stream = get_param($params, "use_basic_cipher_stream", "false");
    my @serif_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $serif_job_name = "$JOB_NAME/serif/$job_batch_num";
        my $experiment_dir = "$master_serif_output_dir/$job_batch_num";
        my $batch_file = "$batch_file_directory/serif_batch_file_$job_batch_num";
        my $serif_cause_effect_patterns_dir = "$hume_repo_root/resource/serif_cause_effect_patterns";
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
                    [ "env PYTHONPATH=$NNEVENT_PYTHON_PATH $PYTHON3 $SERIF_SERVER_MODE_CLIENT_SCRIPT --file_list_path $batch_file --output_directory_path $experiment_dir --server_http_endpoint $serif_uri" ]
                );
            push(@serif_jobs, $serif_jobid);
        }
    }

    # convert factfinder results into json file that the
    # serialize stage will use
    if ((get_param($params, "serif_server_mode_endpoint", "None") eq "None") and ($mode eq "CauseEx")) {
        my $process_factfinder_results_job_name = "$JOB_NAME/serif/process_factfinder_results";
        my $process_factfinder_results_jobid =
            runjobs(
                \@serif_jobs, $process_factfinder_results_job_name,
                {
                    BATCH_QUEUE => $LINUX_QUEUE,
                },
                [ "$PYTHON2 $FACTFINDER_TO_JSON_SCRIPT $master_serif_output_dir $GENERATED_FACTFINDER_JSON_FILE" ]
            );
    }
    else {
        # @hqiu: Logic here is convoluted !!!
        make_output_dir($GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR);
    }
    # Compine results into one list
    my $list_results_job_name = "$JOB_NAME/list-serif-results";
    my $list_results_jobid =
        runjobs(
            \@serif_jobs, $list_results_job_name,
            {
                SCRIPT => 1
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$master_serif_output_dir/*/output/*.xml\" --output_list_path $GENERATED_SERIF_SERIFXML" ]
        );
}

dojobs();

######
# KBP
######
my $GENERATED_KBP_SERIFXML = $GENERATED_SERIF_SERIFXML;
if (exists $stages{"kbp"}) {
    print "KBP stage\n";
    $GENERATED_KBP_SERIFXML = "$processing_dir/kbp_serifxml.list";
    # Strip events
    my $input_serifxml_list =
        get_param($params, "kbp_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_SERIF_SERIFXML
            : get_param($params, "kbp_input_serifxml_list");

    my $strip_events_job_name = "$JOB_NAME/strip_events";
    my $stripped_events_serifxml_dir = "$processing_dir/stripped/output";
    my $stripped_events_serifxml_list = "$processing_dir/stripped_serifxml.list";
    my $strip_events_jobid =
        runjobs(
            [], $strip_events_job_name,
            {
                input_file_list  => $input_serifxml_list,
                output_dir       => $stripped_events_serifxml_dir,
                output_file_list => $stripped_events_serifxml_list,
                BATCH_QUEUE      => $LINUX_QUEUE,
            },
            [ "$STRIP_EVENTS_EXE", "strip_events.par" ]
        );
    dojobs();

    # Run KBP event finding in parallel
    my ($NUM_JOBS, $split_kbp_jobid) = split_file_for_processing("make_kbp_batch_files", $stripped_events_serifxml_list, "$batch_file_directory/kbp_batch_file_", $BATCH_SIZE);
    my $master_kbp_output_dir = make_output_dir("$processing_dir/kbp");
    my @kbp_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $kbp_output_dir = "$master_kbp_output_dir/$job_batch_num/output";
        my $kbp_output_serifxml_list = "$master_kbp_output_dir/$job_batch_num/serifxml.list";
        my $kbp_job_name = "$JOB_NAME/kbp/$job_batch_num";
        my $batch_file = "$batch_file_directory/kbp_batch_file_$job_batch_num";
        my $kbp_jobid =
            runjobs(
                [ $split_kbp_jobid ], $kbp_job_name,
                {
                    git_repo                   => $git_repo,
                    output_file_list           => $kbp_output_serifxml_list,
                    input_file_list            => $batch_file,
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
    my $list_results_job_name = "$JOB_NAME/list-kbp-results";
    my $list_results_jobid =
        runjobs(
            \@kbp_jobs, $list_results_job_name,
            {
                SCRIPT => 1,
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$master_kbp_output_dir/*/output/*.xml\" --output_list_path $GENERATED_KBP_SERIFXML" ]
        );
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

    my $output_serifxml_dir = "$processing_dir/generic_events_serifxml_out/";
    my $output_serifxml_list = "$processing_dir/generic_events_serifxml_out.list";
    my ($NUM_JOBS, $split_generic_events_jobid) = split_file_for_processing("make_generic_events_batch_files", $input_serifxml_list, "$batch_file_directory/generic_events_batch_file_", $BATCH_SIZE);
    $output_serifxml_dir = make_output_dir($output_serifxml_dir);
    my @generic_events_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/generic_events_batch_file_$job_batch_num";
        my $add_event_mentions_from_propositions_jobid =
            runjobs(
                [ $split_generic_events_jobid ], "$JOB_NAME/generic_events/add_event_mentions_from_propositions_$job_batch_num",
                {
                    JSERIF_ROOT          => $JSERIF_ROOT,
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

    my $list_results_job_name = "$JOB_NAME/list-generic-events-results";
    my $list_results_jobid =
        runjobs(
            \@generic_events_split_jobs, $list_results_job_name,
            {
                SCRIPT => 1,
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$output_serifxml_dir/*\" --output_list_path $output_serifxml_list" ]
        );
    $GENERATED_GENERIC_EVENTS_SERIFXML = $output_serifxml_list;
}

dojobs();


###################
# NN Event Typing 
###################
my $GENERATED_NN_EVENT_SERIFXML = $GENERATED_GENERIC_EVENTS_SERIFXML;

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
                jserif_root           => $JSERIF_ROOT,
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
    my $nn_events_model_list = get_param($params, "nn_events_model_list");

    my $input_serifxml_list =
        get_param($params, "nn_events_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_NN_EVENT_SERIFXML
            : get_param($params, "nn_events_input_serifxml_list");

    # Run NN event finding in parallel
    my ($NUM_JOBS, $split_nn_events_jobid) = split_file_for_processing("make_nn_events_batch_files", $input_serifxml_list, "$batch_file_directory/nn_events_batch_file_", $NN_EVENTS_BATCH_SIZE);
    my $master_nn_events_output_dir = make_output_dir("$processing_dir/nn_events");

    my @nn_add_events_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/nn_events_batch_file_$job_batch_num";

        my $nn_events_batch_dir = make_output_dir("$master_nn_events_output_dir/$job_batch_num");
        my $nn_events_batch_output = make_output_dir("$master_nn_events_output_dir/$job_batch_num/output");
        my $genericity_added_batch_output = make_output_dir("$master_nn_events_output_dir/$job_batch_num/genericity_output");
        my $nn_events_batch_output_list = "$batch_file_directory/nn_events_genericity_batch_file_$job_batch_num";
        my $nn_events_genericity_output_list = "$master_nn_events_output_dir/$job_batch_num/nn_events_genericity.list";

        make_output_dir($nn_events_batch_output);

        my $batch_predictions_file = "$nn_events_batch_dir/predictions.json";
        my $merge_nn_output_jobid;

        if (get_param($params, "nn_event_server_mode_endpoint", "None") eq "None") {
            my $add_prefix_to_serifxml_in_list =
                runjobs(
                    [ $split_nn_events_jobid ], "$JOB_NAME/nn_events/add_prefix_$job_batch_num",
                    {
                        BATCH_QUEUE      => $LINUX_QUEUE,
                        SGE_VIRTUAL_FREE => "4G",
                        SCRIPT           => 1,
                    },
                    [ "cat $batch_file | awk '{print \"SERIF:\"\$0}' > $batch_file\.with_type" ]
                );

            open my $handle, '<', $nn_events_model_list or die "Cannot open $nn_events_model_list: $!";;
            chomp(my @nn_models = <$handle>);
            close $handle;

            my @nn_events_jobs = ();
            my @nn_prediction_files = ();
            foreach my $nn_model (@nn_models) {
                my ($nn_model_name, $nn_model_path) = ($nn_model =~ m/([^\0\ \/]+)\ ([^\0]+)/);

                my $nn_events_batch_model_dir = "$nn_events_batch_dir/$nn_model_name";
                my $nn_events_batch_model_output_dir = "$nn_events_batch_model_dir/output";

                make_output_dir($nn_events_batch_model_dir);
                make_output_dir($nn_events_batch_model_output_dir);

                my $nn_events_job_name = "$JOB_NAME/nn_events/$job_batch_num" . "_" . $nn_model_name;
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
            my $batch_predictions_list = "$nn_events_batch_dir/predictions.list";

            open my $fh, '>', $batch_predictions_list or die "Cannot open $batch_predictions_list: $!";
            print $fh join("\n", @nn_prediction_files);
            close $fh;

            $merge_nn_output_jobid = runjobs(
                \@nn_events_jobs, "$JOB_NAME/nn_events/merge_nn_output_$job_batch_num",
                {
                    BATCH_QUEUE => $LINUX_QUEUE,
                },
                [ "$PYTHON2 $COMBINE_NN_EVENTS_JSON_SCRIPT $batch_predictions_list $batch_predictions_file" ]
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
            #					["env PYTHONPATH=$NNEVENT_PYTHON_PATH $PYTHON3 $NLPLINGO_SERVER_MODE_CLIENT_SCRIPT --file_list_path $batch_file --output_json_path $nn_events_batch_dir/predictions.json --server_http_endpoint $nn_event_uri"]
            #				);
            #				push(@nn_events_jobs, $nn_events_jobid);
        }


        # dojobs();

        # add decoded events from JSON to SerifXmls (as EventMentions)
        my $add_event_mentions_in_json_to_serifxmls_jobid =
            runjobs(
                [ $merge_nn_output_jobid ], "$JOB_NAME/nn_events/add_em_$job_batch_num",
                {
                    JSERIF_ROOT        => $JSERIF_ROOT,
                    inputFileJson      => $batch_predictions_file,
                    inputListSerifXmls => $batch_file,
                    outputDir          => $nn_events_batch_output,
                    BATCH_QUEUE        => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE   => "16G",
                    ATOMIC             => 1,
                },
                [ "sh", "add_event_mentions_in_json_to_serifxmls.sh" ]
            );
        push(@nn_add_events_jobs, $add_event_mentions_in_json_to_serifxmls_jobid);

        my $list_nn_batch_results_job_name = "$JOB_NAME/nn_events/list_results_$job_batch_num";
        my $list_nn_batch_results_jobid =
            runjobs(
                [ $add_event_mentions_in_json_to_serifxmls_jobid ], $list_nn_batch_results_job_name,
                {
                    SCRIPT => 1,
                },
                [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$nn_events_batch_output/*.serifxml\" --output_list_path $nn_events_batch_output_list" ]
            );
        push(@nn_add_events_jobs, $list_nn_batch_results_jobid);

        if (exists $stages{"kbp"}) {
            # run genericity classifier
            my $nn_event_genericity_job_name = "$JOB_NAME/nn_events/genericity_$job_batch_num";
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
    my $list_results_job_name = "$JOB_NAME/list-nn-events-results";
    if (exists $stages{"kbp"}) {
        my $list_results_jobid =
            runjobs(
                \@nn_add_events_jobs, $list_results_job_name,
                {
                    SCRIPT => 1
                },
                [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$master_nn_events_output_dir/*/genericity_output/*.serifxml\" --output_list_path $GENERATED_NN_EVENTS_SERIFXML" ]
            );
    }
    else {
        my $list_results_jobid =
            runjobs(
                \@nn_add_events_jobs, $list_results_job_name,
                {
                    SCRIPT => 1
                },
                [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$master_nn_events_output_dir/*/output/*.serifxml\" --output_list_path $GENERATED_NN_EVENTS_SERIFXML" ]
            );
    }
}

dojobs();

###################
# Probabilistic grounding
###################

my $GENERATED_GROUNDING_SERIFXML = $GENERATED_NN_EVENTS_SERIFXML;
if (exists $stages{"probabilistic-grounding"}) {
    print "Probabilistic Grounding stage\n";
    my $GENERATED_GROUNDING_DIR = "$processing_dir/probabilistic-grounding";
    $GENERATED_GROUNDING_SERIFXML = "$processing_dir/grounded_serifxml.list";
    my $input_serifxml_list =
        get_param($params, "grounding_input") eq "GENERATED"
            ? $GENERATED_NN_EVENTS_SERIFXML
            : get_param($params, "grounding_input");

    my ($NUM_JOBS, $split_probabilistic_grounding_jobid) = split_file_for_processing("make_probabilistic_grounding_batch_files", $input_serifxml_list, "$batch_file_directory/probabilistic_grounding_batch_file_", $BATCH_SIZE);
    my $master_probabilistic_grounding_output_dir = make_output_dir($GENERATED_GROUNDING_DIR);
    my @probabilistic_grounding_split_jobs = ();

    my $event_ontology = "$internal_ontology_dir/event_ontology.yaml";
    my $exemplars = "$internal_ontology_dir/data_example_events.json";
    my $embeddings = "$external_dependencies_root/common/glove.6B.50d.p";
    my $lemmas = "$external_dependencies_root/common/lemma.nv";
    my $stopwords = "$internal_ontology_dir/stopwords.list";
    my $threshold = "0.7";
    my $which_ontology = "";
    if ($mode eq "CauseEx") {
        $which_ontology = "CAUSEEX";
    }
    else {
        $which_ontology = "HUME";
    }

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/probabilistic_grounding_batch_file_$job_batch_num";
        my $GENERATED_GROUNDING_CACHE = "$GENERATED_GROUNDING_DIR/$job_batch_num.json";
        # 1. run grounder over input to produce cache
        my $grounding_generation_jobid =
            runjobs(
                [ $split_probabilistic_grounding_jobid ],
                "$JOB_NAME/probabilistic_grounding/generate_cache_$job_batch_num",
                {
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE => "32G"
                },
                [ "$PYTHON2 $PROB_GROUNDING_SCRIPT "
                    . "--event_ontology $event_ontology "
                    . "--exemplars $exemplars "
                    . "--embeddings $embeddings "
                    . "--lemmas $lemmas "
                    . "--stopwords $stopwords "
                    . "--threshold $threshold "
                    . "--which_ontology $which_ontology "
                    . "--serifxmls $batch_file "
                    . "--output $GENERATED_GROUNDING_CACHE" ]
            );

        # 2. inject groundings into new serifxmls
        my $grounding_injection_jobid =
            runjobs(
                [ $grounding_generation_jobid ],
                "$JOB_NAME/probabilistic_grounding/add_grounded_types_from_cache_$job_batch_num",
                {
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    SGE_VIRTUAL_FREE => "32G"
                },
                [ "$PROB_GROUNDING_INJECTION_EXE "
                    . "$GENERATED_GROUNDING_CACHE "
                    . "$batch_file "
                    . "$GENERATED_GROUNDING_DIR" ]
            );
        push(@probabilistic_grounding_split_jobs, $grounding_injection_jobid);
    }

    # 3. save new serifxmls as filelist
    my $list_grounding_results_jobid =
        runjobs(
            \@probabilistic_grounding_split_jobs,
            "$JOB_NAME/list_grounding_serifxml",
            {
                SCRIPT => 1,
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$GENERATED_GROUNDING_DIR/*.xml\" --output_list_path $GENERATED_GROUNDING_SERIFXML" ]
        );

}

dojobs();

######################
# Event consolidation
######################
my $GENERATED_EVENT_CONSOLIDATION_SERIFXML = $GENERATED_GROUNDING_SERIFXML;
if (exists $stages{"event-consolidation"}) {
    print "Event consolidation stage\n";

    my $input_serifxml_list =
        get_param($params, "event_consolidation_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_EVENT_CONSOLIDATION_SERIFXML
            : get_param($params, "event_consolidation_input_serifxml_list");

    my $compatibleEventFile = "$hume_repo_root/resource/event_consolidation/causeex/compatible_events.txt";
    my $argumentRoleEntityTypeFile = "$hume_repo_root/resource/event_consolidation/causeex/event_role.entity_type.constraints";
    my $lemmaFile = "$external_dependencies_root/common/lemma.nv";
    my $keywordFile = "";
    my $blacklistFile = "";
    my $kbpEventMappingFile = "";
    if ($mode eq "CauseEx") {
        $keywordFile = "$hume_repo_root/resource/event_consolidation/causeex/event_type.keywords";
        $blacklistFile = "$hume_repo_root/resource/event_consolidation/causeex/event_type.blacklist";
        $kbpEventMappingFile = "$hume_repo_root/resource/event_consolidation/causeex/KBP_events.json";
    }
    else {
        $keywordFile = "$hume_repo_root/resource/event_consolidation/wm/event_type.keywords";
        $blacklistFile = "$hume_repo_root/resource/event_consolidation/wm/event_type.blacklist";
        $kbpEventMappingFile = "$hume_repo_root/resource/event_consolidation/wm/KBP_events.json";
    }

    my $input_metadata_file = get_param($params, "event_consolidation_input_metadata_file");
    my $eventOntologyYAMLFilePath = "$internal_ontology_dir/event_ontology.yaml";
    my $copyArgumentSentenceWindow = get_param($params, "copyArgumentSentenceWindow");

    my $output_serifxml_dir = "$processing_dir/event_consolidation_serifxml_out/";
    my $output_serifxml_list = "$processing_dir/event_consolidation_serifxml_out.list";

    my ($NUM_JOBS, $split_event_consolidation_jobid) = split_file_for_processing("make_event_consolidation_batch_files", $input_serifxml_list, "$batch_file_directory/event_consolidation_batch_file_", $BATCH_SIZE);
    $output_serifxml_dir = make_output_dir($output_serifxml_dir);
    my @event_consolidation_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/event_consolidation_batch_file_$job_batch_num";
        my $event_consolidation_jobid = runjobs(
            [ $split_event_consolidation_jobid ], "$JOB_NAME/event_consolidation/run_event_consolidation_$job_batch_num",
            {
                JSERIF_ROOT                => $JSERIF_ROOT,
                strListSerifXmlFiles       => $batch_file,
                strOutputDir               => $output_serifxml_dir,
                strInputMetadataFile       => $input_metadata_file,
                compatibleEventFile        => $compatibleEventFile,
                ontologyFile               => $eventOntologyYAMLFilePath,
                argumentRoleEntityTypeFile => $argumentRoleEntityTypeFile,
                mode                       => $mode,
                keywordFile                => $keywordFile,
                blacklistFile              => $blacklistFile,
                lemmaFile                  => $lemmaFile,
                copyArgumentSentenceWindow => $copyArgumentSentenceWindow,
                BATCH_QUEUE                => $LINUX_QUEUE,
                SGE_VIRTUAL_FREE           => "32G",
                wordnetDir                 => "$SERIF_DATA/english/Software/WN16/DICT",
                sieveResourceDir           => "$dependencies_root/event_consolidation/sieve",
                geonamesFile               => "$dependencies_root/event_consolidation/geoNames.db",
                polarityFile               => "$hume_repo_root/resource/event_consolidation/common/polarity_modifiers.txt",
                kbpEventMappingFile        => $kbpEventMappingFile,
                accentEventMappingFile     => "$hume_repo_root/resource/event_consolidation/accent_event_mapping.json",
                accentCodeToEventTypeFile  => "$hume_repo_root/resource/event_consolidation/cameo_code_to_event_type.txt"
            },
            [ "sh", "run_event_consolidation.sh" ]
        );
        push(@event_consolidation_split_jobs, $event_consolidation_jobid)
    }

    my $generate_event_consolidation_serifxml_list_jobid =
        runjobs(
            \@event_consolidation_split_jobs, "$JOB_NAME/event_consolidation/list-event-consolidation-results",
            {
                SCRIPT => 1
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$output_serifxml_dir/*\" --output_list_path $output_serifxml_list" ]
        );
    $GENERATED_EVENT_CONSOLIDATION_SERIFXML = $output_serifxml_list;
}

dojobs();

#################################
# Event timeline
#################################

if (exists $stages{"event-timeline"}){
    my $event_timeline_input_serifxml_list = get_param($params,"event_timeline_input_serifxml_list") eq "GENERATED"?$GENERATED_EVENT_CONSOLIDATION_SERIFXML:get_param($params,"event_timeline_input_serifxml_list");
    my $output_event_timeline_dir = make_output_dir("$processing_dir/event_timeline_output");
    my $extract_event_timestamp_info_jobid = runjobs(
        [],"$JOB_NAME/event_timeline/1_extract_event_timestamp",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "32G"
        },
        ["$EXTRACT_TIMELINE_FROM_SERIFXML_EXE $event_timeline_input_serifxml_list $output_event_timeline_dir/event_timeline.ljson"]
    );
    my $group_eventmention_in_timeline_bucket = runjobs(
        [$extract_event_timestamp_info_jobid],"$JOB_NAME/event_timeline/2_group_into_bucket",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "2G"
        },
        ["$PYTHON3 $GROUP_EVENTMENTION_IN_TIMELINE_BUCKET_SCRIPT $output_event_timeline_dir/event_timeline.ljson > $output_event_timeline_dir/event_timeline.table"]
    );
}

dojobs();

########################
# Event-Event Relations
########################
my $GENERATED_LEARNIT_TRIPLE_FILE = "$processing_dir/event_event_relations/relation_and_event_pairs_freq.txt";
my $GENERATED_LEARNIT_EVENT_COUNT_FILE = "$processing_dir/event_event_relations/event_triggers_in_causal_relations.txt";
my $GENERATED_EVENT_EVENT_RELATION_SERIFXML = $GENERATED_EVENT_CONSOLIDATION_SERIFXML;

if (exists $stages{"event-event-relations"}) {
    print "Event-Event relations stage\n";
    $GENERATED_EVENT_EVENT_RELATION_SERIFXML = "$processing_dir/event_event_relations_serifxml.list";
    my $input_serifxml_list =
        get_param($params, "eer_input_serifxml_list") eq "GENERATED"
            ? (exists $stages{"event-consolidation"}
            ? $GENERATED_EVENT_CONSOLIDATION_SERIFXML
            : $GENERATED_GROUNDING_SERIFXML)
            : get_param($params, "eer_input_serifxml_list");

    my $input_serif_cause_effect_json_dir =
        get_param($params, "eer_input_serif_cause_effect_relations_dir") eq "GENERATED"
            ? $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR
            : get_param($params, "eer_input_serif_cause_effect_relations_dir");

    # resources for filtering bad triples
    # @hqiu. We should remove this to only run regular learnit
    my $MIN_FREQ_EVENT_PAIRS = get_param($params, "learnit_min_freq_event_pairs");

    my $stage_processing_dir = $processing_dir . "/event_event_relations/";

    # use high-prec prop patterns; do not use whilte list of relational triples
    run_learnit_and_nre_extractors($stage_processing_dir, $input_serifxml_list, $batch_file_directory, "all", $MIN_FREQ_EVENT_PAIRS, "na", "na");
    dojobs();

    # generate triple file
    my $generate_triple_file_job_name = "$JOB_NAME/event_event_relations/generate_triple_file";
    my $generate_triple_file_jobid =
        runjobs(
            [], $generate_triple_file_job_name,
            {
                expt_dir    => $stage_processing_dir,
                triple_file => $GENERATED_LEARNIT_TRIPLE_FILE,
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "sh", "generate_triple_file.sh" ]
        );

    dojobs();

    my $learnit_relations_file = "$stage_processing_dir/learnit_event_event_relations_file.json";
    my $nre_relations_file = "$stage_processing_dir/nre_event_event_relations_file.json";

    # generate event count file
    my $generate_event_count_file_job_name = "$JOB_NAME/event_event_relations/generate_event_count_file";
    my $generate_event_count_file_jobid =
        runjobs(
            [], $generate_event_count_file_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $EVENT_COUNT_SCRIPT $learnit_relations_file $GENERATED_LEARNIT_EVENT_COUNT_FILE" ],
        );
    dojobs();

    # Add causal relations to serifxml


    my $input_json_list = "$input_serif_cause_effect_json_dir,$learnit_relations_file,$nre_relations_file";

    my ($NUM_JOBS, $split_create_event_event_relations_jobid) = split_file_for_processing("make_create_event_event_relations_batch_files", $input_serifxml_list, "$batch_file_directory/create_event_event_relations_batch_file_", $BATCH_SIZE);

    my @create_event_event_relations_split_jobs = ();
    my $uncalibrated_eer_processing_dir = make_output_dir("$stage_processing_dir/uncalibrated_serif_folder");

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/create_event_event_relations_batch_file_$job_batch_num";

        my $create_event_event_relations_jobid =
            runjobs(
                [ $split_create_event_event_relations_jobid ], "$JOB_NAME/event_event_relations/add_causal_relations_$job_batch_num",
                {
                    input_serifxml_list       => $batch_file,
                    output_serifxml_directory => $uncalibrated_eer_processing_dir,
                    input_json_list           => $input_json_list,
                    BATCH_QUEUE               => $LINUX_QUEUE,
                },
                [ "$EVENT_EVENT_RELATION_EXE", "event_event_relations.par" ],
            );

        push(@create_event_event_relations_split_jobs, $create_event_event_relations_jobid);
    }
    my $uncalibrated_eer_serif_list = "$stage_processing_dir/uncalibrated_serif.list";
    my $output_event_event_relations_dir = make_output_dir("$stage_processing_dir/serifxml_output");
    my $list_uncalibrate_eer_serif_jobid =
        runjobs(
            \@create_event_event_relations_split_jobs, "$JOB_NAME/event_event_relations/list_uncalibrate_serifxml",
            {
                SCRIPT => 1
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$uncalibrated_eer_processing_dir/*.xml\" --output_list_path $uncalibrated_eer_serif_list" ]
        );
    my $calibrate_eer_score_jobid = runjobs(
        [ $list_uncalibrate_eer_serif_jobid ], "$JOB_NAME/event_event_relations/calibrate_causal_relations",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "32G",
        },
        [ "$EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE $uncalibrated_eer_serif_list $output_event_event_relations_dir" ]
    );

    my $list_eer_results_job_name = "$JOB_NAME/event_event_relations/list_eer_serifxml";
    my $list_eer_results_jobid =
        runjobs(
            [ $calibrate_eer_score_jobid ], $list_eer_results_job_name,
            {
                SCRIPT => 1
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$output_event_event_relations_dir/*.xml\" --output_list_path $GENERATED_EVENT_EVENT_RELATION_SERIFXML" ]
        );

    dojobs();
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

    my $learnit_relation_triple_file =
        get_param($params, "serialization_input_learnit_triple_file") eq "GENERATED"
            ? $GENERATED_LEARNIT_TRIPLE_FILE
            : get_param($params, "serialization_input_learnit_triple_file");

    my $learnit_event_head_count_file =
        get_param($params, "serialization_input_learnit_event_count_file") eq "GENERATED"
            ? $GENERATED_LEARNIT_EVENT_COUNT_FILE
            : get_param($params, "serialization_input_learnit_event_count_file");

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

    # KBConstructor call 2 -- use grounding cache and serialize
    my $serifxml_dir = "$processing_dir/final_serifxml";
    my $copy_serifxml_jobname = "$JOB_NAME/serialize/copy_final_serifxml";
    my $copy_serifxml_jobid =
        runjobs(
            [], $copy_serifxml_jobname,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $COPY_FILES_SCRIPT $input_serifxml_list $serifxml_dir \"$metadata_file\"" ]
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
                    learnit_relation_triple_file                    => $learnit_relation_triple_file,
                    learnit_event_head_count_file                   => $learnit_event_head_count_file,
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
                    bbn_namespace                                   => $bbn_namespace,
                    mode                                            => $mode,
                    seed_milestone                                  => "m17",
                    seed_type                                       => $document_type,
                    seed_version                                    => "v1",
                    SGE_VIRTUAL_FREE                                => $mem,
                    BATCH_QUEUE                                     => $batch_queue,
                    ua_geoid_txt_file_path                          => "$external_dependencies_root/wm/geo_dict_with_population_SOUTH_SUDAN.txt",
                    ontology_turtle_folder                          => "$hume_repo_root/resource/ontologies/causeex/190206"
                },
                [ "$PYTHON2 $KB_CONSTRUCTOR_SCRIPT", $template_filename ]
            );
    }
}

dojobs();

##################
# CauseEx Release 
##################

# Creates directory for release, currently only unstructured data
if (exists $stages{"causeex-release"}) {
    print "CauseEx release stage\n";

    my $serialization_dir =
        get_param($params, "causeex_release_serialization_dir") eq "GENERATED"
            ? $GENERATED_SERIALIZATION_DIR
            : get_param($params, "causeex_release_serialization_dir");

    my $release_dir = get_param($params, "causeex_release_dir");
    my $all_directory = make_output_dir("$release_dir/all");
    opendir(my $dh, $serialization_dir);
    my @document_types = grep {-d "$serialization_dir/$_" && !/^\.{1,2}$/} readdir($dh);

    my @release_jobs = ();
    foreach my $document_type (@document_types) {
        my $document_type_dir = "$serialization_dir/$document_type";
        my $causeex_release_job_name = "$JOB_NAME/causeex_release/$document_type";
        my $causeex_release_job_id =
            runjobs(
                [], $causeex_release_job_name,
                {
                    BATCH_QUEUE => $LINUX_QUEUE,
                },
                [ "$PYTHON2 $CAUSEEX_RELEASE_SCRIPT $document_type_dir $release_dir" ],
                [ "cp $release_dir/$document_type/*.nt $all_directory" ]
            );
        push @release_jobs, $causeex_release_job_id;
    }

}

dojobs();

sub run_learnit_and_nre_extractors {
    my $processing_dir = $_[0];
    my $input_serifxml_list = $_[1];
    my $batch_file_directory = $_[2];
    my $useOnlyPropPatterns = $_[3];
    my $MIN_FREQ_EVENT_PAIRS = $_[4];
    my $USE_TRIPLE_WHITE_LIST = $_[5];
    my $str_file_triple_relation_event_pairs = $_[6];

    my $learnit_relations_file = "$processing_dir/learnit_event_event_relations_file.json";
    my $nre_relations_file = "$processing_dir/nre_event_event_relations_file.json";
    my $extractor_target = get_param($params, "extractor_target", "binary_event_event");
    my ($NUM_JOBS, $split_learnit_jobid) = split_file_for_processing("make_run_learnit_batch_files", $input_serifxml_list, "$batch_file_directory/learnit_serif_batch_file_", $BATCH_SIZE);
    my $master_learnit_output_dir = make_output_dir("$processing_dir/");
    my $mappings_output_dir = make_output_dir("$master_learnit_output_dir/mappings");
    my $decoding_output_dir = make_output_dir("$master_learnit_output_dir/decoding");
    my $source_lists_dir = make_output_dir("$master_learnit_output_dir/source_lists");

    my $learnit_pattern_dir = get_param($params, "learnit_pattern_dir") eq "DEFAULT"
        ? "$hume_repo_root/resource/learnit_patterns"
        : get_param("learnit_input_pattern_dir");

    # copy $input_serifxml_list to source_lists_dir
    my $copy_serif_lists =
        runjobs([ $split_learnit_jobid ], "$JOB_NAME/event_event_relations/copy_serif_lists",
            { SCRIPT => 1 },
            [ "cp $input_serifxml_list $source_lists_dir" ]
        );
    my @learnit_decoding_jobs = ();
    my @nre_decoding_jobs = ();
    my @mappings_output_files = ();
    # Trick runjobs into expanding Serif parameter file
    my $expand_learnit_template_job_id =
        runjobs([ $copy_serif_lists ], "$JOB_NAME/event_event_relations/expand_template",
            {
                learnit_root => $learnit_root,
                source_lists => $source_lists_dir,
                SERIF_DATA   => $SERIF_DATA,
                BATCH_QUEUE  => $LINUX_QUEUE,
                SCRIPT       => 1,
            },
            [ "$PYTHON2 -c pass", "learnit.par" ]
        );
    dojobs();
    my $learnit_params = "$exp_root/etemplates/$JOB_NAME/event_event_relations/$exp-expand_template.learnit.par";
    #print $learnit_params;
    #texit 1;
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $learnit_job_name = "$JOB_NAME/event_event_relations/mappings/$job_batch_num";
        my $input_batch_file = "$batch_file_directory/learnit_serif_batch_file_$job_batch_num";
        my $mappings_output_file = "$mappings_output_dir/$job_batch_num.sjson";
        # mappings creation
        my $learnit_mappings_jobid =
            runjobs(
                [ $expand_learnit_template_job_id ], $learnit_job_name,
                {
                    SGE_VIRTUAL_FREE => "25G",
                    BATCH_QUEUE      => $LINUX_QUEUE,
                },
                [ "$LEARNIT_INSTANCE_EXTRACTOR_EXE $learnit_params $extractor_target $input_batch_file $mappings_output_file" ]
            );
        # LearnIt decoding
        $learnit_job_name = "$JOB_NAME/event_event_relations/decoding/$job_batch_num";
        my $decoding_output_file = "$decoding_output_dir/$job_batch_num.json";
        my $decoding_log_file = "$decoding_output_dir/$job_batch_num.log";

        my $learnit_decoding_jobid =
            runjobs(
                [ $learnit_mappings_jobid ], $learnit_job_name,
                {
                    SGE_VIRTUAL_FREE => "25G",
                    BATCH_QUEUE      => $LINUX_QUEUE,
                },
                [ "$LEARNIT_DECODER_SCRIPT $learnit_params $mappings_output_file $learnit_root $decoding_output_file $useOnlyPropPatterns $MIN_FREQ_EVENT_PAIRS $USE_TRIPLE_WHITE_LIST $str_file_triple_relation_event_pairs $learnit_pattern_dir $decoding_log_file" ]
            );
        # Apply NRE models
        $learnit_job_name = "$JOB_NAME/event_event_relations/nre/$job_batch_num";
        my $nreOutputPrefix = $mappings_output_file . ".NRE/";
        my $neural_relation_decoding_jobid =
            runjobs(
                [ $learnit_mappings_jobid ], $learnit_job_name,
                {
                    SGE_VIRTUAL_FREE => "25G",
                    BATCH_QUEUE      => $LINUX_QUEUE,
                    job_retries      => 1,
                    ATOMIC           => 1,
                },
                [ "$NEURAL_RELATION_DECODER_SCRIPT $learnit_params $mappings_output_file $nreOutputPrefix $learnit_root $deepinsight_root $nre_model_root $ANACONDA_ROOT py2-tf1" ]
            );

        push(@learnit_decoding_jobs, $learnit_decoding_jobid);
        push(@nre_decoding_jobs, $neural_relation_decoding_jobid);
        push(@mappings_output_files, $mappings_output_file);
    }

    # Combine decoding results into one json file.
    my $combine_results_job_name = "$JOB_NAME/event_event_relations/combine_learnit_decoding_results";
    my $combine_results_jobid =
        runjobs(
            \@learnit_decoding_jobs, $combine_results_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $LEARNIT_JSON_AGGREGATOR_SCRIPT $decoding_output_dir $learnit_relations_file" ]
        );

    # Combine NRE decoding results into one json file.
    my $list_nre_dir = $mappings_output_dir . "/list_nre_dir";
    my $list_nre_job_name = "$JOB_NAME/event_event_relations/list_nre_json";
    my $list_nre_dir_jobid =
        runjobs(
            \@nre_decoding_jobs, $list_nre_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
                SCRIPT      => 1
            },
            [ "$CREATE_FILE_LIST_SCRIPT --unix_style_pathname \"$mappings_output_dir/*.NRE\" --output_list_path $list_nre_dir" ]
        );

    my $combine_nre_results_job_name = "$JOB_NAME/event_event_relations/combine_nre_decoding_results";
    my $combine_nre_results_jobid =
        runjobs(
            [ $list_nre_dir_jobid ], $combine_nre_results_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $NRE_JSON_AGGREGATOR_SCRIPT $list_nre_dir $nre_relations_file.aggr" ]
        );

    my $nre_postprocessing_job_name = "$JOB_NAME/event_event_relations/nre_postprocessing";
    my $nre_postprocessing_job_id =
        runjobs(
            [ $combine_nre_results_jobid ], $nre_postprocessing_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $NRE_POSTPROCESSING $nre_relations_file.aggr $nre_relations_file.filtered" ]
        );

    my $nre_rescale_freq_job_name = "$JOB_NAME/event_event_relations/nre_rescale_freq";
    my $nre_rescale_freq_job_id =
        runjobs(
            [ $nre_postprocessing_job_id ], $nre_rescale_freq_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $NRE_RESCALE_FREQ $nre_relations_file.filtered $nre_relations_file.rescaled" ]
        );

    my $nre_strip_low_conf_job_name = "$JOB_NAME/event_event_relations/nre_strip_low_conf";
    my $nre_strip_low_conf_job_id =
        runjobs(
            [ $nre_rescale_freq_job_id ], $nre_strip_low_conf_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $NRE_STRIP_LOW_CONF $nre_relations_file.rescaled $nre_relations_file" ]
        );

    # Run scorer on decoding results.
    my $learnit_scoring_job_name = "$JOB_NAME/event_event_relations/learnit-scoring";
    my $learnit_scoring_jobid =
        runjobs(
            \@learnit_decoding_jobs, $learnit_scoring_job_name,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON2 $LEARNIT_SCORER_SCRIPT $decoding_output_dir $decoding_output_dir/event_event_relations.decoder.score" ]
        );

    # make copies of causal json and decoder output directory
    my $copy_decoder_output_path = "$master_learnit_output_dir/decoding_copy";
    my $copy_learnit_decoder_output =
        runjobs([ $learnit_scoring_jobid ], "$JOB_NAME/event_event_relations/copy_decoder_output",
            { SCRIPT => 1 },
            [ "cp -r $decoding_output_dir $copy_decoder_output_path" ]
        );
    dojobs();

    # create a mappings list file
    my $mappings_file_list = "$master_learnit_output_dir/mappings_list_file";
    open my $fh, '>', $mappings_file_list or die "Cannot open $mappings_file_list: $!";
    print $fh join("\n", @mappings_output_files);
    close $fh;

    return($learnit_params, $mappings_file_list);
}


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
    my $jobid = runjobs([], "$JOB_NAME/$split_jobname",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SCRIPT      => 1,
        },
        "/usr/bin/split -d -a 5 -l $bs $bf $bp");

    return($njobs, $jobid);
}

sub check_requirements {
    my $rv = 1;
    my @required_git_repos = ();
    if (exists $stages{"kbp"}) {
        push(@required_git_repos, "$git_repo/kbp");
    }
    if (exists $stages{"event-event-relations"}) {
        push(@required_git_repos, "$git_repo/learnit");
        push(@required_git_repos, "$git_repo/deepinsight");
    }
    push(@required_git_repos, "$git_repo/jserif");

    for my $git_repo (@required_git_repos) {
        if (!-e $git_repo) {
            print "You must have the git repo: " . $git_repo . " cloned\n";
            $rv = 0;
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
        push(@required_git_files, "$git_repo/jserif/serif-util/target/appassembler/bin/NeuralNamesModelInputOutputMapper");
    }
    if (exists $stages{"kbp"}) {
        push(@required_git_files, "$STRIP_EVENTS_EXE");
        push(@required_git_files, "$KBP_EVENT_FINDER_EXE");
    }

    if (exists $stages{"nn-events"}) {

    }
    if (exists $stages{"event-event-relations"}) {
        push(@required_git_files, "$git_repo/learnit/neolearnit/target/appassembler/bin/InstanceExtractor");
        push(@required_git_files, "$git_repo/learnit/neolearnit/target/appassembler/bin/EventEventRelationPatternDecoder");
        push(@required_git_files, "$EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE");
    }

    for my $git_file (@required_git_files) {
        if (!-e $git_file) {
            print "You must have the file: " . $git_file . " . You may need to mvn install a git repo\n";
            $rv = 0;
        }
    }

    if (!defined $ENV{'SVN_PROJECT_ROOT'}) {
        print "You must set the environment variable SVN_PROJECT_ROOT in .bashrc to a Projects directory in an svn checkout\n";
        return 0;
    }

    my @required_svn_files = (
        $ENV{'SVN_PROJECT_ROOT'} . "/SERIF/python/serifxml.py",
        $ENV{'SVN_PROJECT_ROOT'} . "/SERIF/par"
    );
    if ($mode eq "CauseEx") {
        push(@required_svn_files, "$ENV{'SVN_PROJECT_ROOT'}/W-ICEWS/lib");
    }
    for my $svn_file (@required_svn_files) {
        if (!-e $svn_file) {
            print "You must have $svn_file checked out from svn\n";
            $rv = 0;
        }
    }

    return $rv;

}

sub get_current_time {
    my ($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
    my $nice_timestamp = sprintf("%04d%02d%02d-%02d%02d%02d",
        $year + 1900, $mon + 1, $mday, $hour, $min, $sec);
    return $nice_timestamp;
}
