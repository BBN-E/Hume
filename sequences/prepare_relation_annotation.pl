#!/bin/env perl
#
# SERIF Run ExperimentBuild Experiment
# Copyright (C) 2014 BBN Technologies
use strict;
use warnings;
use Getopt::Long;
use File::Basename;
use FindBin qw($Bin);
use lib "/d4m/ears/releases/Cube2/R2015_08_03_2/install-optimize-static/perl_lib/";
use runjobs4;
use File::PathConvert;
use File::Basename;
use Getopt::Long;
use Cwd;
use ParameterFiles;

## global variables
our $path_convert = (sub {shift;});
our $path_convert_unix_to_win = \&File::PathConvert::unix2win;
#

package main;

main();

# TODO
# 1.
#

sub main {
	if (!defined($ENV{SGE_ROOT})) {
		print "WARNING: SGE_ROOT not defined; using a default value!\n";
		$ENV{SGE_ROOT} = "/opt/sge-6.2u5";
	}

	# Command-line arguments:
	our $PARAMS;

	# handle parameters
	Getopt::Long::Configure("pass_through");
	GetOptions(
			"params=s"	=> \$PARAMS,
		  );
	Getopt::Long::Configure("no_pass_through");
	my $PERL="/opt/perl-5.14.1-x86_64/bin/perl";

	defined( $PARAMS ) || usage();
	print "Using param file $PARAMS\n";
	my $params = ParameterFiles::load_param_file($PARAMS);
	
	####### START RUNJOBS ###########
	my ($expt_dir, $exp) = startjobs();
	max_jobs(300);  # Max number of jobs to run at once
	
	my $job_prefix = $params->{"job_prefix"};
	
	my $sub_job_prefix = $job_prefix."/serif/";
	my $sub_job_directory = $expt_dir."/expts/".$sub_job_prefix;
	
	# run_serif($sub_job_prefix, $sub_job_directory, $params);
	print("========== stage: C++ SERIF ==========\n");
	print("expt_dir=".$expt_dir."\n");
	print("exp=".$exp."\n");
	print("sub_job_prefix=".$sub_job_prefix."\n");
	print("sub_job_directory=".$sub_job_directory."\n");
	my $list_serif_xml_output=run_serif($sub_job_prefix, $sub_job_directory, $params);
	print("===== C++ SERIF Output: list_serif_xml_output=".$list_serif_xml_output);

	endjobs();
	exit 0;

    print("========== stage: trigger finder step 1 ==========\n");
	$sub_job_prefix = $job_prefix."/trigger-finder-step1/";
	$sub_job_directory = $expt_dir."/expts/".$sub_job_prefix;
	run_trigger_finder($sub_job_prefix, $sub_job_directory, $params, $list_serif_xml_output);
	#print("===== pattern_relation_decoder, Output: list_serif_xml_output=".$list_serif_xml_output."\n");

    # $sub_job_prefix = $job_prefix."/generate-trigger-list/";
	#run_on_queue_now_local($sub_job_prefix, "setup/generate_trigger_list_by_freq", "4G",
	#    "cat /nfs/ld100/u10/bmin/repositories/CauseEx/expts/causeex_m3_and_wm_starter.v1/serif/output/batch*/output/*.triggers|awk '{print $1}'|sort|uniq -c|sort -r -n > /nfs/ld100/u10/bmin/repositories/CauseEx/expts/causeex_m3_and_wm_starter.v1/list_all_triggers",
	#    $QUEUE, $QUEUE_PRIORITY);
    # ## THEN MANUALLY annotate list_all_triggers -> list_bad_triggers
    # ## ADD into EventTriggerFinder


    print("========== stage: trigger finder step 2 ==========\n");
	$sub_job_prefix = $job_prefix."/trigger-finder-step2/";
	$sub_job_directory = $expt_dir."/expts/".$sub_job_prefix;
	run_trigger_finder($sub_job_prefix, $sub_job_directory, $params, $list_serif_xml_output);

	endjobs();
}


sub run_trigger_finder{
	my $sub_job_prefix=shift;
    my $sub_job_directory=shift;
    my $params=shift;
	my $listInputSerifXmls=shift;

	my $QUEUE=$params->{"queue"};
    my $QUEUE_PRIORITY=$params->{"queue_priority"};

	my $batch_size=5;

	my $script_trigger_finder = "/nfs/ld100/u10/bmin/repositories/CauseEx/templates/run_trigger_finding.sh";

	my $batch_list_dir = $sub_job_directory."/batches/";
	run_on_queue_now_local($sub_job_prefix, "setup/mkdir_batches", "4G", "mkdir -p $batch_list_dir", $QUEUE, $QUEUE_PRIORITY);

    print("splitting...\n");

	run_on_queue_now_local($sub_job_prefix, "setup/split_serifxml_list_into_batches", "4G", "split -d -a 6 -l $batch_size $listInputSerifXmls $batch_list_dir/batch", $QUEUE, $QUEUE_PRIORITY);

    print("Apply trigger finder onto batches ... \n");

    my @batch_lists = glob "$batch_list_dir/*";
    foreach my $batch_list (@batch_lists) {
            my ($batch_name,$batch_dir) = fileparse($batch_list);
            my $batch_file_str=&$path_convert("$batch_list");

            my $job_name=$sub_job_prefix."/trigger_finder_step1/run_on_".$batch_name;


            my $processjob = runjobs([],
                    $job_name,
                    {
                        BATCH_QUEUE => $QUEUE,
                        QUEUE_PRIO => $QUEUE_PRIORITY,
                        SGE_VIRTUAL_FREE => "16G",
                        inputFileList => $batch_list,
                    }, "/bin/bash", $script_trigger_finder);

    }

    dojobs();
}
	

sub run_serif{
	my $sub_job_prefix=shift;
	my $sub_job_directory=shift;
	my $params=shift;

	my $QUEUE=$params->{"queue"};
	my $QUEUE_PRIORITY=$params->{"queue_priority"};

	my $SERIF_START_STAGE=$params->{"serif_start_stage"};
	my $SERIF_END_STAGE=$params->{"serif_end_stage"};
	my $ENTITY_LINKING_MODE=$params->{"entity_linking_mode"};

	my $doclist=$params->{"doclist"};

	my $batch_size=10;

	my $source_format = 'sgm';
        #my $source_format = 'txt';

	my $SERIF=$params->{"serif_bin"};
	my $PAR=$params->{"serif_par"};

	my $batch_list_dir = $sub_job_directory."/batches/";
	my $serif_output_dir=$sub_job_directory."/output/";
	run_on_queue_now_local($sub_job_prefix, "setup/mkdir_batches", "4G", "mkdir -p $batch_list_dir", $QUEUE, $QUEUE_PRIORITY);
	run_on_queue_now_local($sub_job_prefix, "setup/mkdir_output", "4G", "mkdir -p $serif_output_dir", $QUEUE, $QUEUE_PRIORITY);

	print("splitting...\n");

	run_on_queue_now_local($sub_job_prefix, "setup/split_doclist_into_batches", "4G", "split -d -a 6 -l $batch_size $doclist $batch_list_dir/batch", $QUEUE, $QUEUE_PRIORITY);

	print("SERIF processing... \n");

	my @batch_lists = glob "$batch_list_dir/*";
	foreach my $batch_list (@batch_lists) {
		my ($batch_name,$batch_dir) = fileparse($batch_list);

		my $batch_file_str=&$path_convert("$batch_list");
		my $serif_path=&$path_convert("$SERIF");

		my $experiment_dir=$serif_output_dir."/".$batch_name;

		my $job_name=$sub_job_prefix."/serif/".$SERIF_START_STAGE."-".$SERIF_END_STAGE."_".$batch_name;

        my $input_type_str = "";
        my $doc_reader_regions_to_process = "TEXT,TURN,SPEAKER,POST,POSTER,POSTDATE,SUBJECT,HEADLINE,DATELINE";
        my $entity_linking_mode = $ENTITY_LINKING_MODE;

		my $processjob = runjobs([],
                        $job_name,
                        {
                        BATCH_QUEUE => $QUEUE,
                        QUEUE_PRIO => $QUEUE_PRIORITY,
                        SGE_VIRTUAL_FREE => "16G",
                        project_dir => &$path_convert("$experiment_dir"),
                        batch_file => $batch_file_str,
                        experiment_dir => $experiment_dir,
                        serif_start_stage => $SERIF_START_STAGE,
                        serif_end_stage => $SERIF_END_STAGE,
                        source_format => $source_format,
                        input_type_str => $input_type_str,,
                        doc_reader_regions_to_process => $doc_reader_regions_to_process,
                        entity_linking_mode => $entity_linking_mode,
                        }, $serif_path, $PAR);

	}

	dojobs();

	my $list_serif_xml_output=$sub_job_directory."/list_serif_xml_output.txt";
        run_on_queue_now_local($sub_job_prefix, "generate_output_serif_xml_list", "4G", "find $serif_output_dir/*/output/*.xml > $list_serif_xml_output", $QUEUE, $QUEUE_PRIORITY);

	return $list_serif_xml_output;
}


sub run_on_queue_now_local {
	(
	 my $job_prefix,
	 my $job_name,
	 my $sge_vm_free,
	 my $command, 
	 my $QUEUE,
	 my $QUEUE_PRIORITY
	) = @_;

	runjobs([],"$job_prefix/$job_name", {BATCH_QUEUE => $QUEUE, QUEUE_PRIO => $QUEUE_PRIORITY, SGE_VIRTUAL_FREE => "$sge_vm_free"}, $command);
	dojobs();
}


1;
