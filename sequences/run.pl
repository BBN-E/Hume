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
my $learnit_root;
my $nlplingo_root;

my $jserif_event_jar;
BEGIN{
    $textopen_root = "/d4m/nlp/releases/text-open/R2020_08_21";
    $hume_repo_root = "/d4m/nlp/releases/Hume/R2020_09_29_3";
    # $hume_repo_root = Cwd::abs_path(__FILE__ . "/../..");
    $learnit_root = "/d4m/nlp/releases/learnit/R2020_08_28";
    $nlplingo_root = "/d4m/nlp/releases/nlplingo/R2020_08_23";
    $jserif_event_jar = "/d4m/nlp/releases/jserif/serif-event/serif-events-8.10.3-SNAPSHOT-pg.jar"; # For kbp
    unshift(@INC, "/d4m/ears/releases/runjobs4/R2019_03_29/lib");
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
    unshift(@INC, "$learnit_root/lib/perl_lib/");
}

use runjobs4;
use Utils;
use LearnItDecoding;

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

my $LINUX_QUEUE = get_param($params, "cpu_queue", "nongale-sl6");
#my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-sl69-non-k10s");
my $SINGULARITY_GPU_QUEUE = get_param($params, "singularity_gpu_queue", "allGPUs-sl610");

my $dependencies_root = "$hume_repo_root/resource/dependencies";
my $external_dependencies_root = "/nfs/raid87/u10/shared/Hume";
my $unmanaged_external_dependencies_root = "/nfs/raid87/u11/users/hqiu/external_dependencies_unmanaged";

my $learnit_jar_path = "$learnit_root/neolearnit/target/neolearnit-2.0-SNAPSHOT-jar-with-dependencies.jar";
my $hume_serif_util_jar_path = "$hume_repo_root/src/java/serif-util/target/causeex-serif-util-1.0.0-jar-with-dependencies.jar";
# Location of all the output of this sequence
(my $processing_dir, undef) = Utils::make_output_dir("$exp_root/expts/$JOB_NAME", "$JOB_NAME/mkdir_job_directory", []);

# Make copy of config file for debugging purposes
# copy($config_file, $processing_dir . "/" . get_current_time() . "-" . basename($config_file));

# Python commands
my $PYTHON3 = "/opt/Python-3.5.2-x86_64/bin/python3.5 -u";
my $ANACONDA_ROOT = "";
if (get_param($params, "ANACONDA_ROOT", "None") eq "None") {
    $ANACONDA_ROOT = "/nfs/raid87/u11/users/hqiu/miniconda_prod";
}
else {
    $ANACONDA_ROOT = get_param($params, "ANACONDA_ROOT");
}

my $CONDA_ENV_NAME_FOR_DOC_RESOLVER = "py3-jni";
my $CONDA_ENV_NAME_FOR_BERT_CPU = "py3-jni";
my $CONDA_ENV_NAME_FOR_BERT_GPU = "p3-bert-gpu";
my $CONDA_ENV_NAME_FOR_NN_EVENT_TYPING = "python-tf0.11-cpu";

my $ANACONDA_PY2_ROOT_FOR_NN_EVENT_TYPING = "$unmanaged_external_dependencies_root/nn_event_typing/anaconda2";


# Scripts
my $CONVERT_CDR_TO_HUME_CORPUS = "$hume_repo_root/src/python/data_digestion/cdr_converter.py";
my $CREATE_FILELIST_PY_PATH = "$textopen_root/src/python/util/common/create_filelist_with_batch_size.py";
my $COPY_FILES_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/copy_serifxml_by_document_type.py";
my $KB_CONSTRUCTOR_SCRIPT = "$hume_repo_root/src/python/knowledge_base/kb_constructor.py";
my $COMBINE_NN_EVENTS_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/merge_event_mentions_in_json.py";
my $LEARNIT_JSON_AGGREGATOR_SCRIPT = "$learnit_root/scripts/decoder_list_of_json_output_aggregator.py";
my $NNEVENT_DECODE_SCRIPT = "$nlplingo_root/nlplingo/tasks/train_test.py";
my $FACTFINDER_TO_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/factfinder_output_to_json.py";
my $EVENT_COUNT_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/count_triggers_in_causal_relations.py";
my $VALIDATE_JSON_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/validate_json.py";
my $PROB_GROUNDING_SCRIPT = "$hume_repo_root/src/python/misc/ground_serifxml.py";
my $ADD_BERT_TO_FILELIST_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/add_bert_to_filelist.py";
##my $NN_MAPPING_SCRIPT = "$hume_repo_root/src/python/misc/map_nn_output.py";
my $CREATE_FILE_LIST_SCRIPT = "$PYTHON3 $hume_repo_root/src/python/pipeline/scripts/create_filelist.py";
my $PREPARE_SERIF_EMBEDDING_FILELIST_SCRIPT = "$hume_repo_root/src/python/pipeline/scripts/prepare_serif_embedding_filelist.py";

my $NEURAL_RELATION_DECODER_SCRIPT_LDC = "$hume_repo_root/scripts/run_EventEventRelationNeuralDecoder_ldc.sh";
my $NEURAL_RELATION_DECODER_SCRIPT_OLD = "$hume_repo_root/scripts/run_EventEventRelationNeuralDecoder_old.sh";

my $nre_model_root = "$external_dependencies_root/common/event_event_relation/models/042219";
my $ldc_model_root = "$external_dependencies_root/common/event_event_relation/models/ckpt_train_ldc-unified_E82_E70_E61_E48_20191206_07_39_27";


# my $SINGULARITY_WRAPPER = "$hume_repo_root/scripts/run-in-singularity-container.sh";

my $SERIF_SERVER_MODE_CLIENT_SCRIPT = "$hume_repo_root/experiments/service_mode/serif_client.py";
my $NLPLINGO_SERVER_MODE_CLIENT_SCRIPT = "$hume_repo_root/experiments/service_mode/nlplingo_client.py";
my $GROUP_EVENTMENTION_IN_TIMELINE_BUCKET_SCRIPT = "$hume_repo_root/src/python/util/group_event_mention_in_timeline_bucket.py";


# Exes
my $BASH = "/bin/bash";
my $SERIF_EXE = "$hume_repo_root/bin/Serif";

my $KBP_EVENT_FINDER_EXE = "java -cp $jserif_event_jar com.bbn.serif.events.EventFinderBin";
my $LEARNIT_INSTANCE_EXTRACTOR_EXE = "java -cp $learnit_jar_path com.bbn.akbc.neolearnit.exec.InstanceExtractor";
my $STRIP_EVENTS_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.StripEvents2";
my $EVENT_EVENT_RELATION_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.EventEventRelationCreator";
my $EVENT_EVENT_RELATION_SCORE_CALIBRATE_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.CalibrateConfidences";
my $EXTRACT_TIMELINE_FROM_SERIFXML_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.DumpEventMentionForEventTimeline";
my $ADD_EVENT_MENTION_BY_POS_TAGS_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.AddEventMentionByPOSTags";
my $ADD_EVENT_MENTION_FROM_JSON_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.AddEventMentionFromJson";
my $DOCTHEORY_RESOLVER_EXE = "java -cp $hume_serif_util_jar_path com.bbn.serif.util.resolver.DocTheoryResolver";
# Libraries
my $NNEVENT_PYTHON_PATH = "$textopen_root/src/python:" . "$nlplingo_root";
my $BERT_REPO_PATH = "$external_dependencies_root/common/bert/repo/bert";
my $BERT_PYTHON_PATH = "$nlplingo_root:$BERT_REPO_PATH:$textopen_root/src/python";
my $BERT_TOKENIZER_PATH = "$hume_repo_root/src/python/bert/do_bert_tokenization.py";
my $BERT_EXTRACT_BERT_FEATURES_PATH = "$hume_repo_root/src/python/bert/extract_bert_features.py";
my $BERT_NPZ_EMBEDDING = "$hume_repo_root/src/python/bert/do_npz_embeddings.py";
my $BERT_GENERATE_FILE_LIST_BY_NUMBER_OF_TOKENS = "$hume_repo_root/src/python/bert/generate_bert_input_by_num_of_bert_tokens_with_reverse_order.py";
my $AFFINITY_SCHEDULER = "$hume_repo_root/src/python/pipeline/affinity_scheduler/scheduler.py";
my $AGGREGATE_WORD_PAIR_COUNTS = "$hume_repo_root/src/python/misc/aggregate_word_pair_count_dicts.py";

my $only_cpu_available = (get_param($params, "only_cpu_available", "false") eq "true");
if ($only_cpu_available) {
    $CONDA_ENV_NAME_FOR_BERT_GPU = $CONDA_ENV_NAME_FOR_BERT_CPU
}

my $BERT_MODEL_PATH = "$external_dependencies_root/common/bert/bert_model/uncased_L-12_H-768_A-12";
my $BERT_VOCAB_FILE = "$BERT_MODEL_PATH/vocab.txt";

# Please let @hqiu know if you want to change $SERIF_DATA
my $SERIF_DATA = "/d4m/serif/data";

my $NUM_OF_BATCHES_GLOBAL = get_param($params, "num_of_batches_global", 1);
my $NUM_OF_SCHEDULING_JOBS_FOR_NN = get_param($params, "num_of_scheduling_jobs_for_nn", "unknown");

my $mode = get_param($params, "mode");
my $internal_ontology_dir;
my $open_ontology_dir = "$hume_repo_root/resource/ontologies/open/";
my $external_ontology_dir;
if ($mode eq "CauseEx") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/causeex/";
    $external_ontology_dir = "";
}
elsif ($mode eq "WorldModelers") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/hume/";
    $external_ontology_dir = "$hume_repo_root/resource/dependencies/probabilistic_grounding/WM_Ontologies/";
}
elsif ($mode eq "BBN") {
    $internal_ontology_dir = "$hume_repo_root/resource/ontologies/internal/bbn";
    $external_ontology_dir = "";
}
else {
    die "mode has to be CauseEx or WorldModelers";
}

my $internal_event_ontology_yaml_filename = "event_ontology.yaml";
my $use_compositional_ontology = get_param($params, "use_compositional_ontology", "true");
if ($mode eq "WorldModelers" && $use_compositional_ontology eq "true") {
    $internal_event_ontology_yaml_filename = "compositional_event_ontology.yaml";
}

# Batch files
# my $batch_file_directory = make_output_dir("$processing_dir/batch_files");

check_requirements();

# Max jobs setting
max_jobs("$JOB_NAME/serif" => 200,);
max_jobs("$JOB_NAME/bert" => 100,);
max_jobs("$JOB_NAME/kbp" => 200,);
max_jobs("$JOB_NAME/learnit_decoder" => 100,);
max_jobs("$JOB_NAME/pyserif" => 100,);
max_jobs("$JOB_NAME/serialize" => 500,);

my $use_bert = (get_param($params, "use_bert", "true") eq "true");
my $max_number_of_tokens_per_sentence_global = int(get_param($params, "max_number_of_tokens_per_sentence", 250));


################
# CDR ingestion
################
my $input_metadata_file = "";
my $input_sgm_list = "";
if (exists $stages{"cdr-ingestion"}) {
    print "CDR ingestion stage\n";
    my $input_cdr_list = get_param($params, "input_cdr_list");
    my $breaking_point = int(get_param($params, "breaking_point", 30000));
    my $stage_name = "cdr_ingestion";

    (my $cdr_ingestion_output_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    (my $cdr_ingestion_batch_output_dir, my $mkdir_batch_jobids) = Utils::make_output_dir("$processing_dir/$stage_name/batch_file", "$JOB_NAME/$stage_name/mkdir_stage_processing_batch", []);
    my ($split_jobid, undef) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $PYTHON3,
        CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
        num_of_batches          => $NUM_OF_BATCHES_GLOBAL,
        suffix                  => "",
        output_file_prefix      => "$cdr_ingestion_batch_output_dir/",
        list_file_path          => $input_cdr_list,
        job_prefix              => "$JOB_NAME/$stage_name/",
        dependant_job_ids       => $mkdir_batch_jobids,
    );

    my @cdr_ingestion_jobs = ();
    for (my $n = 0; $n < $NUM_OF_BATCHES_GLOBAL; $n++) {
        (my $batch_processing_dir, my $mkdir_batch_jobid) = Utils::make_output_dir("$cdr_ingestion_output_dir/$n", "$JOB_NAME/$stage_name/$n/mkdir_batch_processing_" . $n, $split_jobid);
        my $batch_file = "$cdr_ingestion_batch_output_dir/$n";;
        my $cdr_ingestion_batch_jobid = runjobs(
            $mkdir_batch_jobid, "$JOB_NAME/$stage_name/$n/convert_cdr_to_corpus",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $CONVERT_CDR_TO_HUME_CORPUS --input_cdr_list $batch_file --output_folder $batch_processing_dir --breaking_point $breaking_point" ]
        );
        push(@cdr_ingestion_jobs, $cdr_ingestion_batch_jobid);
    }
    $input_metadata_file = "$cdr_ingestion_output_dir/metadata_all.txt";
    $input_sgm_list = "$cdr_ingestion_output_dir/sgms_all.list";
    my $list_results_metadata_jobid = runjobs(
        \@cdr_ingestion_jobs, "$JOB_NAME/$stage_name/list-metadata-results",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SCRIPT      => 1
        },
        [ "find $cdr_ingestion_output_dir -type f -name 'metadata.txt' -exec cat {} \\; > $input_metadata_file" ]
    );
    my $list_results_sgms_list_jobid = runjobs(
        \@cdr_ingestion_jobs, "$JOB_NAME/$stage_name/list-sgms-list-results",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
            SCRIPT      => 1
        },
        [ "find $cdr_ingestion_output_dir -type f -name 'sgms.list' -exec cat {} \\; | shuf > $input_sgm_list" ]
    );
    dojobs();
    # if (is_run_mode()) {
    #     open(FILE, "<$input_sgm_list") or die "Could not open file: $!";
    #     my $lines = 0;
    #     while (<FILE>) {
    #         $lines++;
    #     }
    #     if ($lines < 1) {
    #         die "Empty corpus folder detected!";
    #     }
    #     elsif ($lines < $NUM_OF_BATCHES_GLOBAL) {
    #         die "NUM_OF_BATCHES must be less than or equal to $lines";
    #     }
    #     close(FILE);
    # }
}
dojobs();


########
# Serif
########


my $GENERATED_SERIF_SERIFXML = "$processing_dir/serif_serifxml.list";
my $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR = "$processing_dir/serif_cause_effect_json";
my $GENERATED_FACTFINDER_JSON_FILE = "$processing_dir/serif/facts.json";
if (exists $stages{"serif"}) {
    print "Serif stage\n";

    # Run Serif in parallel
    my $mkdir_jobid;
    $input_sgm_list = get_param($params, "serif_input_sgm_list") eq "GENERATED" ? $input_sgm_list : get_param($params, "serif_input_sgm_list");

    my $serif_fast_mode = (get_param($params, "serif_fast_mode", "false") eq "true");

    my $gpe_pseudonym = (get_param($params, "gpe_pseudonym", "false") eq "true");

    my $stage_name = "serif";
    (my $master_serif_output_dir, $mkdir_jobid) = Utils::make_output_dir("$processing_dir/serif", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    (my $batch_file_dir, $mkdir_jobid) = Utils::make_output_dir("$master_serif_output_dir/batch_files", "$JOB_NAME/$stage_name/mkdir_stage_processing_batch", []);

    my ($split_serif_jobid, undef) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $PYTHON3,
        CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
        num_of_batches          => $NUM_OF_BATCHES_GLOBAL,
        suffix                  => "",
        output_file_prefix      => "$batch_file_dir/",
        list_file_path          => $input_sgm_list,
        job_prefix              => "$JOB_NAME/$stage_name/",
        dependant_job_ids       => [],
    );
    my $par_dir = $ENV{"SVN_PROJECT_ROOT"} . "/SERIF/par";

    my $should_track_files_read = get_param($params, "track_serif_files_read", "true");
    my $use_basic_cipher_stream = get_param($params, "use_basic_cipher_stream", "false");
    my $serif_cause_effect_patterns_dir = "$hume_repo_root/resource/serif_cause_effect_patterns";
    my $fast_mode_pars = "";
    if ($serif_fast_mode) {
        $fast_mode_pars = "
OVERRIDE run_icews: false
OVERRIDE run_fact_finder: false
OVERRIDE max_parser_seconds: 5
    ";
    }

    my @serif_jobs = ();
    for (my $n = 0; $n < $NUM_OF_BATCHES_GLOBAL; $n++) {
        my $job_batch_num = $n;
        my $serif_job_name = "$JOB_NAME/$stage_name/$job_batch_num";
        my $experiment_dir = "$master_serif_output_dir/$job_batch_num";
        my $batch_file = "$batch_file_dir/$job_batch_num";

        if (get_param($params, "serif_server_mode_endpoint", "None") eq "None") {
            if ($mode eq "CauseEx") {
                my $serif_par = "serif_causeex.par";
                my $icews_lib_dir = $ENV{"SVN_PROJECT_ROOT"} . "/W-ICEWS/lib";
                my $project_specific_serif_data_root = "$hume_repo_root/resource/serif_data_causeex";
                my $gpe_pseudonym_pars = "";
                if ($gpe_pseudonym) {
                    $gpe_pseudonym_pars = "
OVERRIDE tokenizer_subst: $project_specific_serif_data_root/tokenization/token-subst.data
";
                }
                my $serif_jobid =
                    runjobs(
                        $split_serif_jobid, $serif_job_name,
                        {
                            par_dir                           => $par_dir,
                            experiment_dir                    => $experiment_dir,
                            batch_file                        => $batch_file,
                            icews_lib_dir                     => $icews_lib_dir,
                            bbn_actor_db                      => get_param($params, "serif_input_awake_db"),
                            project_specific_serif_data_root  => $project_specific_serif_data_root,
                            cause_effect_output_dir           => $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR,
                            SERIF_DATA                        => $SERIF_DATA,
                            BATCH_QUEUE                       => $LINUX_QUEUE,
                            serif_cause_effect_patterns_dir   => $serif_cause_effect_patterns_dir,
                            should_track_files_read           => $should_track_files_read,
                            use_basic_cipher_stream           => $use_basic_cipher_stream,
                            max_number_of_tokens_per_sentence => $max_number_of_tokens_per_sentence_global,
                            fast_mode_pars                    => $fast_mode_pars,
                            gpe_pseudonym_pars                => $gpe_pseudonym_pars
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
                        $split_serif_jobid, $serif_job_name,
                        {
                            par_dir                           => $par_dir,
                            experiment_dir                    => $experiment_dir,
                            batch_file                        => $batch_file,
                            bbn_actor_db                      => get_param($params, "serif_input_awake_db"),
                            project_specific_serif_data_root  => $project_specific_serif_data_root,
                            cause_effect_output_dir           => $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR,
                            SERIF_DATA                        => $SERIF_DATA,
                            BATCH_QUEUE                       => $LINUX_QUEUE,
                            serif_cause_effect_patterns_dir   => $serif_cause_effect_patterns_dir,
                            should_track_files_read           => $should_track_files_read,
                            use_basic_cipher_stream           => $use_basic_cipher_stream,
                            max_number_of_tokens_per_sentence => $max_number_of_tokens_per_sentence_global,
                            fast_mode_pars                    => $fast_mode_pars
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
                        BATCH_QUEUE => $LINUX_QUEUE,
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
        Utils::make_output_dir($GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR, "$JOB_NAME/$stage_name/mkdir_dummy_fact_finder", []);
    }
    # Compine results into one list
    my $list_results_jobid = generate_file_list(\@serif_jobs, "$JOB_NAME/$stage_name/list-serif-results", "$master_serif_output_dir/*/output/*.xml", $GENERATED_SERIF_SERIFXML);
}

dojobs();

#######
# BERT
#######
my $GENERATED_BERT_NPZ_LIST = "NONE";
if ((exists $stages{"bert"}) && $use_bert) {
    print "bert stage\n";

    my $input_serifxml_list =
        get_param($params, "bert_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_SERIF_SERIFXML
            : get_param($params, "bert_input_serifxml_list");
    my $BERT_layers =
        get_param($params, "bert_layers") eq "DEFAULT"
            ? "-1"
            : get_param($params, "bert_layers");
    my $stage_name = "bert";
    (my $stage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/bert", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);

    my $single_bert_thread_mode = get_param($params, "single_bert_thread_mode", "false") eq "true";
    my $number_of_processes_bert_io = int(get_param($params, "number_of_batches_bert_io", $NUM_OF_BATCHES_GLOBAL));
    my $number_of_processes_bert_cpu = int(get_param($params, "number_of_batches_bert_cpu", $NUM_OF_BATCHES_GLOBAL));
    $GENERATED_BERT_NPZ_LIST = "$stage_processing_dir/bert_npz.list";

    my $bert_nn_batch_size = 32;
    my $bucket_size = 128;
    my $maximum_allowed_bert_tokens_per_sentence = 1.5 * $max_number_of_tokens_per_sentence_global; # Maximum is 512 from @ychan

    my $token_map_dir;

    my $token_map_list = "$stage_processing_dir/token_map.list";
    my $sent_info_list_by_docid_for_s1 = "$stage_processing_dir/sent_info_list_by_docid_for_s1.list";

    my $list_token_map_jobid;
    my $list_sent_info_list_by_docid_for_s1_jobid;
    {
        # Stage 1. Got alignment map in between serif and bert token. Get pure serif token
        my @extract_token_map_and_serif_token_jobs = ();
        my $mini_stage = "extract_token_map_and_serif_tokens";
        (my $batch_file_directory, my $mkdir_batch_jobid) = Utils::make_output_dir("$stage_processing_dir/$mini_stage/batch_files", "$JOB_NAME/$stage_name/$mini_stage/mkdir_stage_processing_batch", []);
        $token_map_dir = "$stage_processing_dir/$mini_stage/token_map";

        my ($split_bert_jobid, undef) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            num_of_batches          => $number_of_processes_bert_io,
            suffix                  => "",

            output_file_prefix      => "$batch_file_directory/bert_batch_file_",
            list_file_path          => $input_serifxml_list,
            job_prefix              => "$JOB_NAME/$stage_name/$mini_stage/",
            dependant_job_ids       => $mkdir_batch_jobid,
        );
        for (my $n = 0; $n < $number_of_processes_bert_io; $n++) {
            my $batch_file = "$batch_file_directory/bert_batch_file_$n";
            (my $token_map_dir_batch, undef) = Utils::make_output_dir("$token_map_dir/$n", "$JOB_NAME/$stage_name/$mini_stage/$n/mkdir_token_map_batch", []);
            my $add_prefix_to_serifxml_in_list_jobid =
                runjobs(
                    $split_bert_jobid, "$JOB_NAME/$stage_name/$mini_stage/$n/make_bert_batch_files_add_prefix",
                    {
                        BATCH_QUEUE => $LINUX_QUEUE,
                        SCRIPT      => 1
                    },
                    [ "cat $batch_file | awk '{print \"SERIF:\"\$0}' > $batch_file\.with_type" ]
                );
            my $producing_bert_tokens = runjobs(
                [ $add_prefix_to_serifxml_in_list_jobid ], "$JOB_NAME/$stage_name/$mini_stage/$n/bert_tokens",
                {
                    BATCH_QUEUE => $LINUX_QUEUE
                },
                [ "env PYTHONPATH=$BERT_PYTHON_PATH MKL_NUM_THREADS=1 $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT_CPU/bin/python $BERT_TOKENIZER_PATH --filelist $batch_file\.with_type --bert_vocabfile $BERT_VOCAB_FILE --outdir $token_map_dir_batch --maximum_allowed_bert_tokens_per_sentence $maximum_allowed_bert_tokens_per_sentence --do_lower_case True" ]
            );
            push(@extract_token_map_and_serif_token_jobs, $producing_bert_tokens);
        }
        $list_token_map_jobid = generate_file_list(\@extract_token_map_and_serif_token_jobs, "$JOB_NAME/$stage_name/$mini_stage/list-token_map-results", "$token_map_dir/*/*.token_map", $token_map_list);
        $list_sent_info_list_by_docid_for_s1_jobid = generate_file_list(\@extract_token_map_and_serif_token_jobs, "$JOB_NAME/$stage_name/$mini_stage/list-input_token-results", "$token_map_dir/*/sent_info.info", $sent_info_list_by_docid_for_s1);

    }

    my $batch_prefix_for_sorted_sentences = "sorted_sentences_";
    my $output_sorted_sentences_dir;
    my $generate_token_num_reverse_list_jobid;
    my $bert_job_list_path = "$stage_processing_dir/bert_job_list.list";
    my $number_of_batches_modified = $number_of_processes_bert_cpu;
    if ($single_bert_thread_mode) {
        $number_of_batches_modified = int($number_of_processes_bert_cpu * $NUM_OF_BATCHES_GLOBAL);
    }
    {
        # Stage 2. Sort Sentences list by their number of tokens
        my $mini_stage = "sort_sentence_list_by_number_of_tokens";
        $output_sorted_sentences_dir = "$stage_processing_dir/$mini_stage";

        $generate_token_num_reverse_list_jobid = runjobs(
            [ $list_sent_info_list_by_docid_for_s1_jobid ], "$JOB_NAME/$stage_name/$mini_stage",
            {
                BATCH_QUEUE => $LINUX_QUEUE
            },
            [ "env MKL_NUM_THREADS=1 $PYTHON3 $BERT_GENERATE_FILE_LIST_BY_NUMBER_OF_TOKENS --input_sent_info_list $sent_info_list_by_docid_for_s1 --number_of_batches $number_of_batches_modified --batch_prefix $batch_prefix_for_sorted_sentences --output_path $output_sorted_sentences_dir --bert_job_list_path $bert_job_list_path" ]
        );
    }

    my $bert_output_dir = "$stage_processing_dir/bert_embs";
    my $bert_output_prefix = "bert_emb_";
    my @run_bert_jobs = ();
    {
        # Stage 3. Run bert

        my $mini_stage = "run_bert";

        (my $batch_file_directory, my $mkdir_bert_batch_jobids) = Utils::make_output_dir("$stage_processing_dir/$mini_stage/run_bert_batch", "$JOB_NAME/$stage_name/$mini_stage/mkdir_batch_folder", [ $generate_token_num_reverse_list_jobid ]);

        my ($split_bert_jobid, undef) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            num_of_batches          => $number_of_processes_bert_cpu,
            suffix                  => "",
            output_file_prefix      => "$batch_file_directory/bert_batch_file_",
            list_file_path          => $bert_job_list_path,
            job_prefix              => "$JOB_NAME/$stage_name/$mini_stage/split_batch",
            dependant_job_ids       => $mkdir_bert_batch_jobids,
        );

        for (my $n = 0; $n < $number_of_processes_bert_cpu; $n++) {
            my $input_batch_file = "$batch_file_directory/bert_batch_file_$n";
            my $runjob_conf = {};
            $runjob_conf->{BATCH_QUEUE} = $SINGULARITY_GPU_QUEUE;
            $runjob_conf->{SGE_VIRTUAL_FREE} = "12G";

            if ($single_bert_thread_mode) {
                $runjob_conf->{SCRIPT} = 1;
                $runjob_conf->{SGE_VIRTUAL_FREE} = "28G";
                $runjob_conf->{max_memory_over} = "228G";
            }

            if ($single_bert_thread_mode) {
                (my $scratch_file_directory, my $mkdir_scratch_batch_jobids) = Utils::make_output_dir("$stage_processing_dir/$mini_stage/$n/run_bert_scratch", "$JOB_NAME/$stage_name/$mini_stage/$n/mkdir_scratch_folder", $mkdir_bert_batch_jobids);
                my $run_bert_jobid = runjobs(
                    $split_bert_jobid, "$JOB_NAME/$stage_name/$mini_stage/$n/run_bert",
                    $runjob_conf,
                    [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $AFFINITY_SCHEDULER --input_list_path $input_batch_file --batch_id $n --number_of_batches $NUM_OF_BATCHES_GLOBAL --command_prefix \"env PYTHONPATH=$BERT_PYTHON_PATH MKL_NUM_THREADS=1 $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT_GPU/bin/python $BERT_EXTRACT_BERT_FEATURES_PATH \-\-input_batch_file BBN_INPUT_BATCH_FILE \-\-output_dir $bert_output_dir \-\-output_prefix $bert_output_prefix \-\-current_bert_batch_id BBN_PASS_IN_BATCH_ID_FIELD \-\-BERT_BASE_DIR $BERT_MODEL_PATH \-\-layers $BERT_layers \-\-batch_size $bert_nn_batch_size \-\-bucket_size $bucket_size \-\-do_lower_case True \-\-max_seq_length $maximum_allowed_bert_tokens_per_sentence\" --batch_arg_name BBN_INPUT_BATCH_FILE --scratch_space $scratch_file_directory --pass_in_batch_id_field BBN_PASS_IN_BATCH_ID_FIELD --number_of_jobs_from_user $NUM_OF_SCHEDULING_JOBS_FOR_NN" ]
                );
                push(@run_bert_jobs, $run_bert_jobid);
            }
            else {
                my $run_bert_jobid = runjobs(
                    $split_bert_jobid, "$JOB_NAME/$stage_name/$mini_stage/$n/run_bert",
                    $runjob_conf,
                    [ "env PYTHONPATH=$BERT_PYTHON_PATH MKL_NUM_THREADS=1 $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT_GPU/bin/python $BERT_EXTRACT_BERT_FEATURES_PATH --input_batch_file $input_batch_file --output_dir $bert_output_dir --output_prefix $bert_output_prefix --current_bert_batch_id $n --BERT_BASE_DIR $BERT_MODEL_PATH --layers $BERT_layers --batch_size $bert_nn_batch_size --bucket_size $bucket_size --do_lower_case True --max_seq_length $maximum_allowed_bert_tokens_per_sentence" ]

                );
                push(@run_bert_jobs, $run_bert_jobid);
            }

        }

    }

    my $generated_npz_dir;

    {
        # Stage 4. Generate NPZ
        my $mini_stage = "generate_npz";
        my @generate_npz_jobid = ();
        $generated_npz_dir = "$stage_processing_dir/$mini_stage/npzs";
        for (my $n = 0; $n < $number_of_batches_modified; $n++) {
            my $batch_dir = "$bert_output_dir/$bert_output_prefix" . $n;
            (undef, my $mkdir_minijob_id) = Utils::make_output_dir("$batch_dir", "$JOB_NAME/$stage_name/$mini_stage/$n/mkdir", []);
            my $batch_out_dir = "$generated_npz_dir/$n";
            my $generate_npz_jobid = runjobs(
                \@run_bert_jobs, "$JOB_NAME/$stage_name/$mini_stage/$n/generate_npz",
                {
                    BATCH_QUEUE => $LINUX_QUEUE
                },
                [ "env MKL_NUM_THREADS=1 $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_BERT_CPU/bin/python $BERT_NPZ_EMBEDDING --batch_dir $batch_dir --token_map_list $token_map_list --outdir $batch_out_dir" ]

            );
            push(@generate_npz_jobid, $generate_npz_jobid);
        }
        my $list_results_jobid = generate_file_list(\@generate_npz_jobid, "$JOB_NAME/$stage_name/$mini_stage/list-bert-results", "$generated_npz_dir/*/*.npz", $GENERATED_BERT_NPZ_LIST);

        my $clean_up_jobid = runjobs(
            $list_results_jobid, "$JOB_NAME/$stage_name/$mini_stage/cleanup",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
                SCRIPT      => 1
            },
            [ "rm -rf $token_map_dir" ],
            [ "rm -rf $output_sorted_sentences_dir" ],
            [ "rm -rf $bert_output_dir" ]
        );
    }
}

dojobs();

######
# KBP
######
my $GENERATED_KBP_SERIFXML = $GENERATED_SERIF_SERIFXML;
if (exists $stages{"kbp"}) {
    print "KBP stage\n";
    my $mkdir_jobid;
    $GENERATED_KBP_SERIFXML = "$processing_dir/kbp_serifxml.list";

    my $input_serifxml_list =
        get_param($params, "kbp_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_SERIF_SERIFXML
            : get_param($params, "kbp_input_serifxml_list");
    my $stage_name = "kbp";
    (my $master_kbp_output_dir, $mkdir_jobid) = Utils::make_output_dir("$processing_dir/kbp", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    (my $batch_file_directory, $mkdir_jobid) = Utils::make_output_dir("$master_kbp_output_dir/batch_files", "$JOB_NAME/$stage_name/mkdir_stage_processing_batch", []);
    # Run KBP event finding in parallel


    my ($split_kbp_jobid, undef) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $PYTHON3,
        CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
        num_of_batches          => $NUM_OF_BATCHES_GLOBAL,
        suffix                  => "",

        output_file_prefix      => "$batch_file_directory/kbp_batch_file_",
        list_file_path          => $input_serifxml_list,
        job_prefix              => "$JOB_NAME/$stage_name/",
        dependant_job_ids       => [],
    );

    my @kbp_jobs = ();
    for (my $n = 0; $n < $NUM_OF_BATCHES_GLOBAL; $n++) {
        my $job_batch_num = $n;
        (my $batch_processing_dir, $mkdir_jobid) = Utils::make_output_dir("$master_kbp_output_dir/$job_batch_num", "$JOB_NAME/$stage_name/$job_batch_num/mkdir_batch_processing_" . $job_batch_num, []);
        (my $strip_event_serif_out_dir, $mkdir_jobid) = Utils::make_output_dir("$batch_processing_dir/strip_events/", "$JOB_NAME/$stage_name/$job_batch_num/mkdir_batch_processing_strip_" . $job_batch_num, []);
        my $batch_input_file = "$batch_file_directory/kbp_batch_file_$job_batch_num";
        my $stripped_events_serifxml_list = "$batch_file_directory/stripped_$job_batch_num.list";
        my $strip_events_jobid =
            runjobs(
                $split_kbp_jobid, "$JOB_NAME/$stage_name/$job_batch_num/strip_events-$job_batch_num",
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
        my $kbp_job_name = "$JOB_NAME/$stage_name/$job_batch_num/kbp-$job_batch_num";
        my $kbp_jobid =
            runjobs(
                [ $strip_events_jobid ], $kbp_job_name,
                {
                    output_file_list           => $kbp_output_serifxml_list,
                    input_file_list            => $stripped_events_serifxml_list,
                    output_directory           => $kbp_output_dir,
                    SERIF_DATA                 => $SERIF_DATA,
                    BATCH_QUEUE                => $LINUX_QUEUE,
                    dependencies_root          => $dependencies_root,
                    external_dependencies_root => $external_dependencies_root,
                    SGE_VIRTUAL_FREE           => [ "24G", "32G", "48G" ],
                    job_retries                => 3
                },
                [ "env JAVA_OPTS=\"-Xmx48G\" $KBP_EVENT_FINDER_EXE", "kbp_event_finder.par" ]
            );
        push(@kbp_jobs, $kbp_jobid);
    }

    # Compine results into one list
    my $list_results_jobid = generate_file_list(\@kbp_jobs, "$JOB_NAME/$stage_name/list-kbp-results", "$master_kbp_output_dir/*/output/*.xml", $GENERATED_KBP_SERIFXML);
}

dojobs();

###################################
# LearnIt  UnaryEvent and EventArg
###################################
my $LEARNIT_DECODER_SERIFXML = $GENERATED_KBP_SERIFXML;
if (exists $stages{"learnit-decoder"}) {
    print "LearnIt decoder stage\n";
    my $mkdir_jobid;
    my $learnit_decoder_jobids;
    my $output_learnit_seriflist_path;
    my $cserif_causal_json_stage_processing_dir;
    {
        my $stage_name = "learnit_decoder/learnit";
        my $generic_event_noun_whitelist = get_param($params, "generic_event_noun_whitelist", "GENERATED") eq "GENERATED" ? "$hume_repo_root/resource/generic_events/generic_event.whitelist.wn-fn.variants" : get_param($params, "generic_event_noun_whitelist");
        my $generic_event_blacklist = get_param($params, "generic_event_blacklist", "GENERATED") eq "GENERATED" ? "$hume_repo_root/resource/generic_events/modal_aux.verbs.list" : get_param($params, "generic_event_blacklist");
        my $learnit_event_and_event_arg_pattern_dir = "DUMMY";
        my $learnit_unary_entity_extractors = "DUMMY";
        my $stage_to_run;
        if ($mode eq "CauseEx") {
            $stage_to_run = "generic_event,unary_event_and_binary_event_argument_decoding,binary_event_event_decoding";
            $learnit_event_and_event_arg_pattern_dir = get_param($params, "learnit_event_and_event_arg_pattern_dir") eq "DEFAULT"
                ? "$hume_repo_root/resource/domains/CX_ICM/learnit/unary_event.legacy,$hume_repo_root/resource/domains/CX_ICM/learnit/unary_event"
                : get_param("learnit_event_and_event_arg_pattern_dir");
        }
        elsif ($mode eq "BBN") {
            $stage_to_run = "generic_event,unary_event_and_binary_event_argument_decoding,binary_event_event_decoding";
            $learnit_event_and_event_arg_pattern_dir = get_param($params, "learnit_event_and_event_arg_pattern_dir") eq "DEFAULT"
                ? "$hume_repo_root/resource/domains/BBN/learnit/unary_event"
                : get_param("learnit_event_and_event_arg_pattern_dir");
        }
        else {
            $stage_to_run = "generic_event,unary_entity,unary_event_and_binary_event_argument_decoding,binary_event_event_decoding";
            $learnit_event_and_event_arg_pattern_dir = get_param($params, "learnit_event_and_event_arg_pattern_dir") eq "DEFAULT"
                ? "$hume_repo_root/resource/domains/WM/learnit/unary_event.legacy,$hume_repo_root/resource/domains/WM/learnit/unary_event"
                : get_param("learnit_event_and_event_arg_pattern_dir");
            $learnit_unary_entity_extractors = get_param($params, "learnit_unary_entity_pattern_dir") eq "DEFAULT" ?
                "$hume_repo_root/resource/domains/WM/learnit/unary_entity" : get_param($params, "learnit_unary_entity_pattern_dir");
        }
        my $learnit_event_event_relation_pattern_dir = get_param($params, "learnit_event_event_relation_pattern_dir") eq "DEFAULT" ? "$hume_repo_root/resource/domains/common/learnit/binary_event.legacy,$hume_repo_root/resource/domains/common/learnit/binary_event" : get_param($params, "learnit_event_event_relation_pattern_dir");

        my $input_serifxml_list =
            get_param($params, "learnit_decoder_input_serifxml_list") eq "GENERATED"
                ? $GENERATED_KBP_SERIFXML
                : get_param($params, "learnit_decoder_input_serifxml_list");

        my $learnit_decoding_obj = LearnItDecoding->new(
            TEXT_OPEN   => $textopen_root,
            PYTHON3     => $PYTHON3,
            BATCH_QUEUE => $LINUX_QUEUE,
            MEM_LIMIT   => "16G"
        );
        ($learnit_decoder_jobids, $output_learnit_seriflist_path) = $learnit_decoding_obj->LearnItDecoding(
            dependant_job_ids                 => [],
            job_prefix                        => "$JOB_NAME/$stage_name",
            runjobs_template_path             => "learnit_decoding_pipeline.par",
            runjobs_template_hash             => {
                stages_to_run                                    => $stage_to_run,
                max_number_of_tokens_per_sentence                => $max_number_of_tokens_per_sentence_global,
                generic_event_noun_whitelist                     => $generic_event_noun_whitelist,
                generic_event_blacklist                          => $generic_event_blacklist,
                unary_event_and_binary_event_argument_extractors => $learnit_event_and_event_arg_pattern_dir,
                binary_event_event_extractors                    => $learnit_event_event_relation_pattern_dir,
                unary_entity_extractors                          => $learnit_unary_entity_extractors

            },
            input_serifxml_list               => $input_serifxml_list,
            num_of_jobs                       => $NUM_OF_BATCHES_GLOBAL,
            stage_processing_dir              => "$processing_dir/$stage_name",
            should_output_incomplete_examples => "false"
        );
    }

    # {
    #     #### Code block for adding CSerif causal json back
    #     my $stage_name = "learnit_decoder/cserif_causal_json";
    #     ($cserif_causal_json_stage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    #     (my $batch_file_dir, undef) = Utils::make_output_dir("$cserif_causal_json_stage_processing_dir/batch_files", "$JOB_NAME/$stage_name/mkdir_staging_processing_batch_files", []);
    #
    #     my $input_json_list = get_param($params, "input_serif_cause_effect_relations_dir") eq "GENERATED"
    #         ? $GENERATED_SERIF_CAUSE_EFFECT_JSON_DIR
    #         : get_param($params, "input_serif_cause_effect_relations_dir");
    #
    #     my ($split_cserif_causal_json_jobid, undef) = Utils::split_file_list_with_num_of_batches(
    #         PYTHON                  => $PYTHON3,
    #         CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
    #         num_of_batches          => $NUM_OF_BATCHES_GLOBAL,
    #         suffix                  => "",
    #
    #         output_file_prefix      => "$batch_file_dir/",
    #         list_file_path          => $output_learnit_seriflist_path,
    #         job_prefix              => "$JOB_NAME/$stage_name/",
    #         dependant_job_ids       => $learnit_decoder_jobids,
    #     );
    #
    #     my @create_event_event_relations_split_jobs = ();
    #
    #     for (my $n = 0; $n < $NUM_OF_BATCHES_GLOBAL; $n++) {
    #         my $job_batch_num = $n;
    #         (my $batch_processing_folder, $mkdir_jobid) = Utils::make_output_dir("$cserif_causal_json_stage_processing_dir/$job_batch_num/serifxml_uncalibrated", "$JOB_NAME/$stage_name/$job_batch_num/mkdir_uncalibrated_" . $job_batch_num, []);
    #         my $input_batch_file = "$batch_file_dir/$job_batch_num";
    #
    #         my $create_event_event_relations_jobid =
    #             runjobs(
    #                 $split_cserif_causal_json_jobid, "$JOB_NAME/$stage_name/add_causal_relations_$job_batch_num",
    #                 {
    #                     input_serifxml_list       => $input_batch_file,
    #                     output_serifxml_directory => $batch_processing_folder,
    #                     input_json_list           => $input_json_list,
    #                     BATCH_QUEUE               => $LINUX_QUEUE,
    #                 },
    #                 [ "$EVENT_EVENT_RELATION_EXE", "event_event_relations.par" ],
    #             );
    #         push(@create_event_event_relations_split_jobs, $create_event_event_relations_jobid);
    #     }
    #
    #     my $list_uncalibrate_eer_serif_jobid = generate_file_list(\@create_event_event_relations_split_jobs, "$JOB_NAME/$stage_name/list_uncalibrate_serifxml", "$cserif_causal_json_stage_processing_dir/*/serifxml_uncalibrated/*.xml", "$cserif_causal_json_stage_processing_dir/cserif_causal_json_serif.list");
    #     ## End code boundary for OpenNRE
    # }


    #### End code block
    $LEARNIT_DECODER_SERIFXML = "$output_learnit_seriflist_path";
}
dojobs();

##################
# NN Event Typing 
##################
my $GENERATED_NN_EVENT_SERIFXML = $LEARNIT_DECODER_SERIFXML;

if (exists $stages{"nn-event-typing"}) {
    print "NN Event Typing stage\n";
    my $mkdir_jobid;
    my $input_serifxml_list =
        get_param($params, "nn_event_typing_input_serifxml_list") eq "GENERATED"
            ? $LEARNIT_DECODER_SERIFXML
            : get_param($params, "nn_event_typing_input_serifxml_list");

    (my $nn_event_typing_processing_dir, $mkdir_jobid) = Utils::make_output_dir("$processing_dir/nn_event_typing", "$JOB_NAME/nn_event_typing/mkdir_stage_processing", []);
    my $nn_event_typing_prefix = "nn_event_typing";

    # create_nn_decoder_input
    (my $nn_type_decoder_output_dir, $mkdir_jobid) = Utils::make_output_dir("$nn_event_typing_processing_dir/nn_type_decoder_output/", "$JOB_NAME/nn_event_typing/mkdir_stage_processing_output", []);
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
                BATCH_QUEUE           => $LINUX_QUEUE,
            },
            [ "sh", "update_serifxml_with_event_typing.sh" ]
        );

    dojobs();

    $GENERATED_NN_EVENT_SERIFXML = $nn_event_typing_serifxml_list;
}

dojobs();


# # genericity has been turned off for the moment. Will need to turn it back later
# if (exists $stages{"kbp"}) {
#     print "kbp genericity stage\n";
#     my $stage_name = "kbp_genericity";
#     my $input_serifxml_list = $GENERATED_NN_DECODER_SERIFXML;
#     # run genericity classifier
#     my ($stage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
#     my ($batch_file_directory, undef) = Utils::make_output_dir("$stage_processing_dir/batch_file", "$JOB_NAME/$stage_name/mkdir_stage_processing_batch", []);
#
#     my ($split_nn_kbp_genericity_jobid, undef) = Utils::split_file_list_with_num_of_batches(
#         PYTHON                  => $PYTHON3,
#         CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
#         num_of_batches          => $NUM_OF_BATCHES_GLOBAL,
#         suffix                  => "",
#
#         output_file_prefix      => "$batch_file_directory/kbp_genericity_batch_file_",
#         list_file_path          => $input_serifxml_list,
#         job_prefix              => "$JOB_NAME/$stage_name/",
#         dependant_job_ids       => [],
#     );
#
#     my @kbp_genericity_jobs = ();
#
#     for (my $n = 0; $n < $NUM_OF_BATCHES_GLOBAL; $n++) {
#         my $job_batch_num = $n;
#         my $batch_file = "$batch_file_directory/kbp_genericity_batch_file_$job_batch_num";
#         my $nn_event_genericity_job_name = "$JOB_NAME/$stage_name/$job_batch_num/genericity_$job_batch_num";
#         my ($batch_processing_dir, undef) = Utils::make_output_dir("$stage_processing_dir/$job_batch_num/genericity_output", "$JOB_NAME/$stage_name/$job_batch_num/mkdir_stage_processing", []);
#         my $nn_events_genericity_output_list = "$batch_processing_dir/nn_events_genericity.DONOTUSE"; # DO NOT USE THIS JUST A PLACEHOLDER
#         my $nn_event_genericity_jobid =
#             runjobs(
#                 $split_nn_kbp_genericity_jobid, $nn_event_genericity_job_name,
#                 {
#                     dependencies_root          => $dependencies_root,
#                     external_dependencies_root => $external_dependencies_root,
#                     output_file_list           => $nn_events_genericity_output_list,
#                     input_file_list            => $batch_file,
#                     output_directory           => $batch_processing_dir,
#                     SERIF_DATA                 => $SERIF_DATA,
#                     BATCH_QUEUE                => $LINUX_QUEUE,
#                     SGE_VIRTUAL_FREE           => "20G"
#
#                 },
#                 [ "$KBP_EVENT_FINDER_EXE", "kbp_genericity_only.par" ]
#             );
#         push(@kbp_genericity_jobs, $nn_event_genericity_jobid);
#     }
#     my $output_serif_list = "$processing_dir/$stage_name.list";
#     my $list_results_jobid = generate_file_list(\@kbp_genericity_jobs, "$JOB_NAME/$stage_name/list-kbp-genericity-results", "$stage_processing_dir/*/genericity_output/*.xml", $output_serif_list);
#     $GENERATED_NN_DECODER_SERIFXML = $output_serif_list;
# }
#
# dojobs();

######################
# Bias/Reliability/Credibility
######################
if (exists $stages{"bias"}) {
    print "Bias/Reliability stage\n";

    my $input_serifxml_list =
        get_param($params, "bias_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_NN_EVENT_SERIFXML
            : get_param($params, "bias_input_serifxml_list");
    my $bias_host_name = get_param($params, "bias_host");
    my $bias_metadata = get_param($params, "bias_input_metadata_file");

    my $stage_name = "bias";
    my $mkdir_jobid;
    (my $stage_processing_dir, $mkdir_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    (my $batch_file_directory, $mkdir_jobid) = Utils::make_output_dir("$stage_processing_dir/batch_file", "$JOB_NAME/$stage_name/mkdir_stage_processing_batch", []);

    # Run bias/reliability modeling in parallel

    my ($split_bias_jobid, undef) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $PYTHON3,
        CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
        num_of_batches          => $NUM_OF_BATCHES_GLOBAL,
        suffix                  => "",

        output_file_prefix      => "$batch_file_directory/bias_batch_file_",
        list_file_path          => $input_serifxml_list,
        job_prefix              => "$JOB_NAME/$stage_name/",
        dependant_job_ids       => [],
    );

    my @bias_jobs = ();
    for (my $n = 0; $n < $NUM_OF_BATCHES_GLOBAL; $n++) {
        my $job_batch_num = $n;
        my $batch_file = "$batch_file_directory/bias_batch_file_$job_batch_num";

        (my $batch_processing_dir, $mkdir_jobid) = Utils::make_output_dir(
            "$stage_processing_dir/$job_batch_num", "$JOB_NAME/$stage_name/$job_batch_num/mkdir_batch_processing_" . $job_batch_num, []);

        # assume CDRs are already in bias data dir

        # run curl and pipe to json in output dir
        my $bias_job = runjobs(
            $split_bias_jobid,
            "$JOB_NAME/$stage_name/run_bias_$job_batch_num",
            {
                BATCH_QUEUE      => $LINUX_QUEUE,
                batch_file       => $batch_file,
                bias_metadata    => $bias_metadata,
                bias_host        => $bias_host_name,
                batch_output_dir => $batch_processing_dir
            },
            [ "/bin/bash", "run_bias.sh" ]
        );
        push(@bias_jobs, $bias_job);

        # validate output
        my $validate_bias_job = runjobs(
            [ $bias_job ],
            "$JOB_NAME/$stage_name/validate_bias_$job_batch_num",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
                SCRIPT      => 1,
            },
            [ "$PYTHON3 $VALIDATE_JSON_SCRIPT $batch_processing_dir" ]
        );
        push(@bias_jobs, $validate_bias_job);
    }
}

dojobs();


######################
# Event consolidation
######################
my $GENERATED_PYSERIF_SERIFXML = $GENERATED_NN_EVENT_SERIFXML;
if (exists $stages{"pyserif"}) {
    print "PySerif consolidation stage\n";

    my $input_serifxml_list =
        get_param($params, "pyserif_input_serifxml_list") eq "GENERATED"
            ? $GENERATED_NN_EVENT_SERIFXML
            : get_param($params, "pyserif_input_serifxml_list");

    # "NONE" acceptable for when not using BERT
    my $bert_npz_file_list =
        get_param($params, "bert_npz_filelist") eq "GENERATED"
            ? $GENERATED_BERT_NPZ_LIST
            : get_param($params, "bert_npz_filelist");

    my $stage_name = "pyserif";
    my $single_bert_thread_mode = get_param($params, "single_bert_thread_mode", "false") eq "true";
    my $number_of_batches_pyserif = int(get_param($params, "number_of_batches_pyserif", $NUM_OF_BATCHES_GLOBAL));

    my $output_pyserif_eer_doc_list;
    my $pyserif_eer_list_collector_job_id;

    my $output_pyserif_main_doc_list;
    my $pyserif_main_list_collector_job_id;
    my $pyserif_main_list_count_collector_job_id;
    my $word_pair_count_list;

    {
        my $mini_stage_name = "pyserif_eer";
        (my $ministage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_processing", []);
        (my $ministage_batch_dir, my $mkdir_batch_jobs) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name/batch_file", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_batch_processing", []);

        (my $create_filelist_jobid, undef
        ) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            dependant_job_ids       => $mkdir_batch_jobs,
            job_prefix              => "$JOB_NAME/$stage_name/$mini_stage_name/",
            num_of_batches          => $number_of_batches_pyserif,
            list_file_path          => $input_serifxml_list,
            output_file_prefix      => $ministage_batch_dir . "/batch_",
            suffix                  => ".list",
        );

        my $eer_template;
        if ($mode eq "BBN") {
            $eer_template = "pyserif_eer_bbn.par";
        }
        else {
            $eer_template = "pyserif_eer.par";
        }

        my $pyserif_template = {
            BATCH_QUEUE                       => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE                  => "8G",
            textopen_root                     => $textopen_root,
            hume_root                         => $hume_repo_root,
            bert_npz_file_list                => $bert_npz_file_list,
            max_number_of_tokens_per_sentence => $max_number_of_tokens_per_sentence_global,
        };
        if ($single_bert_thread_mode) {
            $pyserif_template->{SCRIPT} = 1;
            $pyserif_template->{SGE_VIRTUAL_FREE} = "28G";
            $pyserif_template->{max_memory_over} = "228G";
        }
        my @split_jobs = ();
        for (my $batch = 0; $batch < $number_of_batches_pyserif; $batch++) {
            my $batch_file = "$ministage_batch_dir/batch_$batch.list";
            my $batch_output_folder = "$ministage_processing_dir/$batch/output";

            if ($single_bert_thread_mode) {
                (my $ministage_scratch_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name/scratch_file/$batch", "$JOB_NAME/$stage_name/$mini_stage_name/$batch/mkdir_stage_scratch_processing", []);
                (my $basic_file_name, undef) = fileparse($eer_template);
                my $expanded_template_path = "$exp_root/etemplates/$JOB_NAME/$stage_name/$mini_stage_name/$exp-pyserif_$batch.$basic_file_name";
                my $pyserif_dep_jobid = runjobs4::runjobs(
                    $create_filelist_jobid, "$JOB_NAME/$stage_name/$mini_stage_name/pyserif_$batch",
                    $pyserif_template,
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "mkdir -p $batch_output_folder" ],
                    [ "$PYTHON3 -c pass", $eer_template ],
                    [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $AFFINITY_SCHEDULER --input_list_path $batch_file\.with_type --batch_id $batch --number_of_batches $NUM_OF_BATCHES_GLOBAL --command_prefix \"env PYTHONPATH=$nlplingo_root:$textopen_root/src/python MKL_NUM_THREADS=1 KERAS_BACKEND=tensorflow $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $textopen_root/src/python/serif/driver/pipeline_sequence.py $expanded_template_path BBN_INPUT_BATCH_FILE $batch_output_folder\" --batch_arg_name BBN_INPUT_BATCH_FILE --scratch_space $ministage_scratch_dir --number_of_jobs_from_user $NUM_OF_SCHEDULING_JOBS_FOR_NN" ]
                );
                push(@split_jobs, $pyserif_dep_jobid);
            }
            else {
                my $pyserif_dep_jobid = runjobs4::runjobs(
                    $create_filelist_jobid, "$JOB_NAME/$stage_name/$mini_stage_name/pyserif_$batch",
                    $pyserif_template,
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "mkdir -p $batch_output_folder" ],
                    [ "env PYTHONPATH=$nlplingo_root:$textopen_root/src/python " .
                        "MKL_NUM_THREADS=1 KERAS_BACKEND=tensorflow " .
                        "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $textopen_root/src/python/serif/driver/pipeline_sequence.py", $eer_template, "$batch_file\.with_type $batch_output_folder" ]
                );
                push(@split_jobs, $pyserif_dep_jobid);
            }

        }
        $output_pyserif_eer_doc_list = "$ministage_processing_dir/pyserif_serifxmls_uncalibrated.list";
        $pyserif_eer_list_collector_job_id = generate_file_list(\@split_jobs, "$JOB_NAME/$stage_name/$mini_stage_name/list_uncalibrate_serifxml", "$ministage_processing_dir/*/output/*.xml", $output_pyserif_eer_doc_list);
    }
    {

        my $mini_stage_name = "pyserif_main";

        # EC config
        $input_metadata_file = get_param($params, "metadata_file") eq "GENERATED" ? $input_metadata_file : get_param($params, "metadata_file");
        my $copyArgumentSentenceWindow = get_param($params, "copyArgumentSentenceWindow");
        my $lemmaFile = "$external_dependencies_root/common/lemma.nv";

        my $ec_resource_dir;
        my $dc_template;
        if ($mode eq "CauseEx") {
            $ec_resource_dir = "$hume_repo_root/resource/event_consolidation/causeex";
            $dc_template = "pyserif_main_cx.par";
        }
        elsif ($mode eq "BBN") {
            $ec_resource_dir = "$hume_repo_root/resource/event_consolidation/bbn";
            $dc_template = "pyserif_main_bbn.par";
        }
        else {
            $ec_resource_dir = "$hume_repo_root/resource/event_consolidation/wm";
            $dc_template = "pyserif_main_wm.par";
            if ($use_compositional_ontology eq "true") {
                $dc_template = "pyserif_main_wm_compositional.par"
            }
        }


        # my $dc_template = "pyserif_eer.par";

        my $eventOntologyYAMLFilePath = "$internal_ontology_dir/$internal_event_ontology_yaml_filename";
        my $adverbFile = "$hume_repo_root/resource/event_consolidation/adverb.list";
        my $prepositionFile = "$hume_repo_root/resource/event_consolidation/prepositions.list";
        my $verbFile = "$hume_repo_root/resource/event_consolidation/verbs.wn-fn.variants.filtered";
        my $lightVerbFile = "$hume_repo_root/resource/event_consolidation/common/light_verbs.txt";
        my $interventionJson = "$hume_repo_root/resource/event_consolidation/wm/intervention.json";
        my $roleOntologyFile = "$hume_repo_root/resource/ontologies/internal/common/role_ontology.yaml";
        my $themeIllegalTypes = "$ec_resource_dir/theme-invalid_entity_types.txt";
        my $themeFactors = "$ec_resource_dir/theme-factor_types.txt";
        my $themeConstraints = "$ec_resource_dir/theme-selection_constraints.txt";
        my $propertyProcessTypes = "$ec_resource_dir/property-process_types.txt";
        my $propertyPropertyTypes = "$ec_resource_dir/property-property_types.txt";

        # End EC config

        # PG config
        my $event_ontology = "$internal_ontology_dir/$internal_event_ontology_yaml_filename";
        my $exemplars = "$internal_ontology_dir/data_example_events.json";
        my $embeddings = "$external_dependencies_root/common/glove.6B.50d.p";
        my $stopwords = "$internal_ontology_dir/stopwords.list";
        my $threshold = "0.7";
        my $n_best = 5;
        my $grounding_mode;
        if ($use_bert) {
            $grounding_mode = get_param($params, "grounding_mode", "full");
        }
        else {
            $grounding_mode = get_param($params, "grounding_mode", "medium");
        }

        # End PG config

        # Nlplingo config
        my $nlplingo_decode_embedding;
        if (-e $bert_npz_file_list) {
            $nlplingo_decode_embedding = "bert";
        }
        else {
            $nlplingo_decode_embedding = "baroni";
        }
        # End Nlplingo config

        my $internal_causal_factor_ontology = "NONE";
        my $internal_causal_factor_ontology_bert_centroids = "NONE";
        my $internal_causal_factor_examplars = "NONE";
        my $internal_ontology_yaml = "NONE";
        my $internal_ontology_bert_centroids = "$internal_ontology_dir/event_centroid.json";
        my $grounding_blacklist = "NONE";
        my $grounding_icm_blacklist = "NONE";
        my $keywords = "$internal_ontology_dir/keywords-anchor_annotation.txt";
        my $pendingflip = "";

        if ($mode eq "CauseEx") {
            $internal_causal_factor_ontology = "$internal_ontology_dir/icms/$internal_event_ontology_yaml_filename";
            $internal_causal_factor_ontology_bert_centroids = "$internal_ontology_dir/icms/causal_factor_centroid.json";
            $internal_causal_factor_examplars = "$internal_ontology_dir/icms/data_example_events.bae.json";
            $grounding_icm_blacklist = "$internal_ontology_dir/icms/bae.blacklist.json";
        }
        else {
            $internal_ontology_yaml = $event_ontology;
            $event_ontology = "$external_ontology_dir/wm_flat_metadata.yml";
            if ($use_compositional_ontology eq "true") {
                $event_ontology = "$external_ontology_dir/CompositionalOntology_v2.1_metadata.yml"
            }
            $grounding_blacklist = "$external_dependencies_root/wm/wm.blacklist.interventions_20200305.json";
            $pendingflip = "$hume_repo_root/resource/event_consolidation/wm/pending_flip_typelist.json";
        }

        $threshold = # replace default threshold if specified
            get_param($params, "grounding_threshold", "DEFAULT") eq "DEFAULT"
                ? $threshold
                : get_param($params, "grounding_threshold");
        $n_best = # replace default n_best if specified
            get_param($params, "grounding_n_best", "DEFAULT") eq "DEFAULT"
                ? $n_best
                : get_param($params, "grounding_n_best");

        my $pyserif_template = {
            BATCH_QUEUE                        => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE                   => "8G",
            textopen_root                      => $textopen_root,
            doc_resolver_jar_path              => $hume_serif_util_jar_path,
            probabilictic_grounding_main_entry => $PROB_GROUNDING_SCRIPT,
            hume_root                          => $hume_repo_root,
            bert_npz_file_list                 => $bert_npz_file_list,
            max_number_of_tokens_per_sentence  => $max_number_of_tokens_per_sentence_global,
            nlplingo_embedding_name            => $nlplingo_decode_embedding,
            roleOntologyFile                   => $roleOntologyFile,
            ontologyFile                       => $eventOntologyYAMLFilePath,
            argumentRoleEntityTypeFile         => "$ec_resource_dir/event_typerole.entity_type.constraints",
            keywordFile                        => "$ec_resource_dir/event_type.keywords",
            lemmaFile                          => $lemmaFile,
            blacklistFile                      => "$ec_resource_dir/event_type.blacklist",
            cfOntologyFile                     => "$internal_ontology_dir/icms/$internal_event_ontology_yaml_filename",
            cfArgumentRoleEntityTypeFile       => "$ec_resource_dir/icms/event_typerole.entity_type.constraints",
            cfKeywordFile                      => "$ec_resource_dir/icms/event_type.keywords",
            cfBlacklistFile                    => "$ec_resource_dir/icms/event_type.blacklist",
            kbpEventMappingFile                => "$ec_resource_dir/KBP_events.json",
            propertyProcessTypes               => $propertyProcessTypes,
            propertyPropertyTypes              => $propertyPropertyTypes,
            themeFactors                       => $themeFactors,
            themeIllegalTypes                  => $themeIllegalTypes,
            themeConstraints                   => $themeConstraints,
            accentEventMappingFile             => "$hume_repo_root/resource/event_consolidation/accent_event_mapping.json",
            accentCodeToEventTypeFile          => "$hume_repo_root/resource/event_consolidation/cameo_code_to_event_type.txt",
            adverbFile                         => $adverbFile,
            prepositionFile                    => $prepositionFile,
            verbFile                           => $verbFile,
            kbpEventMappingFile                => "$ec_resource_dir/KBP_events.json",
            strInputMetadataFile               => $input_metadata_file,
            lightVerbFile                      => $lightVerbFile,
            interventionJson                   => $interventionJson,
            copyArgumentSentenceWindow         => $copyArgumentSentenceWindow,
            propertiesFile                     => "$hume_repo_root/resource/event_consolidation/common/event_mention_properties.json",
            causalRelationNegationFile         => "$hume_repo_root/resource/causal_relation_word_lists/negation.txt",
            causalRelationDirectory            => "$hume_repo_root/resource/causal_relation_word_lists/relations/",
            reverseFactorTypesFile             => "$hume_repo_root/resource/event_consolidation/common/event_properties_need_reverse_words_phrases.txt",
            factorKeywordWeightFile            => "$hume_repo_root/resource/event_consolidation/common/factor_properties_downweight_words_phrases.txt",
            keywords                           => $keywords,
            stopwords                          => $stopwords,
            grounding_mode                     => $grounding_mode,
            embeddings                         => $embeddings,
            event_exemplars                    => $exemplars,
            event_centroid_file                => $internal_ontology_bert_centroids,
            n_best                             => $n_best,
            event_blacklist                    => $grounding_blacklist,
            threshold                          => $threshold,
            icm_exemplars                      => $internal_causal_factor_examplars,
            icm_centroid_file                  => $internal_causal_factor_ontology_bert_centroids,
            icm_blacklist                      => $grounding_icm_blacklist,
            external_ontology                  => $event_ontology,
            pendingflip                        => $pendingflip,
            lightWordFile                      => "$hume_repo_root/resource/event_consolidation/common/light_words_coref.txt",
            ATOMIC                             => 1
        };
        if ($single_bert_thread_mode) {
            $pyserif_template->{SCRIPT} = 1;
            $pyserif_template->{SGE_VIRTUAL_FREE} = "28G";
            $pyserif_template->{max_memory_over} = "228G";
        }
        (my $ministage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_processing", []);
        (my $ministage_batch_dir, my $mkdir_batch_jobs) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name/batch_file", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_batch_processing", [ $pyserif_eer_list_collector_job_id ]);

        (my $create_filelist_jobid, undef
        ) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            dependant_job_ids       => $mkdir_batch_jobs,
            job_prefix              => "$JOB_NAME/$stage_name/$mini_stage_name/",
            num_of_batches          => $number_of_batches_pyserif,
            list_file_path          => $output_pyserif_eer_doc_list,
            output_file_prefix      => $ministage_batch_dir . "/batch_",
            suffix                  => ".list",
        );

        my @split_jobs = ();
        for (my $batch = 0; $batch < $number_of_batches_pyserif; $batch++) {
            my $batch_file = "$ministage_batch_dir/batch_$batch.list";
            my $batch_output_folder = "$ministage_processing_dir/$batch/output";

            if ($single_bert_thread_mode) {
                (my $ministage_scratch_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name/scratch_file/$batch", "$JOB_NAME/$stage_name/$mini_stage_name/$batch/mkdir_stage_scratch_processing", []);
                (my $basic_file_name, undef) = fileparse($dc_template);
                my $expanded_template_path = "$exp_root/etemplates/$JOB_NAME/$stage_name/$mini_stage_name/$exp-pyserif_$batch.$basic_file_name";
                my $pyserif_dep_jobid = runjobs4::runjobs(
                    $create_filelist_jobid, "$JOB_NAME/$stage_name/$mini_stage_name/pyserif_$batch",
                    $pyserif_template,
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "mkdir -p $batch_output_folder" ],
                    [ "$PYTHON3 -c pass", $dc_template ],
                    [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $AFFINITY_SCHEDULER --input_list_path $batch_file\.with_type --batch_id $batch --number_of_batches $NUM_OF_BATCHES_GLOBAL --command_prefix \"env PYTHONPATH=$nlplingo_root:$textopen_root/src/python MKL_NUM_THREADS=1 KERAS_BACKEND=tensorflow $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $textopen_root/src/python/serif/driver/pipeline_sequence.py $expanded_template_path BBN_INPUT_BATCH_FILE $batch_output_folder\" --batch_arg_name BBN_INPUT_BATCH_FILE --scratch_space $ministage_scratch_dir --number_of_jobs_from_user $NUM_OF_SCHEDULING_JOBS_FOR_NN" ]
                );
                push(@split_jobs, $pyserif_dep_jobid);
            }
            else {
                my $pyserif_dep_jobid = runjobs4::runjobs(
                    $create_filelist_jobid, "$JOB_NAME/$stage_name/$mini_stage_name/pyserif_$batch",
                    $pyserif_template,
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "mkdir -p $batch_output_folder" ],
                    [ "env PYTHONPATH=$nlplingo_root:$textopen_root/src/python " .
                        "KERAS_BACKEND=tensorflow MKL_NUM_THREADS=1 " .
                        "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $textopen_root/src/python/serif/driver/pipeline_sequence.py", $dc_template, "$batch_file\.with_type $batch_output_folder" ]
                );
                push(@split_jobs, $pyserif_dep_jobid);
            }

        }
        $output_pyserif_main_doc_list = "$ministage_processing_dir/pyserif_serifxmls_uncalibrated.list";
        $pyserif_main_list_collector_job_id = generate_file_list(\@split_jobs, "$JOB_NAME/$stage_name/$mini_stage_name/list_uncalibrate_serifxml", "$ministage_processing_dir/*/output/*.xml", $output_pyserif_main_doc_list);
        my @count_collector_jobs = ();
        push(@count_collector_jobs, $pyserif_main_list_collector_job_id);
        $word_pair_count_list = "$ministage_processing_dir/word_pair_counts.list";
        $pyserif_main_list_count_collector_job_id = generate_file_list(\@count_collector_jobs, "$JOB_NAME/$stage_name/$mini_stage_name/list_word_pair_counts", "$ministage_processing_dir/*/output/*.pkl", $word_pair_count_list);
    }

    my $output_pyserif_calibration_list;
    my $generate_aggregate_count_jobid;
    my $aggregate_count_processing_dir;
    {
        my $mini_stage_name = "generate_aggregate_count";
        ($aggregate_count_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_processing", []);

        $generate_aggregate_count_jobid = runjobs(
            [ $pyserif_main_list_count_collector_job_id ], "$JOB_NAME/$stage_name/$mini_stage_name",
            {
                BATCH_QUEUE => $LINUX_QUEUE
            },
            [ "$PYTHON3 $AGGREGATE_WORD_PAIR_COUNTS --input_list $word_pair_count_list --output_dir $aggregate_count_processing_dir" ]
        );
    }

    my $aggregate_counts = $aggregate_count_processing_dir . '/aggregate_counts.pkl';
    {
        my $mini_stage_name = "pyserif_confidence_calibration";
        my $confidence_calibrate_template = "pyserif_confidence_calibrate.par";

        my $pyserif_template = {
            BATCH_QUEUE               => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE          => "8G",
            textopen_root             => $textopen_root,
            aggregate_word_pair_count => $aggregate_counts,
            ATOMIC                    => 1
        };
        if ($single_bert_thread_mode) {
            $pyserif_template->{SCRIPT} = 1;
            $pyserif_template->{SGE_VIRTUAL_FREE} = "28G";
            $pyserif_template->{max_memory_over} = "228G";
        }
        (my $ministage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_processing", []);
        (my $ministage_batch_dir, my $mkdir_batch_jobs) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name/batch_file", "$JOB_NAME/$stage_name/$mini_stage_name/mkdir_stage_batch_processing", [ $pyserif_main_list_collector_job_id, $generate_aggregate_count_jobid ]);

        (my $create_filelist_jobid, undef
        ) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            dependant_job_ids       => $mkdir_batch_jobs,
            job_prefix              => "$JOB_NAME/$stage_name/$mini_stage_name/",
            num_of_batches          => $number_of_batches_pyserif,
            list_file_path          => $output_pyserif_main_doc_list,
            output_file_prefix      => $ministage_batch_dir . "/batch_",
            suffix                  => ".list",
        );

        my @confidence_split_jobs = ();
        for (my $batch = 0; $batch < $number_of_batches_pyserif; $batch++) {
            my $batch_file = "$ministage_batch_dir/batch_$batch.list";
            my $batch_output_folder = "$ministage_processing_dir/$batch/output";

            if ($single_bert_thread_mode) {
                (my $ministage_scratch_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$mini_stage_name/scratch_file/$batch", "$JOB_NAME/$stage_name/$mini_stage_name/$batch/mkdir_stage_scratch_processing", []);
                (my $basic_file_name, undef) = fileparse($confidence_calibrate_template);
                my $expanded_template_path = "$exp_root/etemplates/$JOB_NAME/$stage_name/$mini_stage_name/$exp-pyserif_$batch.$basic_file_name";
                my $pyserif_dep_jobid = runjobs4::runjobs(
                    $create_filelist_jobid, "$JOB_NAME/$stage_name/$mini_stage_name/pyserif_$batch",
                    $pyserif_template,
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "mkdir -p $batch_output_folder" ],
                    [ "$PYTHON3 -c pass", $confidence_calibrate_template ],
                    [ "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $AFFINITY_SCHEDULER --input_list_path $batch_file\.with_type --batch_id $batch --number_of_batches $NUM_OF_BATCHES_GLOBAL --command_prefix \"env PYTHONPATH=$nlplingo_root:$textopen_root/src/python MKL_NUM_THREADS=1 KERAS_BACKEND=tensorflow $ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $textopen_root/src/python/serif/driver/pipeline_sequence.py $expanded_template_path BBN_INPUT_BATCH_FILE $batch_output_folder\" --batch_arg_name BBN_INPUT_BATCH_FILE --scratch_space $ministage_scratch_dir --number_of_jobs_from_user $NUM_OF_SCHEDULING_JOBS_FOR_NN" ]
                );
                push(@confidence_split_jobs, $pyserif_dep_jobid);
            }
            else {
                my $pyserif_dep_jobid = runjobs4::runjobs(
                    $create_filelist_jobid, "$JOB_NAME/$stage_name/$mini_stage_name/pyserif_$batch",
                    $pyserif_template,
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "mkdir -p $batch_output_folder" ],
                    [ "env PYTHONPATH=$nlplingo_root:$textopen_root/src/python " .
                        "KERAS_BACKEND=tensorflow MKL_NUM_THREADS=1 " .
                        "$ANACONDA_ROOT/envs/$CONDA_ENV_NAME_FOR_DOC_RESOLVER/bin/python $textopen_root/src/python/serif/driver/pipeline_sequence.py", $confidence_calibrate_template, "$batch_file\.with_type $batch_output_folder" ]
                );
                push(@confidence_split_jobs, $pyserif_dep_jobid);
            }
        }
        $output_pyserif_calibration_list = "$ministage_processing_dir/pyserif_serifxmls_uncalibrated.list";
        my $list_collector_job_id = generate_file_list(\@confidence_split_jobs, "$JOB_NAME/$stage_name/$mini_stage_name/list_uncalibrate_serifxml", "$ministage_processing_dir/*/output/*.xml", $output_pyserif_calibration_list);
    }

    $GENERATED_PYSERIF_SERIFXML = $output_pyserif_calibration_list;

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
            ? $GENERATED_PYSERIF_SERIFXML
            : get_param($params, "serialization_input_serifxml_list");

    my $input_factfinder_json_file =
        get_param($params, "serialization_input_factfinder_json_file") eq "GENERATED"
            ? $GENERATED_FACTFINDER_JSON_FILE
            : get_param($params, "serialization_input_factfinder_json_file");
    my $mkdir_jobid;
    $input_metadata_file = get_param($params, "metadata_file") eq "GENERATED" ? $input_metadata_file : get_param($params, "metadata_file");
    my $awake_db = get_param($params, "serialization_input_awake_db", "NA");

    my $template_filename;
    my $ontology_flags;
    my $bbn_namespace;
    my $should_go_up_instead_of_using_backup_namespaces;
    if ($mode eq "CauseEx") {
        if (get_param($params, "serialization_also_output_jsonld", "NA") eq "True") {
            $template_filename = "kb_constructor_rdf_jsonld.par";
        }
        elsif (get_param($params,"serialization_to_unification_json","False") eq "True"){
            $template_filename = "kb_constructor_unification_json.par";
        }
        else {
            $template_filename = "kb_constructor_rdf.par";
        }
        $ontology_flags = "CAUSEEX";
        $should_go_up_instead_of_using_backup_namespaces = "false";
        $bbn_namespace = "http://graph.causeex.com/bbn#";
    }
    elsif ($mode eq "BBN") {
        $template_filename = "kb_constructor_bbn.par";
        $ontology_flags = "BBN";
    }
    elsif ($mode eq "WorldModelers") {
        $template_filename = "kb_constructor_json_ld.par";
        $ontology_flags = "WM,WM_INDICATOR";
        $should_go_up_instead_of_using_backup_namespaces = "true,false";
        $bbn_namespace = "DO_NOT_USE_BACKUP_NAMESPACE,DO_NOT_USE_BACKUP_NAMESPACE";
    }

    my $batch_job_dir = "$processing_dir/serialization_batch";
    my $copy_serifxml_jobname = "$JOB_NAME/serialize/generate_serialization_batch";
    my $copy_serifxml_jobid =
        runjobs(
            [], $copy_serifxml_jobname,
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $COPY_FILES_SCRIPT --input_serif_list $input_serifxml_list --output_dir $batch_job_dir --input_metadata_file $input_metadata_file" ]
        );
    dojobs();

    # Serialize!
    my @serialization_batches = ();
    if (is_run_mode()) {
        opendir(my $dh, $batch_job_dir);
        @serialization_batches = grep {-d "$batch_job_dir/$_" && !/^\.{1,2}$/} readdir($dh);
    }

    foreach my $batch_id (@serialization_batches) {
        my $serializer_output_dir = "$GENERATED_SERIALIZATION_DIR/$batch_id";

        my $input_batch_file_dir = "$batch_job_dir/$batch_id";
        my $ttl_output_file = "$serializer_output_dir/output";
        my $nt_output_file = "$serializer_output_dir/output";
        my $jsonld_output_file = "$serializer_output_dir/output";
        if ($mode eq "WorldModelers") {
            $jsonld_output_file = $jsonld_output_file . ".json-ld";
        }
        my $json_output_file = "$serializer_output_dir/output.json";
        my $pickle_output_file = "$serializer_output_dir/output.p";
        my $json_graph_file = "$serializer_output_dir/output.graph.json";
        my $tabular_output_file = "$serializer_output_dir/output.tsv";
        my $relation_tsv_file = "$serializer_output_dir/output.relations.tsv";
        my $unification_output_dir = "$serializer_output_dir";
        my $serialize_job_name = "$JOB_NAME/serialize/kb-$batch_id";

        #	my $grounding_cache_dir = make_output_dir("$processing_dir/grounding_cache");

        # Use robust settings for serialization
        my $batch_queue = "gale-nongale-sl6";
        my $mem = "4G";

        my $serialize_jobid =
            runjobs(
                [ $copy_serifxml_jobid ], $serialize_job_name,
                {
                    serif_accent_event_type                         => "$hume_repo_root/resource/serif_data_causeex/accent/event_types.txt",
                    event_coreference_file                          => "NULL",
                    batch_file_dir                                  => $input_batch_file_dir,
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
                    event_yaml                                      => "$internal_ontology_dir/$internal_event_ontology_yaml_filename",
                    external_ontology_flags                         => $ontology_flags,
                    should_go_up_instead_of_using_backup_namespaces => $should_go_up_instead_of_using_backup_namespaces,
                    bbn_namespace                                   => $bbn_namespace,
                    mode                                            => $mode,
                    use_compositional_ontology                      => "$use_compositional_ontology",
                    seed_milestone                                  => "SAMS",
                    seed_type                                       => "4",
                    seed_version                                    => "NEWS",
                    BATCH_QUEUE                                     => $batch_queue,
                    geoname_with_gdam_woredas                       => "$external_dependencies_root/wm/geoname_with_gdam_woredas.txt",
                    ontology_turtle_folder                          => "$hume_repo_root/resource/ontologies/causeex/200915",
                    intervention_whitelist                          => "$hume_repo_root/resource/wm/intervention_whitelist_030920.txt"
                },
                [ "mkdir -p $serializer_output_dir" ],
                [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $KB_CONSTRUCTOR_SCRIPT", $template_filename ]
            );
    }
}

dojobs();

if (exists $stages{"pipeline-statistics"}) {
    my $dump_extraction =
        get_param($params, "dump_extraction", "False");
    my $dump_serialization = get_param($params, "dump_serialization", "False");
    my $Dumper_root = "$hume_repo_root/src/python/pipeline/dumper";
    print "Pipeline Statistics stage\n";
    my $stage_name = "pipeline_statistics";
    my $mkdir_jobid;
    (my $stage_processing_dir, $mkdir_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_staging_processing", []);

    my $print_numeric_statistics_jobid = runjobs(
        [], "$JOB_NAME/$stage_name/numeric_statistics",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "env PYTHONPATH=$textopen_root/src/python:\$PYTHONPATH $PYTHON3 $Dumper_root/get_event_and_event_arg_cnt.py --expt_root $processing_dir > $stage_processing_dir/numeric_statistics.log" ]
    );
    if ($dump_extraction eq "True") {
        my $dump_grounding_jobid = runjobs(
            [], "$JOB_NAME/$stage_name/dump_grounding",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "env PYTHONPATH=$textopen_root/src/python:\$PYTHONPATH $PYTHON3 $Dumper_root/get_all_event_groundings.py --expt_root $processing_dir > $stage_processing_dir/grounding.log" ]
        );
        my $dump_event_arg_jobid = runjobs(
            [], "$JOB_NAME/$stage_name/dump_event_args",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "env PYTHONPATH=$textopen_root/src/python:\$PYTHONPATH $PYTHON3 $Dumper_root/get_all_event_argument.py --expt_root $processing_dir > $stage_processing_dir/event_arg.log" ]
        );
        my $dump_event_event_relation_jobid = runjobs(
            [], "$JOB_NAME/$stage_name/dump_event_event_relation",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "env PYTHONPATH=$textopen_root/src/python:\$PYTHONPATH $PYTHON3 $Dumper_root/get_all_event_event_relation.py --expt_root $processing_dir > $stage_processing_dir/event_event_relation.log" ]
        );
    }
    if ($dump_serialization eq "True") {
        my $serialization_dumper_script = "";
        if ($mode eq "CauseEx") {
            $serialization_dumper_script = "$hume_repo_root/src/python/misc/print_causal_relation_from_unification_json.py";
        }
        else {
            $serialization_dumper_script = "$hume_repo_root/src/python/misc/print_causal_relation_from_jsonld.py";
        }
        my $print_serialization_jobid = runjobs(
            [], "$JOB_NAME/$stage_name/dump_serialization",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $serialization_dumper_script --serialization_root $GENERATED_SERIALIZATION_DIR > $stage_processing_dir/serialization_dump.log" ]
        );
    }
}

dojobs();

if (exists $stages{"visualization"}) {
    my $input_serialization_root = get_param($params, "serialization_root") eq "GENERATED"
        ? $GENERATED_SERIALIZATION_DIR
        : get_param($params, "serialization_root");;
    my $stage_name = "visualization";
    my $mkdir_jobid;
    (my $stage_processing_dir, $mkdir_jobid) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_staging_processing", []);
    my $merge_eer_graph = runjobs(
        [], "$JOB_NAME/$stage_name/merge_eer_graph",
        {
            BATCH_QUEUE => $LINUX_QUEUE,
        },
        [ "$PYTHON3 $learnit_root/HAT/new_backend/utils/aggr_ui_data_from_kb_constructor.py --dir_of_serialization $input_serialization_root --output_path $stage_processing_dir/eer_graph.json" ]
    );

    # Event timeline data generation has been turn off
    if (0) {
        my $event_timeline_input_serifxml_list =
            get_param($params, "event_timeline_input_serifxml_list") eq "GENERATED"
                ? $GENERATED_PYSERIF_SERIFXML
                : get_param($params, "event_timeline_input_serifxml_list");
        (my $output_event_timeline_dir, undef) = Utils::make_output_dir("$processing_dir/event_timeline_output", "$JOB_NAME/event_timeline/mkdir_staging_processing", []);
        my $extract_event_timestamp_info_jobid = runjobs(
            [], "$JOB_NAME/event_timeline/1_extract_event_timestamp",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$EXTRACT_TIMELINE_FROM_SERIFXML_EXE $event_timeline_input_serifxml_list $output_event_timeline_dir/event_timeline.ljson" ]
        );
        my $group_eventmention_in_timeline_bucket = runjobs(
            [ $extract_event_timestamp_info_jobid ], "$JOB_NAME/event_timeline/2_group_into_bucket",
            {
                BATCH_QUEUE => $LINUX_QUEUE,
            },
            [ "$PYTHON3 $GROUP_EVENTMENTION_IN_TIMELINE_BUCKET_SCRIPT $output_event_timeline_dir/event_timeline.ljson > $output_event_timeline_dir/event_timeline.table" ]
        );
    }
}

dojobs();

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



sub check_requirements {

    my @required_git_repos = ();

    for my $git_repo (@required_git_repos) {
        if (!-e $git_repo) {
            die "You must have the git repo: " . $git_repo . " cloned\n";

        }

    }

    my @required_git_files = ();
    if (exists $stages{"nn-event-typing"}) {
        push(@required_git_files, "$hume_repo_root/src/java/serif-util/target/appassembler/bin/NeuralNamesModelInputOutputMapper");
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

