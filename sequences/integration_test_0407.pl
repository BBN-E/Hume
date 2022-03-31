#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';


my $textopen_root;

BEGIN{
    $textopen_root = "/d4m/nlp/releases/text-open/R2020_04_02";
    unshift(@INC, "/d4m/ears/releases/runjobs4/R2019_03_29/lib");
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
}

use runjobs4;
use Utils;

my ($exp_root, $exp) = startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G', "queue_priority" => 5);

max_jobs(50);
my $LINUX_QUEUE = "nongale-sl6";
my $PYTHON3 = "/home/hqiu/bin/python3";
my $JOB_NAME = "hume_integration_test_wrapper_040720";

my $CREATE_FILELIST_PY_PATH = "$textopen_root/src/python/util/common/create_filelist_with_batch_size.py";
my $job_script_prefix = "/nfs/raid88/u10/users/hqiu/integration_test/040720/hume_test_cx_040720_";

{
    my $stage_name = "general_program";

    my $NUM_JOBS = 509;

    my @generic_events_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $run_script = "$job_script_prefix".$n."/run.sh";

        my $add_event_mentions_from_propositions_jobid =
            runjobs(
                [], "$JOB_NAME/$stage_name/merge_mappings_$n",
                {
                    SGE_VIRTUAL_FREE     => "32G",
                    BATCH_QUEUE          => $LINUX_QUEUE,
                },
                [ "/bin/bash $run_script"]
            );
        push(@generic_events_split_jobs, $add_event_mentions_from_propositions_jobid);
    }
}
endjobs();