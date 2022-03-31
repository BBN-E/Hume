#!/usr/bin/env perl
use strict;
use warnings FATAL => 'all';

my $RUNJOBS_RELEASE_DIR = "/d4m/ears/releases/runjobs4/TMP/TMP2021_01_11.65e0fcb.set-gpus-on-gpu-queue-in-docker";
my $NLPLINGO_RELEASE_DIR = "/d4m/nlp/releases/nlplingo/R2021_03_10";
my $TEXT_OPEN_RELEASE_DIR = "/d4m/nlp/releases/text-open/R2021_03_10_1";
my $HUME_RELEASE_DIR = "/d4m/nlp/releases/Hume/R2021_03_10";
my $LEARNIT_RELEASE_DIR = "/d4m/nlp/releases/learnit/R2021_02_13";
my $SVN_PROJECT_ROOT = $ENV{"SVN_PROJECT_ROOT"};
my $SERIF_EXE = "$HUME_RELEASE_DIR/bin/Serif";
my $SERIF_DATA = "/d4m/serif/data";

my $TEXT_OPEN_PYTHONPATH = "$TEXT_OPEN_RELEASE_DIR/src/python/";

my $PRODUCTION_MODE = defined $ENV{'PRODUCTION_MODE'} ? $ENV{'PRODUCTION_MODE'} : 'false';

my $PYTHON_GPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v /nfs/raid84/u11/material/software/python/singularity/venv/python3.6-cuda10.0/covid-gpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE --gpu -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR:/nfs/raid66/u11/users/brozonoy-ad/modal_and_temporal_parsing";

my $PYTHON_CPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v better-cpu -e PRODUCTION_MODE=$PRODUCTION_MODE -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR";

return {
    input_files                       => {
        sgms_list     => "/nfs/raid66/u11/users/brozonoy-ad/text-open/src/python/test/test_mtdp_adapter/test_sgm.list",
        metadata_file => "/nfs/raid66/u11/users/brozonoy-ad/text-open/src/python/test/test_mtdp_adapter/test_file.metadata",
        awake_db      => "/nfs/raid87/u10/shared/Hume/common/serif/wm_eval_before_060119.sqlite",
        serif_list    => "/nfs/raid66/u11/users/brozonoy-ad/Hume/expts/test_pl/nlplingo_event_args/serif.list",
        #sgms_list     => "/nfs/raid88/u10/users/hqiu/raw_corpus/aylien_covid19/Aylien-202006-10p.list",
        #metadata_file => "/nfs/raid88/u10/users/hqiu/raw_corpus/aylien_covid19/metadata.txt",
        #awake_db      => "/nfs/raid87/u10/shared/Hume/common/serif/wm_eval_before_060119.sqlite",
        #serif_list    => "/d4m/ears/expts/48022.aylien_202006_10p.serif.113020/expts/hume_test.dart.082720.wm.v1/serif_serifxml.list"
        language      => "zh",
        input_type    => "txts",
        txts_list     => "/nfs/raid88/u10/users/hqiu_ad/repos/Chinese-data/from_brandeis_repo.list.20",
    },
    job_prefix                        => "mtdp",
    stages_to_run                     => [ "nlplingo_event", "nlplingo_event_args", "doctheory_resolver", "mtdp", "kb_constructor" ],
    num_of_batches                    => 100,
    max_number_of_tokens_per_sentence => 128,
    max_jobs                          => 400,
    use_gpus                          => 1, # 0 - run all jobs as cpu jobs using max_cpu_jobs, 1 - run gpu jobs
    TEXT_OPEN_RELEASE_DIR             => $TEXT_OPEN_RELEASE_DIR,
    TEXT_OPEN_PYTHONPATH              => $TEXT_OPEN_PYTHONPATH,
    NLPLINGO_RELEASE_DIR              => $NLPLINGO_RELEASE_DIR,
    HUME_RELEASE_DIR                  => $HUME_RELEASE_DIR,
    LEARNIT_RELEASE_DIR               => $LEARNIT_RELEASE_DIR,
    PYTHON_GPU                        => $PYTHON_GPU,
    PYTHON_CPU                        => $PYTHON_CPU,
    PYTHON3_SYSTEM                    => "/usr/bin/env python3",
    SERIF_EXE                         => $SERIF_EXE,
    perl_libs                         => [
        "$RUNJOBS_RELEASE_DIR/lib",
        "$TEXT_OPEN_RELEASE_DIR/src/perl/text_open/lib",
        "$NLPLINGO_RELEASE_DIR/perl_lib",
        "$LEARNIT_RELEASE_DIR/lib/perl_lib/"
    ],
    runjobs_pars                      => {
        batch_queue     => 'cpunodes-avx',
        batch_gpu_queue => 'gpu-12G', # It logically goes here but
        # isnt automatically used by runjobs
        queue_priority  => 5,
        local_dir       => "/export/u10",
        queue_mem_limit => [ '7.5G', '15.5G' ],
    },

    serif_pars                        => {
        runjobs_par => {
            par_dir                          => $SVN_PROJECT_ROOT . "/SERIF/par",
            project_specific_serif_data_root => "$HUME_RELEASE_DIR/resource/serif_data_wm",
            SERIF_DATA                       => $SERIF_DATA,
            serif_cause_effect_patterns_dir  => "$HUME_RELEASE_DIR/resource/serif_cause_effect_patterns",
            should_track_files_read          => "false",
            use_basic_cipher_stream          => "false",
            fast_mode_pars                   => "
OVERRIDE run_icews: false
OVERRIDE run_fact_finder: false
OVERRIDE max_parser_seconds: 5
"
        },
        par_file    => "serif_wm.par"
    },
    pyserif_nlp                       => {
        par_file    => {
            zh => {
                txts => "config_stanza_zh_txts"
            }
        },
        runjobs_par => {
            LANGUAGE_MODELS_DIR => "/nfs/raid87/u10/nlp"
        }
    },
    nlplingo_event                    => {
        par_file => "covid_nn_event_trigger.par"
    },
    learnit_pars                      => {
        runjobs_par => {
            stages_to_run                                    => "generic_event,unary_entity,unary_event_and_binary_event_argument_decoding,binary_event_event_decoding",
            generic_event_noun_whitelist                     => "$HUME_RELEASE_DIR/resource/generic_events/generic_event.whitelist.wn-fn.variants",
            generic_event_blacklist                          => "$HUME_RELEASE_DIR/resource/generic_events/modal_aux.verbs.list",
            unary_event_and_binary_event_argument_extractors => "$HUME_RELEASE_DIR/resource/domains/COVID/learnit/unary_event",
            binary_event_event_extractors                    => "$HUME_RELEASE_DIR/resource/domains/COVID/learnit/binary_event",
            unary_entity_extractors                          => "$HUME_RELEASE_DIR/resource/domains/COVID/learnit/unary_entity"
        }
    },
    nlplingo_event_args               => {
        par_file => "covid_nn_event_arg.par"
    },
    mtdp                              => {
        par_file => "mtdp.par"
    },
    nlplingo_eer                      => {
        par_file => "covid_nn_event_event_relation.par"
    },
    doctheory_resolver                => {
        runjobs_par => {
            hume_repo_root => $HUME_RELEASE_DIR
        },
        par_file    => "doctheory_resolver_covid.params"
    },
    kb_constructor_par                => {
        runjobs_par => {
            mode => "covid"
        },
        python      => "env PYTHONPATH=$TEXT_OPEN_PYTHONPATH:\$PYTHONPATH /nfs/raid88/u10/users/hqiu_ad/venv/kb_constructor/bin/python3"
    }

}
