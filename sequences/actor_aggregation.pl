#!/bin/env perl

#
# Requirements:
# pip3 install 'pg8000==1.10.5' --user
#

use strict;
use warnings;

use lib "/d4m/ears/releases/runjobs4/R2019_03_29/lib";
use runjobs4;

use Cwd 'abs_path';
use File::Path;

package main;

my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G');

my $PYTHON3 = "/opt/Python-3.5.2-x86_64/bin/python3.5 -u";
my $hume_repo_root = abs_path("$exp_root");
my $LINUX_QUEUE = "nongale-sl6";

# Inputs
my $job_name = "actor_aggregation/sams_full_run_2";
my $awake_db_name = "causeex_dbpedia_20170308_m15a"; # postgres DB on awake-hn-01
my $actor_id_list = "/nfs/raid87/u11/CauseEx_Datasets/sams-dataset-actor-aggregation/actor_id_list.txt";
my $pickled_kb_list = "/nfs/raid87/u11/CauseEx_Datasets/sams-dataset-actor-aggregation/pickled_kbs.list";
my $bad_relations_file = "/nfs/raid87/u11/CauseEx_Datasets/sams-dataset-actor-aggregation/bad_relations.tsv";
my $geonames_to_wikipedia_file = "/nfs/raid87/u11/CauseEx_Datasets/sams-dataset-actor-aggregation/geonames_to_wikipedia.tsv";

# Scripts
my $GET_RELATIONSHIPS_FROM_AWAKE_DB = "$hume_repo_root/src/python/actor_aggregation/get_actor_aggregation_info_awake_db.py";
my $GET_RELATIONSHIPS_FROM_PICKLED_KBS = "$hume_repo_root/src/python/actor_aggregation/output_relation_counts_from_kbs.py";
my $COMBINE_KB_RELATION_COUNTS = "$hume_repo_root/src/python/actor_aggregation/combine_kb_relation_counts.py";
my $GET_FINAL_ACTOR_AGGREGATION_INFO = "$hume_repo_root/src/python/actor_aggregation/get_final_actor_aggregation_information.py";
my $GET_ALTERNATE_NAMES = "$hume_repo_root/src/python/actor_aggregation/get_alternate_names_awake_db.py";

my $processing_dir = make_output_dir("$exp_root/expts/$job_name");

max_jobs("$job_name/kb" => 400,);

# Actor aggregation from AWAKE DB
my $awake_relations_output_file = "$processing_dir/awake_db_relations.tsv";
my $awake_db_jobid = 
    runjobs(
	[], "$job_name/awake_db",
	{ 
	    BATCH_QUEUE => $LINUX_QUEUE,
	}, 
	["$PYTHON3 $GET_RELATIONSHIPS_FROM_AWAKE_DB $awake_db_name $actor_id_list $awake_relations_output_file"]
    );

# Alternate names from AWAKE DB
my $alternate_names_output_file = "$processing_dir/alternate_names.tsv";
my $alternate_names_jobid =
    runjobs(
	[], "$job_name/alternate_names",
	{ 
	    BATCH_QUEUE => $LINUX_QUEUE,
	}, 
	["$PYTHON3 $GET_ALTERNATE_NAMES $awake_db_name $actor_id_list $geonames_to_wikipedia_file $alternate_names_output_file"]
    );

# KBs
my $kb_relations_output_directory = make_output_dir("$processing_dir/kb_relations");
open(my $fh, '<:encoding(UTF-8)', $pickled_kb_list)
    or die "Could not open file '$pickled_kb_list' $!";
 
my $count = 0;
my $kbs_per_batch = 20;
my @current_kbs = ();
my @kb_jobids = ();

while (my $filename = <$fh>) {
    chomp $filename;
    push @current_kbs, $filename;
    
    if (scalar(@current_kbs) >= $kbs_per_batch) {

	my $padded_count = sprintf "%05d", $count;
	my $output_file = "$kb_relations_output_directory/relations-$padded_count.tsv";
	my $kb_jobid = 
	    runjobs(
		[], "$job_name/kb/$padded_count",
		{ 
		    BATCH_QUEUE => $LINUX_QUEUE,
		}, 
		["$PYTHON3 $GET_RELATIONSHIPS_FROM_PICKLED_KBS $actor_id_list $output_file " . join(" ", @current_kbs)]
	    );
	push @kb_jobids, $kb_jobid;
    
	$count++;
	@current_kbs = ();
    }
    
    #last if $count > 100;
}

# run last batch
if (scalar(@current_kbs) > 0) {

    my $padded_count = sprintf "%05d", $count;
    my $output_file = "$kb_relations_output_directory/relations-$padded_count.tsv";
    my $kb_jobid = 
	runjobs(
	    [], "$job_name/kb/$padded_count",
	    { 
		BATCH_QUEUE => $LINUX_QUEUE,
	    }, 
	    ["$PYTHON3 $GET_RELATIONSHIPS_FROM_PICKLED_KBS $actor_id_list $output_file " . join(" ", @current_kbs)]
	);
    push @kb_jobids, $kb_jobid;
    $count++;
}

# Combine results from KBs
my $combine_output_file = "$processing_dir/kb_relations.tsv";
my $combine_jobid =
    runjobs(
	\@kb_jobids, "$job_name/kb-combine",
	{ 
	    BATCH_QUEUE => $LINUX_QUEUE,
	}, 
	["$PYTHON3 $COMBINE_KB_RELATION_COUNTS $kb_relations_output_directory $combine_output_file"]
    );

my $final_output_file = "$processing_dir/actor_aggregation.tsv";
my $final_aa_job_id = 
    runjobs(
	[ $combine_jobid, $awake_db_jobid], "$job_name/final-aa",
	{ 
	    BATCH_QUEUE => $LINUX_QUEUE,
	}, 
	["$PYTHON3 $GET_FINAL_ACTOR_AGGREGATION_INFO $awake_relations_output_file $combine_output_file $bad_relations_file $geonames_to_wikipedia_file $final_output_file"]
    );

dojobs();

sub make_output_dir {
    my $dir = $_[0];
    mkpath($dir);
    return abs_path($dir);
}
