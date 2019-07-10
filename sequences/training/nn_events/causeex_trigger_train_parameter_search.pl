
use strict;
use warnings;

# Standard libraries:
use FindBin;
use Getopt::Long;
use File::Basename;
use File::Copy;
use Data::Dumper;

# Runjobs libraries:
#use lib ("/d4m/ears/releases/Cube2/R2011_11_21/install-optimize$ENV{ARCH_SUFFIX}/perl_lib");
use lib ("/d4m/ears/releases/Cube2/R2016_02_12/" .
    "install-optimize$ENV{ARCH_SUFFIX}/perl_lib");
use runjobs4;
use File::PathConvert;
use Parameters;
use PerlUtils;
use RunJobsUtils;
use Cwd 'abs_path';

# Package declaration:
package main;

our ($exp_root, $exp) = startjobs();
my $expts = "$exp_root/expts";


my $paramFile = $ARGV[0];
print "Got param file $paramFile\n";
my $params = Parameters::loadAndPrint($paramFile);

defined($params) or die "Could not load params";

my $exptName = $params->get("experiment_name");

max_jobs($exptName . "/gpu/" => 15,);
max_jobs($exptName ."/cpu/" => 200,);


my $SINGULARITY_GPU_QUEUE = "allGPUs-sl69-non-k10s";

my $SINGULARITY_WRAPPER = abs_path("$FindBin::Bin/scripts/run-in-singularity-container.sh");


######## These are the things user might want to change ########

# python_path needs to point 2 things: dir containing serifxml.py , and the nlplingo code base
my $python_path = "/nfs/raid87/u14/CauseEx/NN-events-requirements/SVN_PROJECT_ROOT_PY3:/nfs/ld100/u10/hqiu/CauseEx-pipeline-WM/nlplingo/";

# we directly point to the python binary which has keras, theano (packages required by nlplingo) installed
#my $python_bin = "/nfs/raid66/u14/users/jfaschin/installs/anaconda2/envs/tf-1.5-cpu-py27/bin/python";

my $python_bin = "python3";
my $PYTHON = "/nfs/e-nfs-03/home/jfaschin/bin/mypython";

my $cmd_script = "/nfs/ld100/u10/hqiu/CauseEx-pipeline-WM/nlplingo/nlplingo/event/train_test.py";

my $split_script = abs_path("$FindBin::Bin/scripts/generate_cv.py");

my $aggregate_score_script = abs_path("$FindBin::Bin/scripts/aggregate_scores.py");
my $average_score_script = abs_path("$FindBin::Bin/scripts/average_scores.py");

#my @runs = ("run1", "run2", "run3");
# my @positive_weights = (1.0, 10.0);
# my @batch_sizes = (100, 150);
# my @num_epochs = (5, 10);

# my @positive_weights = (10);
# my @batch_sizes = (100, 150);
# my @num_epochs = (5, 10);
# my @num_feature_maps = (200,300);

my @positive_weights = (3,5);
my @batch_sizes = (50,100);
my @num_epochs = (30);
my @num_feature_maps = (200);

# my @positive_weights = (3,5);
# my @batch_sizes = (50,100);
# my @num_epochs = (20,30,35,40);
# my @num_feature_maps = (150,200);

my $n_fold = 3;

my $input_directory = $params->get("input_directory");

my $num_batches = $params->get("num_batches");

my $do_cross_validation = $params->get("do_cross_validation");

##### setup folds ######
my $exptDir = "$expts/$exptName";

if(!-d $exptDir) {
	my $cmd = "mkdir -p $exptDir";
	`$cmd`;
}

my @cv_split_jobs = ();

for(my $batch_index=0; $batch_index<$num_batches; $batch_index++) {
	my $span_file = sprintf( 
		$input_directory . "/batch_%d/argument.abridged.span_serif_list", 
		$batch_index+1 
		);
	my $name = "$exptName/cv_split_$batch_index";
	my $output_prefix = sprintf( 
		$exptDir . "/argument.abridged.batch_%d", 
		$batch_index+1 
		);
	if($do_cross_validation){

			my $sent_spans_files = join " ", glob($input_directory . "/*.sent_spans");
			my $event_type_list = sprintf( 
				$input_directory . "/event_types_batch_%05d.txt", 
				$batch_index 
			);

			push @cv_split_jobs, runjobs4::runjobs(
				[], 
				$name, 
				{ 
					BATCH_QUEUE => 'nongale-sl6', 
					SGE_VIRTUAL_FREE => "4G" }, 
				["$PYTHON $split_script " . 
				 sprintf("$input_directory/batch_%d/ ", $batch_index+1) .
				 "$output_prefix " . 
				 "$n_fold"]
				);

	} else {
		for(my $fold=0; $fold<$n_fold; $fold++){
			copy(
				$span_file, 
				$output_prefix . ".fold_" . $fold . ".train" 
			);
			print $span_file . "\n";
			print $output_prefix . ".fold_" . $fold . ".train\n";
		}
	}
}

my @average_score_jobs = ();

######## End of things to change ########
for(my $weight_index=0; $weight_index<=$#positive_weights; $weight_index++) {
	my $weight = $positive_weights[$weight_index];

	for(my $size_index=0; $size_index<=$#batch_sizes; $size_index++) {
		my $size = $batch_sizes[$size_index];

		for(my $epoch_index=0; $epoch_index<=$#num_epochs; $epoch_index++) {
			my $epoch = $num_epochs[$epoch_index];
			
			for(my $feature_map_index=0; $feature_map_index<=$#num_feature_maps; $feature_map_index++) {
				my $feature_maps = $num_feature_maps[$feature_map_index];


			my @aggregate_score_jobs = ();
			my @score_files_across_folds = ();

			for(my $fold=0; $fold<$n_fold; $fold++){

				my @batch_learn_jobs = ();
				
				my @score_files_per_fold = ();

				for(my $batch_index=0; $batch_index<$num_batches; $batch_index++) {
					my $domain_ontology_file = sprintf( 
						$input_directory . "/batch_%d/domain_ontology.txt\n", 
						$batch_index+1 
					);
					my $trigger_word_span_file = sprintf( 
					 	$input_directory . "/batch_%d/argument.sent_spans.list", 
					 	$batch_index+1 
					);
					my $span_file_train = sprintf( 
					 	$exptDir . "/argument.abridged.batch_%d.fold_%d.train", 
					 	$batch_index+1,
					 	$fold
					);
					
					my $span_file_dev = sprintf( 
						$exptDir . "/argument.abridged.batch_%d.fold_%d.train", 
						$batch_index+1,
						$fold
						);
					my $span_file_test = sprintf( 
						$exptDir . "/argument.abridged.batch_%d.fold_%d.test", 
						$batch_index+1,
						$fold
						);
					my $suffix = "w" . $weight . "s" . $size . "e" . $epoch . "f". $feature_maps .
						"/fold_" . $fold . "/" .
						sprintf( "batch_%d", $batch_index+1 );
					my $name = $exptName . "/gpu/" . $suffix;
					my $run_dir = $expts . "/". $exptName . "/" . $suffix;
					
					my %execute_train_dev_test_params; 
					if($do_cross_validation){
						%execute_train_dev_test_params = (
							dependant_job_ids => \@cv_split_jobs,
							job_name => $name,
							run_dir => $run_dir,
							params => $params,
							weight => $weight,
							size => $size,
							epoch => $epoch,
							feature_maps => $feature_maps,
							fold => $fold,
							batch_index => $batch_index,
							domain_ontology_file => $domain_ontology_file,
							trigger_word_span_file => $trigger_word_span_file,
							span_file_train => $span_file_train,
							span_file_dev => $span_file_dev,
						    span_file_test => $span_file_test
					    );
					} else {
						%execute_train_dev_test_params = (
							dependant_job_ids => \@cv_split_jobs,
							job_name => $name,
							run_dir => $run_dir,
							params => $params,
							weight => $weight,
							size => $size,
							epoch => $epoch,
							feature_maps => $feature_maps,
							fold => $fold,
							batch_index => $batch_index,
							domain_ontology_file => $domain_ontology_file,
							trigger_word_span_file => $trigger_word_span_file,
							span_file_train => $span_file_train
					    );

					}
					push @batch_learn_jobs, execute_train_dev_test(\%execute_train_dev_test_params);
					if($do_cross_validation){
						push @score_files_per_fold, "$run_dir/test/test_trigger.score";
					}
				}
				if($do_cross_validation){
					my $aggregate_job_name = $exptName . "/cpu/" . 
						"w".$weight."s".$size."e".$epoch . "f". $feature_maps . 
						"/fold_$fold/aggregate_scores";
					my $fold_score_output_path = $expts."/" .
						$exptName."/"
						."w".$weight."s".$size."e".$epoch .  "f". $feature_maps .
						"/fold_$fold/test_trigger.score";
					my $input_score_files_per_fold = join( ' ', @score_files_per_fold); 
					
					push @aggregate_score_jobs, runjobs4::runjobs(
						\@batch_learn_jobs, 
						$aggregate_job_name, 
						{ 
							BATCH_QUEUE => 'nongale-sl6', 
							SGE_VIRTUAL_FREE => "4G" },
						["$PYTHON $aggregate_score_script " . 
						 "--input_files $input_score_files_per_fold " .
						 "--output_file $fold_score_output_path"]
						);
					push @score_files_across_folds, $fold_score_output_path;
				}
			}
			if($do_cross_validation){
				my $average_score_job_name = $exptName."/cpu/".
					"w".$weight."s".$size."e".$epoch. "f". $feature_maps .
					"/average_scores";
				my $average_score_output_path = $expts."/".
					$exptName."/"
					."w".$weight."s".$size."e".$epoch. "f". $feature_maps .
					"/test_trigger.score";
				my $input_score_files_across_folds = join( ' ', @score_files_across_folds);
				push @average_score_jobs, runjobs4::runjobs(
					\@aggregate_score_jobs, 
					$average_score_job_name, 
					{ 
						BATCH_QUEUE => 'nongale-sl6', 
						SGE_VIRTUAL_FREE => "4G" },
					["$PYTHON $average_score_script ".
					 "--input_files $input_score_files_across_folds " .
					 "--output_file $average_score_output_path"]
					);
			}
			}		
		}
	}
}

endjobs();

# Due to Theano and the way the SGE machines are setup, these operations must be run using one script.
sub execute_train_dev_test {
	my ($args) = @_;	

	chomp(%$args);

	my $par = $args->{params}->copy();
	$par->set("domain_ontology", $args->{domain_ontology_file});
	$par->set("trigger_candidate_span_file", $args->{trigger_word_span_file});
	$par->set("filelist.train", $args->{span_file_train});
	$par->set("filelist.dev", $args->{span_file_train});

	if ($args->{span_file_dev}){
		$par->set("filelist.test", $args->{span_file_dev});
	}

	$par->set("trigger.positive_weight", $args->{weight});
	$par->set("trigger.epoch", $args->{epoch});
	$par->set("trigger.num_feature_maps", $args->{feature_maps});
	$par->set("trigger.batch_size", $args->{size});
	$par->set("output_dir", $args->{run_dir});
	$par->set("trigger_model_dir", $args->{run_dir});
	
	if(!-d $args->{run_dir}) {
		my $cmd = "mkdir -p " . $args->{run_dir};
		`$cmd`;
	}
	
	my $params_file = $args->{run_dir} . "/params";
	open OUT, ">$params_file";
	print OUT $par->dump();
	close OUT;
	
	my @run_sh_cmds = ();
	push @run_sh_cmds, "export KERAS_BACKEND=tensorflow\n";
	push @run_sh_cmds, "cd " . $args->{run_dir}. "\n";
	push @run_sh_cmds, "cp " . $args->{domain_ontology_file} . " domain_ontology.txt\n";
	push @run_sh_cmds, "PYTHONPATH=$python_path " . 
		"$python_bin $cmd_script --params " . $args->{run_dir} ."/params --mode train_trigger\n";

	# if($args->{span_file_dev}){;
	# 	push @run_sh_cmds, "PYTHONPATH=$python_path " . 
	# 		"$python_bin $cmd_script --params " . $args->{run_dir} . "/params --mode test_trigger\n";
   
	# }

	if($args->{span_file_test}){
		if(!-d $args->{run_dir} . "/test") {
			my $cmd = "mkdir -p " . $args->{run_dir} . "/test";
			`$cmd`;
		}

		my $params_file_test = $args->{run_dir} . "/test/params";
		my $par_test = $par->copy();
		$par_test->set("filelist.test", $args->{span_file_test});
		$par_test->set("output_dir", $args->{run_dir} . "/test");
		open OUT, ">$params_file_test";
		print OUT $par_test->dump();
		push @run_sh_cmds, "PYTHONPATH=$python_path " . 
			"$python_bin $cmd_script --params " . $args->{run_dir} . "/test/params --mode test_trigger\n";
		push @run_sh_cmds, "rm trigger.hdf\n";
	}

	# Build the run.sh file
	my $bash_file = $args->{run_dir} . "/run.sh";
	open OUT, ">$bash_file";         
	
	for my $run_sh_cmd (@run_sh_cmds) {
		print OUT $run_sh_cmd;
	}
	close OUT;
	
	my $cmd = "chmod +x $bash_file";
	`$cmd`;
	
	# Schedule the run.sh file
	$cmd = "$bash_file";
	my $jobid = runjobs4::runjobs(
		$args->{dependant_job_ids}, 
		$args->{job_name}, 
		{  
			BATCH_QUEUE                      => $SINGULARITY_GPU_QUEUE, 
			SGE_VIRTUAL_FREE => "16G"
		}, 
		["$SINGULARITY_WRAPPER $bash_file"]
		);
	return $jobid;
}
