#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';

use Cwd 'abs_path';

use File::Basename;
use File::Path;

use Getopt::Long;
use List::Util qw[min max];

my $textopen_root;
my $learnit_root;
my $hume_root;
BEGIN{
    $textopen_root = "/home/hqiu/ld100/text-open";
    $hume_root = Cwd::abs_path(__FILE__ . "/../..");
    unshift(@INC, abs_path(__FILE__ . "/../../sequences"));
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
    unshift(@INC, "/d4m/ears/releases/runjobs4/R2019_03_29/lib");
}

use runjobs4;
use Utils;

my $PYTHON3 = "/home/hqiu/ld100/miniconda_dev/envs/pyserif-cpu/bin/python3";
my $CREATE_FILE_LIST_SCRIPT = "$textopen_root/src/python/util/common/create_filelist_with_batch_size.py";


my ($expt_dir, $exp) = runjobs4::startjobs("queue_mem_limit" => '7G', "max_memory_over" => '0.5G');
runjobs4::max_jobs(200);
my $QUEUE = "nongale-sl6";
my $job_prefix = "gigaword_eer_json";
my $number_of_batches = 1000;
my $output_dir = "$expt_dir/expts/$job_prefix";
my $input_serif_list = "/home/hqiu/tmp/all.txt";

(my $mappings_dir, undef) = Utils::make_output_dir("$output_dir", "$job_prefix/mkdir", []);
(my $mappings_batch_dir, my $mkdir_batch_dir_jobid) = Utils::make_output_dir("$output_dir/batch", "$job_prefix/mkdir_batch", []);

my (
    $create_filelist_jobid, @file_list_at_disk
) = Utils::split_file_list_with_num_of_batches(
    PYTHON                  => $PYTHON3,
    CREATE_FILELIST_PY_PATH => $CREATE_FILE_LIST_SCRIPT,
    dependant_job_ids       => $mkdir_batch_dir_jobid,
    job_prefix              => "$job_prefix" . "/create_batch",
    num_of_batches          => $number_of_batches,
    list_file_path          => $input_serif_list,
    output_file_prefix      => $mappings_batch_dir . "/batch_",
    suffix                  => ".list",
);
my @decoding_split_jobs = ();
for (my $batch = 0; $batch < $number_of_batches; $batch++) {
    my $batch_file = "$mappings_batch_dir/batch_$batch.list";
    my $batch_job_prefix = "$job_prefix/decoding_$batch";
    my ($batch_output_dir, $mkdir_batch_jobid) = Utils::make_output_dir("$output_dir/decoding/$batch", "$batch_job_prefix/mkdir_batch", $create_filelist_jobid);
    my ($batch_serifxml_output_dir, $mkdir_serifxml_batch_jobid) = Utils::make_output_dir("$batch_output_dir/serifxmls", "$batch_job_prefix/mkdir_serifxml_batch", $create_filelist_jobid);
    my $MEM_LIMIT = "16G";
    my $learnit_decoder_jobid = runjobs4::runjobs(
        $mkdir_batch_jobid,
        $batch_job_prefix . "/learnit_decoder",
        {
            BATCH_QUEUE      => $QUEUE,
            SGE_VIRTUAL_FREE => $MEM_LIMIT
        },
        [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $hume_root/src/python/misc/eer_json_to_serifxml_cold_start.py --input_list $batch_file --seq_num $batch --output_dir $batch_serifxml_output_dir" ]
    );
    push(@decoding_split_jobs, $learnit_decoder_jobid);
}

runjobs4::dojobs();
runjobs4::endjobs();

1;
