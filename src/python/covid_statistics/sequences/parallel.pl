package runjobs_mapping_quick;
use strict;
use warnings FATAL => 'all';

use Cwd 'abs_path';
my $textopen_root;
my $hume_repo_root;
BEGIN{
    $textopen_root = "/nfs/raid88/u10/users/hqiu_ad/repos/text-open";
    $hume_repo_root = abs_path(__FILE__ . "/../../../../../");;
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
    unshift(@INC, "/d4m/ears/releases/runjobs4/R2019_03_29/lib");
}

use runjobs4;
use constants;
use Utils;

# my $learnit_root = abs_path(__FILE__ . "/../../");

my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G', "queue_priority" => $QUEUE_PRIO);
max_jobs(500);
my $LINUX_QUEUE = "cpunodes";

### Please Change this
my $JOB_NAME = "covid_statistics_collection";
my $NUMBER_OF_BATCHES = 2000;
my $input_cord19_list = "/d4m/ears/expts/48076.cord19.full.021621.v1/expts/test_pl/doctheory_resolver/serif.list";
my $input_aylien_list = "/d4m/ears/expts/48076.aylien.full.021621.v1/expts/test_pl/doctheory_resolver/serif.list";
(my $processing_dir, undef) = Utils::make_output_dir("$exp_root/expts/$JOB_NAME", "$JOB_NAME/mkdir_output", []);
### End please Change this

{
    my $stage_name = "covid_statistics_collection";
    (my $stage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_output", []);
    {
        (my $cord19_batch_file_directory, undef) = Utils::make_output_dir("$stage_processing_dir/cord19_processing/cord19_batch", "$JOB_NAME/$stage_name/cord19_processing/mkdir_output_batch", []);
        my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => "env python3",
            CREATE_FILELIST_PY_PATH => "$textopen_root/src/python/util/common/create_filelist_with_batch_size.py",
            num_of_batches          => $NUMBER_OF_BATCHES,
            suffix                  => "",
            output_file_prefix      => "$stage_processing_dir/cord19_processing/cord19_batch/",
            list_file_path          => $input_cord19_list,
            job_prefix              => "$JOB_NAME/$stage_name/cord19_processing/cord19_batch/",
            dependant_job_ids       => [],
        );
        for (my $n = 0; $n < $NUMBER_OF_BATCHES; $n++) {
            my $batch_file = $batch_files[$n];
            my $output_serifxml_dir = "$stage_processing_dir/cord19_processing/$n/output";
            my $jobid1 =
                runjobs(
                    $split_jobid, "$JOB_NAME/$stage_name/cord19_processing/$n/processing_1",
                    {
                        SGE_VIRTUAL_FREE => "4G",
                        BATCH_QUEUE      => $LINUX_QUEUE,
                    },
                    [ "mkdir -p $output_serifxml_dir" ],
                    [ "env PYTHONPATH=$textopen_root/src/python python3 $hume_repo_root/src/python/covid_statistics/eer_analysis.py untyped $batch_file $output_serifxml_dir/untyped_eer.dump" ],
                    [ "env PYTHONPATH=$textopen_root/src/python python3 $hume_repo_root/src/python/covid_statistics/eer_analysis.py both_end_typed $batch_file $output_serifxml_dir/both_end_typed.dump" ]
                );
        }
    }

    {
        (my $aylien_batch_file_directory, undef) = Utils::make_output_dir("$stage_processing_dir/aylien_processing/aylien_batch", "$JOB_NAME/$stage_name/aylien_processing/mkdir_output_batch", []);
        my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => "env python3",
            CREATE_FILELIST_PY_PATH => "$textopen_root/src/python/util/common/create_filelist_with_batch_size.py",
            num_of_batches          => $NUMBER_OF_BATCHES,
            suffix                  => "",
            output_file_prefix      => "$stage_processing_dir/aylien_processing/aylien_batch/",
            list_file_path          => $input_aylien_list,
            job_prefix              => "$JOB_NAME/$stage_name/aylien_processing/aylien_batch/",
            dependant_job_ids       => [],
        );
        for (my $n = 0; $n < $NUMBER_OF_BATCHES; $n++) {
            my $batch_file = $batch_files[$n];
            my $output_serifxml_dir = "$stage_processing_dir/aylien_processing/$n/output";
            my $jobid1 =
                runjobs(
                    $split_jobid, "$JOB_NAME/$stage_name/aylien_processing/$n/processing_1",
                    {
                        SGE_VIRTUAL_FREE => "4G",
                        BATCH_QUEUE      => $LINUX_QUEUE,
                    },
                    [ "mkdir -p $output_serifxml_dir" ],
                    [ "env PYTHONPATH=$textopen_root/src/python python3 $hume_repo_root/src/python/covid_statistics/event_analysis.py $batch_file $output_serifxml_dir/event.dump" ]
                );
        }
    }

}
endjobs();

1;