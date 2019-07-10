eval '(exit $?0)' && eval 'exec perl -w -S $0 ${1+"$@"}' && eval 'exec perl -w -S $0 $argv:q'
    if 0;

package main;

use warnings;
use strict;
use err_check;

use FindBin;
use Cwd 'abs_path';
use Clone;
use Data::Dumper;


###############################################################
#                 Control Variable Definitions.
###############################################################
BEGIN {

    #BBN_CONTROL: experiment control directory
    $main::BBN_CONTROL = abs_path("$FindBin::Bin../..");

    #Required for Runjobs
    $main::OTHER_QUEUE = 'gale-nongale-sl6';
    $main::QUEUE_PRIO = '5';

    $main::NLPLINGO_PYTHONPATH = "/nfs/raid66/u14/users/jfaschin/Active/Projects/SERIF/python:/nfs/raid87/u15/users/jfaschin/nlplingo_causeeffect",
    $main::NLPLINGO_PYTHON = "/d4m/material/software/python/mypython -b /home/dakodes/cxhome/cause-effect/anaconda2/envs/tensorflow-1.5-gpu-p2/bin/python -l $main::NLPLINGO_PYTHONPATH";

 #Releases
    my $cube2_release_root = "/d4m/ears/releases/Cube2";
    my $cube2_release = "R2016_02_12";
    my $cube_pm_release_root = "/d4m/material/releases/cubepm/";
    my $cube_pm_release = "R2018_01_23";

    #Cube2
    $main::CUBE2_RELEASE_DIR = "$cube2_release_root/$cube2_release";

    #CubePM
    $main::CUBE_PM_RELEASE_DIR = "$cube_pm_release_root/$cube_pm_release";
    $main::CUBE_PM_LIB_DIR = "$main::CUBE_PM_RELEASE_DIR/lib";

    #pycube
    $main::PYCUBE_RELEASE_DIR =  "/nfs/raid84/u12/ychan/sandbox/pycube/pycube.2018_01_26";
    $main::PYTHON_LIB_PATH = $main::PYCUBE_RELEASE_DIR;
    $main::PYTHON_VENV = "/d4m/material/software/python/venv/default/bin/python";
    $main::PYTHON = "/d4m/material/software/python/mypython -b $main::PYTHON_VENV -l $main::PYTHON_LIB_PATH";

    #Runjobs 4
    $main::runjobs4_dir = "$cube2_release_root/$cube2_release/install-optimize/perl_lib";
    $main::SGE_VIRTUAL_FREE = '8G';

    #$main::NLPLINGO_PYTHONPATH = "PYTHONPATH=/nfs/mercury-04/u22/Active/Projects/SERIF/python:/nfs/mercury-04/u40/ychan/repos/nlplingo",
}

use lib $main::CUBE_PM_LIB_DIR;
use lib $main::LOCAL_CUBE_PM_LIB_DIR;
use lib $main::runjobs4_dir;

use runjobs4;
use MT::Subs;

###################################
# Control Variables
###################################
my $env = {
    BBN_CONTROL => $main::BBN_CONTROL,
    exp => $main::exp,
    CUBE2_RELEASE_DIR => $main::CUBE2_RELEASE_DIR,
    CUBEPM_RELEASE_DIR => $main::CUBE_PM_RELEASE_DIR,
    PYCUBE_RELEASE_DIR => $main::PYCUBE_RELEASE_DIR,
    PYTHON => $main::PYTHON,
};

# Initialize template search path
&Common::Utils::init_template_path();
&MT::Subs::init($env);



my ($exp_dir, $exp) = startjobs("batch_queue" => "gale-sl6", "queue_priority" => 5, "queue_mem_limit" => '16G');
max_jobs(400,);

my $pars = {
    # List of lowercase keywords to mine for
    keywords => "/nfs/raid87/u11/users/jfaschin/runjobs/expts/causeex_scs_05142019/nn_events/original_annotation_keywords_and_most_populus_keywords.adjudicated.lowercase.unique.txt",
	# The filelists are lists fo serifxml files
    conds => [
        {
            name => "causeex_scs",
			file_list => "/home/hqiu/ld100/Hume_pipeline/Hume/expts/causeex_scs.v1.051619/generic_events_serifxml_out.list",
			number_of_chunks => 200,
        },
		{
			name => "gigaword",
			file_list => "/nfs/e-nfs-03/home/jfaschin/gigaword_400K.list",
			number_of_chunks => 8000,
		},
    ],


    _binaries => {
		split_list => "$main::PYTHON $main::PYCUBE_RELEASE_DIR/pycube/clir/query_constraint/split_list.py",
        keyword_context_from_corpus => "$main::NLPLINGO_PYTHON " . abs_path("$FindBin::Bin/..") . "/python/keyword_context_from_corpus.py",
        aggregate_kw_context => "$main::NLPLINGO_PYTHON " . abs_path("$FindBin::Bin/..") . "/python/aggregate_kw_context.py",
		gen_amt_annotation => "$main::NLPLINGO_PYTHON "  . abs_path("$FindBin::Bin/..") . "/python/gen_amt_annotation.py"
    },
};


my $expbase = "$exp_dir/expts";

my $jobpfx = "intitial-";

my @output_mkdirs = mkdirs([], "${jobpfx}mkdirs", "$expbase/amt");


my @aggregate_jobs = ();
foreach my $cond (@{$pars->{conds}}) {
    my $cond_name = $cond->{name};
    my $output_dir = "$expbase/output/$cond_name";
    my $intermediate_dir = "$expbase/intermediate/$cond_name";
    
	my $jobpfx = "$cond_name-";

	my @split_mkdirs = mkdirs([@output_mkdirs], "${jobpfx}filelist-mkdirs", "$intermediate_dir/file_list");
	my @split_jobs = json_runjobs(
		[@split_mkdirs], 
		"${jobpfx}split_list",
		{
			file_list => $cond->{file_list},
			number_of_chunks => $cond->{number_of_chunks},
			output_dir => "$intermediate_dir/file_list",
		},
		$pars->{_binaries}->{'split_list'}
	);

    my @chunk_dirs = "";
    for(my $i=0; $i<$cond->{number_of_chunks}; $i++) {
        push(@chunk_dirs, "$output_dir/chunks/chunk$i");
    }

    my @mkdirs = mkdirs(
		[], 
		"${jobpfx}mkdirs", 
		join(
			" ", 
			$intermediate_dir, 
			join(" ", @chunk_dirs), 
			"$output_dir/kw_context", 
			"$output_dir/amt"
		)
	);

    my @data_jobs = ();
    for(my $index=0; $index<$cond->{number_of_chunks}; $index++) {
        my $data_job = json_runjobs(
			[@mkdirs, @split_jobs], 
			"${jobpfx}json-chunk".$index,
			{
				serifxml_filelist => "$intermediate_dir/file_list/chunk$index.list",
				wordlist => $pars->{keywords},
				outdir => "$output_dir/chunks/chunk$index",
				SGE_VIRTUAL_FREE => "16G"
			},
			$pars->{_binaries}->{'keyword_context_from_corpus'}
		);
		push(@data_jobs, $data_job);
    }

    my @aggregate_kw_context_jobs = json_runjobs(
		[@data_jobs], 
		"${jobpfx}aggregate-kw-context",
		{
			chunks_dir => "$output_dir/chunks",
			outdir => "$output_dir/kw_context",
			SGE_VIRTUAL_FREE => "64G",
		},
		$pars->{_binaries}->{'aggregate_kw_context'}
    );
	push @aggregate_jobs, @aggregate_kw_context_jobs;

}
my @gen_amt_annotation_jobs = json_runjobs(
	[@aggregate_jobs], 
	"${jobpfx}gen-amt-annotation",
	{
		kw_context_dir => "$expbase/output/causeex_scs/kw_context",
		aux_context_dir => "$expbase/output/gigaword/kw_context",
		keywords => "/nfs/raid87/u11/users/jfaschin/runjobs/expts/causeex_scs_05142019/nn_events/original_annotation_keywords_and_most_populus_keywords.adjudicated.lowercase.unique.txt",
		# Event type to list of keywords lookup
		event_type_to_kw_file => "/nfs/raid87/u11/users/jfaschin/runjobs/expts/causeex_scs_05142019/nn_events/merged_keywords.json",
		min_number_example => 5,
		number_of_examples => 72280,
		outdir => "$expbase/amt",
	},
	$pars->{_binaries}->{'gen_amt_annotation'}
);

endjobs();

