#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';

use FindBin qw($Bin $Script);

# Load MT-style defines file
my $p;
BEGIN {
    (my $param_file = "$Bin/$Script") =~ s/\.pl$/.defines.pl/;
    my $user_params = do $param_file;
    if (!defined $user_params) {
        die "Unable to parse '$param_file': $@\n" if $@;
        die "Unable to load '$param_file': $!\n" if $!;
    }
    $p = $user_params;
    unshift @INC, @{$p->{perl_libs}};
}

use runjobs4;
use Utils;

my ($exp_dir, $exp) = startjobs(%{$p->{runjobs_pars}});
my $use_gpus = $p->{use_gpus};
if (!$use_gpus) {
    $p->{PYTHON_GPU} = $p->{PYTHON_CPU};
    $p->{runjobs_pars}->{batch_gpu_queue} = $p->{runjobs_pars}->{batch_queue};
}
max_jobs($p->{max_jobs});
my $expts = "$exp_dir/expts/$p->{job_prefix}";

{
    (undef, undef) = pyserif_processing_corpus(
        stage_name        => "pyserif_fix",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{pyserif_fix}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $p->{num_of_batches},
        dependant_job_ids => [],
        input_serif_list  => $p->{input_list},
        template_inject   => $p->{pyserif_fix}->{runjobs_par}
    );
}

endjobs();

sub pyserif_processing_corpus {
    my %args = @_;
    my $stage_name = $args{stage_name};
    my $job_queue = $args{job_queue};
    my $template = $args{template};
    my $template_inject = $args{template_inject} || {};
    my $python = $args{python};
    my $number_of_batches = $args{num_of_batches};
    my $dependant_job_ids = $args{dependant_job_ids};
    my $input_serif_list = $args{input_serif_list};
    my $custom_driver = $args{custom_driver} || "$p->{TEXT_OPEN_PYTHONPATH}/serif/driver/pipeline.py";
    my $convert_filelist_to_old_style = $args{convert_filelist_to_old_style} || 0;

    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $stage_processing_dir = "$expts/$stage_name";
    my $batch_file_dir = "$stage_processing_dir/batch/batch";
    my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $p->{PYTHON3_SYSTEM},
        CREATE_FILELIST_PY_PATH => "$p->{TEXT_OPEN_PYTHONPATH}/util/common/create_filelist_with_batch_size.py",
        num_of_batches          => $number_of_batches,
        suffix                  => "",
        output_file_prefix      => $batch_file_dir,
        list_file_path          => $input_serif_list,
        job_prefix              => "$job_prefix/",
        dependant_job_ids       => $dependant_job_ids,
    );
    my @pyserif_jobs = ();
    for (my $n = 0; $n < $number_of_batches; $n++) {
        my $batch_job_name = "$job_prefix/split/$n";
        my $job_batch_num = $n;
        my $batch_file = $batch_files[$n];
        my $pyserif_batch_job_output_dir = "$stage_processing_dir/split/$job_batch_num";
        my $pyserif_batch_jobid = undef;
        if (!$convert_filelist_to_old_style) {
            $pyserif_batch_jobid =
                runjobs(
                    $split_jobid, $batch_job_name,
                    {
                        TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
                        BATCH_QUEUE          => $job_queue,
                        %{$template_inject}
                    },
                    [ "mkdir -p $pyserif_batch_job_output_dir" ],
                    [ "env JAVA_OPTS=\"-Xmx64G\" $python $custom_driver", $template, "$batch_file $pyserif_batch_job_output_dir" ]
                );
        }
        else {
            $pyserif_batch_jobid =
                runjobs(
                    $split_jobid, $batch_job_name,
                    {
                        TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
                        BATCH_QUEUE          => $job_queue,
                        %{$template_inject}
                    },
                    [ "mkdir -p $pyserif_batch_job_output_dir" ],
                    [ "awk '{print \"serifxml\t\"\$0}' $batch_file > $batch_file\.with_type" ],
                    [ "$python $custom_driver", $template, "$batch_file\.with_type $pyserif_batch_job_output_dir" ]
                );
        }
        push(@pyserif_jobs, $pyserif_batch_jobid);
    }
    my $output_list_path = "$stage_processing_dir/serif.list";
    my $gather_results_jobid = runjobs(
        \@pyserif_jobs, "$job_prefix/collect",
        {
            SCRIPT => 1
        },
        [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/create_filelist.py --unix_style_pathname \"$stage_processing_dir/split/*/*.xml\" --output_list_path $output_list_path" ]
    );
    return([ $gather_results_jobid ], $output_list_path);
}