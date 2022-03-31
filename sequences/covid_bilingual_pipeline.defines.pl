#!/usr/bin/env perl
use strict;
use warnings FATAL => 'all';

my $RUNJOBS_RELEASE_DIR = "/d4m/ears/releases/runjobs4/TMP/TMP2021_01_11.65e0fcb.set-gpus-on-gpu-queue-in-docker";
my $NLPLINGO_RELEASE_DIR = "/d4m/nlp/releases/nlplingo/R2021_10_12";
my $NLPLINGO_RELEASE_DIR_EER = "/d4m/nlp/releases/nlplingo/R2021_06_26";
my $TEXT_OPEN_RELEASE_DIR = "/nfs/raid88/u10/users/hqiu_ad/repos/text-open"; #"/d4m/nlp/releases/text-open/R2021_10_27_1"; #"/d4m/nlp/releases/text-open/R2021_10_15";
my $TEXT_OPEN_RELEASE_DIR_EER = "/d4m/nlp/releases/text-open/R2021_07_22";
my $HUME_RELEASE_DIR = "/nfs/raid88/u10/users/hqiu_ad/repos/Hume";
# my $HUME_RELEASE_DIR = "/nfs/raid66/u11/users/brozonoy-ad/Hume";#"/d4m/nlp/releases/Hume/R2021_10_15";
#my $HUME_RELEASE_DIR = Cwd::abs_path(__FILE__ . "/../..");
my $LEARNIT_RELEASE_DIR = "/d4m/nlp/releases/learnit/R2021_10_26";
my $HYCUBE_RELEASE_DIR = "/d4m/material/releases/hycube/R2021_10_15";
my $CUBE_PM_RELEASE_DIR = "$HYCUBE_RELEASE_DIR/cubepm";
my $PYCUBE_RELEASE_DIR = "$HYCUBE_RELEASE_DIR/pycube";
my $FAIRSEQ_RELEASE_DIR = "/d4m/material/releases/fairseq/R2021_08_03";
my $BETTER_RELEASE_DIR = "/d4m/better/releases/better/R2021_05_12";

my $TEXT_OPEN_PYTHONPATH = "$TEXT_OPEN_RELEASE_DIR/src/python/";
my $TEXT_OPEN_PYTHONPATH_EER = "$TEXT_OPEN_RELEASE_DIR_EER/src/python/";

my $PRODUCTION_MODE = defined $ENV{'PRODUCTION_MODE'} ? $ENV{'PROD`UCTION_MODE'} : 'false';

my $PYTHON_GPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v /nfs/raid84/u11/material/software/python/singularity/venv/python3.6-cuda10.0/covid-gpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE --gpu -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR:$FAIRSEQ_RELEASE_DIR:$PYCUBE_RELEASE_DIR:$BETTER_RELEASE_DIR:/nfs/raid66/u11/users/brozonoy-ad/modal_and_temporal_parsing:/nfs/raid66/u11/users/brozonoy-ad/sutime-site-packages:/nfs/raid66/u11/users/brozonoy-ad/python-heideltime";
my $PYTHON_CPU_ALLENNLP = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v /nfs/raid84/u11/material/software/python/singularity/.venv.stage/python3.6-cuda10.0/pyserif-gpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e OMP_NUM_THREADS=1 -l $TEXT_OPEN_PYTHONPATH:/nfs/raid87/u10/nlp/spacy";
my $PYTHON_GPU_NLPLINGO = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v /nfs/raid84/u11/material/software/python/singularity/venv/python3.6-cuda10.0/covid-gpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE --gpu -l $TEXT_OPEN_PYTHONPATH_EER:$NLPLINGO_RELEASE_DIR_EER";

my $PYTHON_CPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v better-cpu -e PRODUCTION_MODE=$PRODUCTION_MODE -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR:$FAIRSEQ_RELEASE_DIR:$PYCUBE_RELEASE_DIR:$BETTER_RELEASE_DIR:/nfs/raid66/u11/users/brozonoy-ad/modal_and_temporal_parsing";

my $PYTHON_CPU_SPACY = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v /nfs/raid84/u11/material/software/python/singularity/venv/python3.6-cuda10.0/covid-gpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR:$FAIRSEQ_RELEASE_DIR:$PYCUBE_RELEASE_DIR:$BETTER_RELEASE_DIR";

my $MT_PYTHON_CPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v pytorch1.5-cpu -e PRODUCTION_MODE=$PRODUCTION_MODE -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR:$FAIRSEQ_RELEASE_DIR:$PYCUBE_RELEASE_DIR:$BETTER_RELEASE_DIR:/nfs/raid66/u11/users/brozonoy-ad/modal_and_temporal_parsing";
my $MT_PYTHON_GPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v pytorch1.5-gpu --gpu -e PRODUCTION_MODE=$PRODUCTION_MODE -l $TEXT_OPEN_PYTHONPATH:$NLPLINGO_RELEASE_DIR:$FAIRSEQ_RELEASE_DIR:$PYCUBE_RELEASE_DIR:$BETTER_RELEASE_DIR:/nfs/raid66/u11/users/brozonoy-ad/modal_and_temporal_parsing";

my $COREF_RELEASE_DIR = "/d4m/nlp/releases/coref/R2020_11_12_2";
my $UWCOREF_PYTHON_CPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v better-cpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e OMP_NUM_THREADS=1 -l $TEXT_OPEN_PYTHONPATH:$COREF_RELEASE_DIR";

return {
    input_files                       => {
        en      => {
            type           => "sgms",
            file_list      => "/d4m/ears/expts/48311.iarpa_final_demo.entity_linking.v1/expts/iarpa-covid-demo/entity_linking/en/serif.list",
            num_of_batches => 2400,
            metadata       => "/nfs/raid88/u10/users/hqiu/raw_corpus/aylien_covid19/metadata.txt"
        },
        zh_hans => {
            type                  => "sgms",
            file_list             => "/d4m/ears/expts/48311.iarpa_final_demo.entity_linking.v1/expts/iarpa-covid-demo/entity_linking/cn/serif.list",
            num_of_batches        => 2400,
            metadata              => "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/covid/chinese_news_vol2_sgms/metadata.txt",
            en_serif_list_from_en => undef, # Reserved field if you want to run bilingual LearnIt and skip MT
            mt_json_filelist      => undef, # Reserved field if you want to run bilingual LearnIt and skip MT
        }
    },
    job_prefix                        => "iarpa-covid-demo",
    stages_to_run                     => [ "special_pyserif_stage", "kb_constructor" ],
    max_number_of_tokens_per_sentence => 128,
    max_jobs                          => 400,
    use_gpus                          => 1, # 0 - run all jobs as cpu jobs using max_cpu_jobs, 1 - run gpu jobs
    TEXT_OPEN_RELEASE_DIR             => $TEXT_OPEN_RELEASE_DIR,
    TEXT_OPEN_PYTHONPATH              => $TEXT_OPEN_PYTHONPATH,
    TEXT_OPEN_RELEASE_DIR_EER         => $TEXT_OPEN_RELEASE_DIR_EER,
    TEXT_OPEN_PYTHONPATH_EER          => $TEXT_OPEN_PYTHONPATH_EER,
    NLPLINGO_RELEASE_DIR              => $NLPLINGO_RELEASE_DIR,
    HUME_RELEASE_DIR                  => $HUME_RELEASE_DIR,
    LEARNIT_RELEASE_DIR               => $LEARNIT_RELEASE_DIR,
    BETTER_RELEASE_DIR                => $BETTER_RELEASE_DIR,
    CUBE_PM_RELEASE_DIR               => $CUBE_PM_RELEASE_DIR,
    PYCUBE_RELEASE_DIR                => $PYCUBE_RELEASE_DIR,
    FAIRSEQ_RELEASE_DIR               => $FAIRSEQ_RELEASE_DIR,
    PYTHON_GPU                        => $PYTHON_GPU,
    PYTHON_CPU_ALLENNLP               => $PYTHON_CPU_ALLENNLP,
    PYTHON_GPU_NLPLINGO               => $PYTHON_GPU_NLPLINGO,
    PYTHON_CPU                        => $PYTHON_CPU,
    PYTHON_CPU_SPACY                  => $PYTHON_CPU_SPACY,
    MT_PYTHON_CPU                     => $MT_PYTHON_CPU,
    MT_PYTHON_GPU                     => $MT_PYTHON_GPU,
    UWCOREF_PYTHON_CPU                => $UWCOREF_PYTHON_CPU,
    PYTHON3_SYSTEM                    => "/usr/bin/env python3",
    perl_libs                         => [
        "$RUNJOBS_RELEASE_DIR/lib",
        "$TEXT_OPEN_RELEASE_DIR/src/perl/text_open/lib",
        "$NLPLINGO_RELEASE_DIR/perl_lib",
        "$LEARNIT_RELEASE_DIR/lib/perl_lib/",
        "$HYCUBE_RELEASE_DIR/cubepm/lib",
    ],
    runjobs_pars                      => {
        batch_queue     => 'cpunodes-avx',
        batch_gpu_queue => 'gpu-12G', # It logically goes here but
        # isnt automatically used by runjobs
        queue_priority  => 4,
        local_dir       => "/export/u10",
        queue_mem_limit => [ '7.5G', '15.5G', '31.5G' ],
    },

    pyserif_nlp                       => {
        par_file    => {
            zh => {
                txts => "config_stanza_zh_txts",
                sgms => "config_stanza_zh_sgms"
            },
            en => {
                txts               => "config_stanza_en_txts",
                mtjsons            => "config_stanza_en_mtjsons",
                sgms               => "config_stanza_en_sgms",
                sgms_lightweight   => "config_stanza_en_sgms_lightweight",
                serifxmls_depparse => "config_stanza_en_serifxmls_depparse"
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
        runjobs_par                        => {
            stages_to_run                                    => "generic_event,unary_entity,unary_event_and_binary_event_argument_decoding,binary_event_event_decoding",
            generic_event_noun_whitelist                     => "$HUME_RELEASE_DIR/resource/generic_events/generic_event.whitelist.wn-fn.variants",
            generic_event_blacklist                          => "$HUME_RELEASE_DIR/resource/generic_events/modal_aux.verbs.list",
            unary_event_and_binary_event_argument_extractors => "$HUME_RELEASE_DIR/resource/domains/COVID/learnit/unary_event",
            binary_event_event_extractors                    => "$HUME_RELEASE_DIR/resource/domains/COVID/learnit/binary_event",
            unary_entity_extractors                          => "$HUME_RELEASE_DIR/resource/domains/COVID/learnit/unary_entity"
        },
        run_mt_and_jserif_compliance_stage => 1
    },
    throw_out_of_ontology_events      => {
        runjobs_par => {
            hume_repo_root => $HUME_RELEASE_DIR
        },
        par_file    => "doctheory_resolver_covid_p1.params"
    },
    nlplingo_event_args               => {
        par_file => {
            en => "covid_en_nn_event_arg.par",
            zh => "covid_zh_nn_event_arg.par",
        }
    },
    nmt_pars                          => {
        model_dir       =>
            "/d4m/ears/expts/48139.zho_bi_falign_v30k_notag.wikidata.20211014/expts/fairseq-train",
        checkpoint_path =>
            "/d4m/ears/expts/48139.zho_bi_falign_v30k_notag.wikidata.20211014/expts/fairseq-train/checkpoint_best.pt",
    },
    mtdp                              => {
        par_file => "mtdp.par"
    },
    entity_coreference                => {
        par_file    => {
            en => "covid_en_nn_entity_coref.par",
            zh => "covid_zh_nn_entity_coref.par",
        },
        runjobs_par => {
            ALLENNLP_DIR => "/nfs/raid87/u10/nlp"
        }

    },
    entity_linking                    => {
        par_file => {
            en => "covid_en_entity_linking.par",
            zh => "covid_zh_entity_linking.par",
        }
    },
    nlplingo_eer                      => {
        par_file => "covid_nn_event_event_relation.par"
    },
    doctheory_resolver                => {
        runjobs_par => {
            en => { hume_repo_root => $HUME_RELEASE_DIR, pattern_file_name => "pruning-patterns-en.sexp" },
            cn => { hume_repo_root => $HUME_RELEASE_DIR, pattern_file_name => "pruning-patterns-cn.sexp" }
        },
        par_file    => "doctheory_resolver_covid_p2.params"
    },
    kb_constructor_par                => {
        runjobs_par         => {
            mode => "covid"
        },
        par_file            => "kb_constructor_covid_pyserif.par",
        python              => "env PYTHONPATH=$TEXT_OPEN_PYTHONPATH:\$PYTHONPATH /nfs/raid88/u10/users/hqiu_ad/venv/kb_constructor/bin/python3",
        serialize_fillables => 0
    },
    jserif_compatible_par             => {
        par_file => "config_jserif_cleaner.par"
    },
    special_pyserif_stage             => {
        par_file => {
            en => "covid_special_pyserif_v1.par",
            zh => "covid_special_pyserif_v1.par"
        }
    }

}
