package runjobs_mapping_quick;
use strict;
use warnings FATAL => 'all';

use Cwd 'abs_path';
my $textopen_root;
my $hume_repo_root;
BEGIN{
    $textopen_root = "/nfs/ld100/u10/hqiu/text-open";
    $hume_repo_root = abs_path(__FILE__ . "/../../");
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
    unshift(@INC, "/d4m/ears/releases/runjobs4/R2019_03_29/lib");
}

use runjobs4;
use constants;
use Utils;

my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G', "queue_priority" => $QUEUE_PRIO);
max_jobs(100);
my $LINUX_QUEUE = "cpunodes";

### Please Change this
my $JOB_NAME = "covid_canonical_name";
my $BATCH_SIZE = 1000;
my $input_mappings_list = "/home/hqiu/tmp/doc.list";
(my $processing_dir,undef) = Utils::make_output_dir("$exp_root/expts/$JOB_NAME","$JOB_NAME/mkdir_output",[]);
### End please Change this


{
    my $stage_name = "generic_event";
    (my $stage_processing_dir,undef) = Utils::make_output_dir("$processing_dir/$stage_name","$JOB_NAME/$stage_name/mkdir_output",[]);
    (my $batch_file_directory,undef) = Utils::make_output_dir("$stage_processing_dir/batch_files","$JOB_NAME/$stage_name/mkdir_output_batch",[]);
    (my $output_file_directory,undef) = Utils::make_output_dir("$stage_processing_dir/output_files","$JOB_NAME/$stage_name/mkdir_output_output",[]);

    my ($NUM_JOBS, $split_generic_events_jobid) = Utils::split_file_for_processing("$JOB_NAME/$stage_name/make_batch_files", $input_mappings_list, "$batch_file_directory/batch_file_", $BATCH_SIZE);
    my @generic_events_split_jobs = ();

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$batch_file_directory/batch_file_$job_batch_num";
        my $output_file = "$output_file_directory/batch_file_$job_batch_num";
        my $add_event_mentions_from_propositions_jobid =
            runjobs(
                [ $split_generic_events_jobid ], "$JOB_NAME/$stage_name/generic_event_$job_batch_num",
                {
                    SGE_VIRTUAL_FREE     => "8G",
                    BATCH_QUEUE          => $LINUX_QUEUE,
                },
                [ "env PYTHONPATH=$textopen_root/src/python:\$PYTHONPATH python3 $hume_repo_root/src/python/misc/print_all_event_arguments_location_canonical_name_from_serifxml.py $batch_file $output_file"]
            );
        push(@generic_events_split_jobs, $add_event_mentions_from_propositions_jobid);
    }
}
endjobs();

1;