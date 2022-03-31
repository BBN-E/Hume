#!/usr/bin/env perl
use strict;
use warnings FATAL => 'all';

my $RUNJOBS_RELEASE_DIR = "/d4m/ears/releases/runjobs4/TMP/TMP2021_01_11.65e0fcb.set-gpus-on-gpu-queue-in-docker";
my $TEXT_OPEN_RELEASE_DIR = "/d4m/nlp/releases/text-open/R2021_07_09_2";
my $TEXT_OPEN_PYTHONPATH = "$TEXT_OPEN_RELEASE_DIR/src/python/";
my $HUME_RELEASE_DIR = "/d4m/nlp/releases/Hume/R2021_07_07";

my $PRODUCTION_MODE = defined $ENV{'PRODUCTION_MODE'} ? $ENV{'PRODUCTION_MODE'} : 'false';

my $PYTHON_GPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v /nfs/raid84/u11/material/software/python/singularity/venv/python3.6-cuda10.0/covid-gpu -e KERAS_BACKEND=tensorflow -e PRODUCTION_MODE=$PRODUCTION_MODE --gpu -l $TEXT_OPEN_PYTHONPATH";

my $PYTHON_CPU = "/d4m/material/software/python/singularity/bin/singularity-python.sh -i python3.6-cuda10.0 -v better-cpu -e PRODUCTION_MODE=$PRODUCTION_MODE -l $TEXT_OPEN_PYTHONPATH";

return {
    input_list                        => "/d4m/ears/expts/48158.070821.all_cn_commoncrawl_vol1.v1/expts/time-modules/nlplingo_eer/cn/serif.list",
    job_prefix                        => "pyserif_fix",
    max_number_of_tokens_per_sentence => 128,
    max_jobs                          => 400,
    num_of_batches                    => 50,
    use_gpus                          => 0, # 0 - run all jobs as cpu jobs using max_cpu_jobs, 1 - run gpu jobs
    TEXT_OPEN_RELEASE_DIR             => $TEXT_OPEN_RELEASE_DIR,
    TEXT_OPEN_PYTHONPATH              => $TEXT_OPEN_PYTHONPATH,
    HUME_RELEASE_DIR                  => $HUME_RELEASE_DIR,
    PYTHON_GPU                        => $PYTHON_GPU,
    PYTHON_CPU                        => $PYTHON_CPU,
    PYTHON3_SYSTEM                    => "/usr/bin/env python3",
    perl_libs                         => [
        "$RUNJOBS_RELEASE_DIR/lib",
        "$TEXT_OPEN_RELEASE_DIR/src/perl/text_open/lib",
    ],
    runjobs_pars                      => {
        batch_queue     => 'cpunodes-avx',
        batch_gpu_queue => 'gpu-12G', # It logically goes here but
        # isnt automatically used by runjobs
        queue_priority  => 5,
        local_dir       => "/export/u10",
        queue_mem_limit => [ '7.5G', '15.5G', '23.5G' ],
    },
    pyserif_fix                       => {
        par_file => "fix_actor_entity_and_entity_mention.par"
    },


}
