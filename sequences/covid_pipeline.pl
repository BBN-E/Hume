#!/usr/bin/env perl
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
use Nlplingo;
use LearnItDecoding;
use Utils;

my $last_jobs_ptr = [];
my $last_serif_list_ptr = $p->{input_files}->{serif_list};
my %stages = map {$_ => 1} @{$p->{stages_to_run}};

my ($exp_dir, $exp) = startjobs(%{$p->{runjobs_pars}});
my $use_gpus = $p->{use_gpus};
max_jobs($p->{max_jobs});
my $expts = "$exp_dir/expts/$p->{job_prefix}";

if (exists $stages{"cserif"}) {
    my $stage_name = "cserif";
    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $number_of_batches = $p->{num_of_batches};
    my $stage_processing_dir = "$expts/$stage_name";
    my $batch_file_dir = "$stage_processing_dir/batch/batch";
    my $cause_effect_output_dir = "$stage_processing_dir/causal_json/";
    my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $p->{PYTHON3_SYSTEM},
        CREATE_FILELIST_PY_PATH => "$p->{TEXT_OPEN_PYTHONPATH}/util/common/create_filelist_with_batch_size.py",
        num_of_batches          => $number_of_batches,
        suffix                  => "",
        output_file_prefix      => $batch_file_dir,
        list_file_path          => $p->{input_files}->{sgms_list},
        job_prefix              => "$job_prefix/",
        dependant_job_ids       => $last_jobs_ptr,
    );
    my @serif_jobs = ();
    for (my $n = 0; $n < $number_of_batches; $n++) {
        my $job_batch_num = $n;
        my $serif_job_name = "$job_prefix/split/$job_batch_num";
        my $experiment_dir = "$stage_processing_dir/split/$job_batch_num";
        my $batch_file = $batch_files[$n];
        my $serif_par = $p->{serif_pars}->{par_file};
        my $project_specific_serif_data_root = "$p->{HUME_RELEASE_DIR}/resource/serif_data_wm";
        my $serif_jobid =
            runjobs(
                $split_jobid, $serif_job_name,
                {
                    experiment_dir                    => $experiment_dir,
                    batch_file                        => $batch_file,
                    bbn_actor_db                      => $p->{input_files}->{awake_db},
                    cause_effect_output_dir           => $cause_effect_output_dir,
                    BATCH_QUEUE                       => $p->{runjobs_pars}->{batch_queue},
                    max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence},
                    %{$p->{serif_pars}->{runjobs_par}}
                },
                [ "mkdir -p $cause_effect_output_dir $experiment_dir" ],
                [ "$p->{SERIF_EXE}", $serif_par ]
            );
        push(@serif_jobs, $serif_jobid);
    }
    my $output_list_path = "$stage_processing_dir/serif.list";
    my $gather_results_jobid = runjobs(
        \@serif_jobs, "$job_prefix/collect",
        {
            SCRIPT => 1
        },
        [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/create_filelist.py --unix_style_pathname \"$stage_processing_dir/split/*/output/*.xml\" --output_list_path $output_list_path" ]
    );
    $last_jobs_ptr = [ $gather_results_jobid ];
    $last_serif_list_ptr = $output_list_path;
}
if (exists $stages{"pyserif_nlp"}){
    my $language_flag = $p->{input_files}->{language};
    my $input_type = $p->{input_files}->{input_type};
    my $input_path = $p->{input_files}->{$input_type . "_list"};
    my $config_path = $p->{pyserif_nlp}->{par_file}->{$language_flag}->{$input_type};
    ($last_jobs_ptr, $last_serif_list_ptr) = pyserif_processing_corpus(
        stage_name        => "pyserif_nlp",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $config_path,
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $p->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr,
        input_serif_list  => $input_path,
        template_inject   => $p->{pyserif_nlp}->{runjobs_par}
    );
}
if (exists $stages{"nlplingo_event"}) {
    ($last_jobs_ptr, $last_serif_list_ptr) = pyserif_processing_corpus(
        stage_name        => "nlplingo_event",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_event}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $p->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr,
        input_serif_list  => $last_serif_list_ptr
    );
}
if (exists $stages{"learnit_event_and_eer"}) {
    my $stage_name = "learnit_event_and_eer";
    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $number_of_batches = $p->{num_of_batches};
    my $stage_processing_dir = "$expts/$stage_name";
    my $learnit_decoding_obj = LearnItDecoding->new(
        TEXT_OPEN   => $p->{TEXT_OPEN_RELEASE_DIR},
        PYTHON3     => $p->{PYTHON3_SYSTEM},
        BATCH_QUEUE => $p->{runjobs_pars}->{batch_queue},
        MEM_LIMIT   => "16G"
    );
    (my $learnit_decoder_jobids, my $output_learnit_seriflist_path) = $learnit_decoding_obj->LearnItDecoding(
        dependant_job_ids                 => $last_jobs_ptr,
        job_prefix                        => $job_prefix,
        runjobs_template_path             => "learnit_decoding_pipeline.par",
        runjobs_template_hash             => {
            max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence},
            %{$p->{learnit_pars}->{runjobs_par}}
        },
        input_serifxml_list               => $last_serif_list_ptr,
        num_of_jobs                       => $number_of_batches,
        stage_processing_dir              => $stage_processing_dir,
        should_output_incomplete_examples => "false"
    );
    $last_jobs_ptr = $learnit_decoder_jobids;
    $last_serif_list_ptr = $output_learnit_seriflist_path;
}
if (exists $stages{"nlplingo_event_args"}) {
    ($last_jobs_ptr, $last_serif_list_ptr) = pyserif_processing_corpus(
        stage_name        => "nlplingo_event_args",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_event_args}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $p->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr,
        input_serif_list  => $last_serif_list_ptr,
        template_inject   => {
            hume_root => $p->{HUME_RELEASE_DIR},
        }
    );
}
if (exists $stages{"nlplingo_eer"}) {
    # ($last_jobs_ptr, $last_serif_list_ptr) = pyserif_processing_corpus(
    #     stage_name                    => "nlplingo_eer",
    #     job_queue                     => $p->{runjobs_pars}->{batch_gpu_queue},
    #     template                      => $p->{nlplingo_eer}->{par_file},
    #     python                        => $p->{PYTHON_GPU},
    #     num_of_batches                => $p->{num_of_batches},
    #     dependant_job_ids             => $last_jobs_ptr,
    #     input_serif_list              => $last_serif_list_ptr,
    #     template_inject               => {
    #         hume_root                         => $p->{HUME_RELEASE_DIR},
    #         max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence}
    #     },
    #     custom_driver                 => "$p->{TEXT_OPEN_PYTHONPATH}/serif/driver/pipeline_sequence.py",
    #     convert_filelist_to_old_style => 1
    # );
    ($last_jobs_ptr, $last_serif_list_ptr) = pyserif_processing_corpus(
        stage_name        => "nlplingo_eer",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_eer}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $p->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr,
        input_serif_list  => $last_serif_list_ptr,
        template_inject   => {
            hume_root => $p->{HUME_RELEASE_DIR},
        }
    );
}
if (exists $stages{"doctheory_resolver"}) {
    my $stage_name = "doctheory_resolver";
    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $stage_processing_dir = "$expts/$stage_name";
    my $batch_file_dir = "$stage_processing_dir/batch/batch";
    my $number_of_batches = $p->{num_of_batches};
    my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $p->{PYTHON3_SYSTEM},
        CREATE_FILELIST_PY_PATH => "$p->{TEXT_OPEN_PYTHONPATH}/util/common/create_filelist_with_batch_size.py",
        num_of_batches          => $number_of_batches,
        suffix                  => "",
        output_file_prefix      => $batch_file_dir,
        list_file_path          => $last_serif_list_ptr,
        job_prefix              => "$job_prefix/",
        dependant_job_ids       => $last_jobs_ptr,
    );
    my @doctheory_resolver_jobs = ();
    for (my $n = 0; $n < $number_of_batches; $n++) {
        my $batch_job_name = "$job_prefix/split/$n";
        my $job_batch_num = $n;
        my $batch_file = $batch_files[$n];
        my $doctheory_resolver_batch_job_output_dir = "$stage_processing_dir/split/$job_batch_num";
        my $doctheory_resolver_batch_jobid =
            runjobs(
                $split_jobid, $batch_job_name,
                {
                    BATCH_QUEUE               => $p->{runjobs_pars}->{batch_queue},
                    input_serifxml_list       => $batch_file,
                    output_serifxml_directory => $doctheory_resolver_batch_job_output_dir,
                    %{$p->{doctheory_resolver}->{runjobs_par}}
                },
                [ "mkdir -p $doctheory_resolver_batch_job_output_dir" ],
                [ "env java -cp $p->{HUME_RELEASE_DIR}/src/java/serif-util/target/causeex-serif-util-1.0.0-jar-with-dependencies.jar com.bbn.serif.util.resolver.DocTheoryResolver", $p->{doctheory_resolver}->{par_file} ]
            );
        push(@doctheory_resolver_jobs, $doctheory_resolver_batch_jobid);
    }
    my $output_list_path = "$stage_processing_dir/serif.list";
    my $gather_results_jobid = runjobs(
        \@doctheory_resolver_jobs, "$job_prefix/collect",
        {
            SCRIPT => 1
        },
        [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/create_filelist.py --unix_style_pathname \"$stage_processing_dir/split/*/*.xml\" --output_list_path $output_list_path" ]
    );
    $last_jobs_ptr = [ $gather_results_jobid ];
    $last_serif_list_ptr = $output_list_path;
}
if (exists $stages{"mtdp"}) {
    ($last_jobs_ptr, $last_serif_list_ptr) = pyserif_processing_corpus(
        stage_name        => "mtdp",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{mtdp}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $p->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr,
        input_serif_list  => $last_serif_list_ptr
    );
}
my $serialization_root = $p->{input_files}->{serialization_root};
my @serialization_jobids = ();
if (exists $stages{"kb_constructor"}) {
    my $stage_name = "kb_constructor";
    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $stage_processing_dir = "$expts/$stage_name";
    $serialization_root = $stage_processing_dir;
    my $batch_job_dir = "$stage_processing_dir/batch";
    my $job_output_dir = "$stage_processing_dir/output";
    my $copy_serifxml_jobid =
        runjobs(
            $last_jobs_ptr, "$job_prefix/creating_batch",
            {
                BATCH_QUEUE => $p->{runjobs_pars}->{batch_queue},
            },
            [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/copy_serifxml_by_document_type.py --input_serif_list $last_serif_list_ptr --output_dir $batch_job_dir --input_metadata_file $p->{input_files}->{metadata_file} --num_of_batches $p->{num_of_batches}" ]
        );
    # Serialize!
    my @serialization_batches = ();
    if (is_run_mode()) {
        dojobs();
        opendir(my $dh, $batch_job_dir);
        @serialization_batches = grep {-d "$batch_job_dir/$_" && !/^\.{1,2}$/} readdir($dh);
    }
    foreach my $batch_id (@serialization_batches) {
        my $serializer_output_dir = "$job_output_dir/$batch_id";
        my $input_batch_file_dir = "$batch_job_dir/$batch_id";
        my $serialize_job_name = "$job_prefix/serialize/kb-$batch_id";

        my $serialize_jobid =
            runjobs(
                [ $copy_serifxml_jobid ], $serialize_job_name,
                {
                    event_coreference_file => "NULL",
                    batch_file_dir         => $input_batch_file_dir,
                    pickle_output_file     => "$serializer_output_dir/output.pickle",
                    json_graph_file        => "$serializer_output_dir/visualization",
                    SGE_VIRTUAL_FREE       => "2G",
                    % {$p->{kb_constructor_par}->{runjobs_par}}
                },
                [ "mkdir -p $serializer_output_dir" ],
                [ "$p->{kb_constructor_par}->{python} $p->{HUME_RELEASE_DIR}/src/python/knowledge_base/kb_constructor.py", "kb_constructor_covid.par" ]
            );
        push(@serialization_jobids, $serialize_jobid);
    }
}

if (exists $stages{"merge_visualization_graph"}) {
    my $stage_name = "merge_visualization_graph";
    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $stage_processing_dir = "$expts/$stage_name";

    my $merge_eer_json_jobid = runjobs(
        \@serialization_jobids, "$job_prefix/merge_eer_json",
        {

        },
        [ "mkdir -p $stage_processing_dir" ],
        [ "$p->{PYTHON3_SYSTEM} $p->{LEARNIT_RELEASE_DIR}/HAT/new_backend/utils/aggr_ui_data_from_kb_constructor.py --dir_of_serialization $serialization_root --output_path $stage_processing_dir/output_eer.json" ]
    );
    my $merge_event_frame_jobid = runjobs(
        \@serialization_jobids, "$job_prefix/merge_event_frame",
        {

        },
        [ "mkdir -p $stage_processing_dir" ],
        [ "find $serialization_root -name \"output_event_frame.ljson\" -exec cat {} \\; > $stage_processing_dir/output_event_frame.ljson" ]
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
                    [ "$python $custom_driver", $template, "$batch_file $pyserif_batch_job_output_dir" ]
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

1;
