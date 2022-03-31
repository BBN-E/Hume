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
use MT::NmtDecode;

my %stages = map {$_ => 1} @{$p->{stages_to_run}};

my ($exp_dir, $exp) = startjobs(%{$p->{runjobs_pars}});
my $use_gpus = $p->{use_gpus};
if (!$use_gpus) {
    $p->{PYTHON_GPU} = $p->{PYTHON_CPU};
    $p->{runjobs_pars}->{batch_gpu_queue} = $p->{runjobs_pars}->{batch_queue};
}
max_jobs($p->{max_jobs});
my $expts = "$exp_dir/expts/$p->{job_prefix}";

my $last_jobs_ptr_en = [];
my $last_jobs_ptr_cn = [];
my $en_input_en_ptr = undef;
my $cn_input_en_ptr = undef;

keys %{$p->{input_files}};
while (my ($k, $v) = each %{$p->{input_files}}) {
    if ($k eq "en") {
        $en_input_en_ptr = $v;
    }
    else {
        $cn_input_en_ptr = $v;
    }
}

if (exists $stages{"pyserif_nlp"}) {
    # en call
    my $en_template_inject = $p->{pyserif_nlp}->{runjobs_par};
    my $en_metadata_hash = { METADATA_FILE_PATH => $p->{input_files}->{en}->{metadata} };
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "pyserif_nlp/en",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{pyserif_nlp}->{par_file}->{en}->{$en_input_en_ptr->{type}},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
        template_inject   => { %$en_template_inject, %$en_metadata_hash }
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    my $zh_template_inject = $p->{pyserif_nlp}->{runjobs_par};
    my $zh_metadata_hash = { METADATA_FILE_PATH => $p->{input_files}->{zh_hans}->{metadata} };
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "pyserif_nlp/cn",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{pyserif_nlp}->{par_file}->{zh}->{$cn_input_en_ptr->{type}},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
        template_inject   => { %$zh_template_inject, %$zh_metadata_hash }
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"nlplingo_event"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "nlplingo_event/en",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_event}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
        template_inject   => {
            hume_root => $p->{HUME_RELEASE_DIR},
        }
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "nlplingo_event/cn",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_event}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
        template_inject   => {
            hume_root => $p->{HUME_RELEASE_DIR},
        }
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"learnit_event_and_eer"} && $p->{learnit_pars}->{run_mt_and_jserif_compliance_stage}) {
    # This is the JSerif compliance and MT stage
    # en call
    my $en_stage_name = "learnit_event_and_eer/en";
    my $en_job_prefix = $p->{job_prefix} . "/$en_stage_name";
    my $en_stage_processing_dir = "$expts/$en_stage_name";
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "$en_stage_name/pyserif_compatible",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{jserif_compatible_par}->{par_file},
        python            => $p->{PYTHON_CPU},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    my $cn_stage_name = "learnit_event_and_eer/cn";
    my $cn_job_prefix = "$p->{job_prefix}/$cn_stage_name";
    my $cn_stage_processing_dir = "$expts/$cn_stage_name";
    # Step 0. Make sure cn serifxml can be digest by JSerif code
    (my $last_jobs_ptr_cn_subjob1, my $cn_serif_list_ptr_subjob1) = pyserif_processing_corpus(
        stage_name        => "$cn_stage_name/pyserif_compatible_original_cn",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{jserif_compatible_par}->{par_file},
        python            => $p->{PYTHON_CPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
    );
    # Step 1, translate chinese articles into english
    (my $last_jobs_ptr_cn_subjob2, my $mt_json_filelist) = translate(
        job_prefix           => "$cn_job_prefix/mt",
        stage_processing_dir => "$cn_stage_processing_dir/mt",
        source_serifxml_list => $cn_input_en_ptr->{file_list},
        num_of_batches       => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids    => $last_jobs_ptr_cn
    );
    # Step 2, pyserif
    ($last_jobs_ptr_cn_subjob2, my $en_serif_list_from_en) = pyserif_processing_corpus(
        stage_name        => "$cn_stage_name/pyserif_translated_en",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{pyserif_nlp}->{par_file}->{en}->{mtjsons},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn_subjob2,
        input_serif_list  => $mt_json_filelist,
        template_inject   => $p->{pyserif_nlp}->{runjobs_par}
    );
    ($last_jobs_ptr_cn_subjob2, $en_serif_list_from_en) = pyserif_processing_corpus(
        stage_name        => "$cn_stage_name/pyserif_compatible_translated_en",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{jserif_compatible_par}->{par_file},
        python            => $p->{PYTHON_CPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn_subjob2,
        input_serif_list  => $en_serif_list_from_en,
    );
    $last_jobs_ptr_cn = ();
    foreach my $job (@{$last_jobs_ptr_cn_subjob1}) {
        push(@{$last_jobs_ptr_cn}, $job);
    }
    foreach my $job (@{$last_jobs_ptr_cn_subjob2}) {
        push(@{$last_jobs_ptr_cn}, $job);
    }
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_subjob1;
    $cn_input_en_ptr->{en_serif_list_from_en} = $en_serif_list_from_en;
    $cn_input_en_ptr->{mt_json_filelist} = $mt_json_filelist;
}

if (exists $stages{"learnit_event_and_eer"}) {
    # en call
    my $en_stage_name = "learnit_event_and_eer/en";
    my $en_job_prefix = $p->{job_prefix} . "/$en_stage_name";
    my $en_stage_processing_dir = "$expts/$en_stage_name";
    my $learnit_decoding_obj = LearnItDecoding->new(
        TEXT_OPEN   => $p->{TEXT_OPEN_RELEASE_DIR},
        PYTHON3     => $p->{PYTHON3_SYSTEM},
        BATCH_QUEUE => $p->{runjobs_pars}->{batch_queue},
        MEM_LIMIT   => "48G"
    );
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = $learnit_decoding_obj->LearnItDecoding(
        dependant_job_ids                 => $last_jobs_ptr_en,
        job_prefix                        => $en_job_prefix,
        runjobs_template_path             => "learnit_decoding_pipeline.par",
        runjobs_template_hash             => {
            max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence},
            %{$p->{learnit_pars}->{runjobs_par}}
        },
        languages                         => [ "English" ],
        filelists                         => { English => $en_input_en_ptr->{file_list} },
        num_of_jobs                       => $en_input_en_ptr->{num_of_batches},
        stage_processing_dir              => $en_stage_processing_dir,
        should_output_incomplete_examples => "false"
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local->{English};
    #cn call
    my $cn_stage_name = "learnit_event_and_eer/cn";
    my $cn_job_prefix = "$p->{job_prefix}/$cn_stage_name";
    my $cn_stage_processing_dir = "$expts/$cn_stage_name";
    # Step 3, bilingual LearnIt
    ($last_jobs_ptr_cn, my $combined_filelist) = $learnit_decoding_obj->LearnItDecoding(
        dependant_job_ids                 => $last_jobs_ptr_cn,
        job_prefix                        => "$cn_job_prefix/bilingual_learnit",
        runjobs_template_path             => "learnit_decoding_pipeline_bilingual.par",
        runjobs_template_hash             => {
            max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence},
            %{$p->{learnit_pars}->{runjobs_par}}
        },
        languages                         => [ "English", "Chinese" ],
        filelists                         => { English => $cn_input_en_ptr->{en_serif_list_from_en}, Chinese => $cn_input_en_ptr->{file_list}, mt_json_list => $cn_input_en_ptr->{mt_json_filelist} },
        num_of_jobs                       => $cn_input_en_ptr->{num_of_batches},
        stage_processing_dir              => "$cn_stage_processing_dir/bilingual_learnit",
        should_output_incomplete_examples => "false"
    );
    $cn_input_en_ptr->{file_list} = $combined_filelist->{Chinese};
}

if (exists $stages{"throw_out_of_ontology_events"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = doctheory_resolver(
        job_prefix                         => $p->{job_prefix} . "/throw_out_of_ontology_events/en",
        stage_processing_dir               => "$expts/throw_out_of_ontology_events/en",
        dependant_job_ids                  => $last_jobs_ptr_en,
        input_serifxml_list                => $en_input_en_ptr->{file_list},
        num_of_batches                     => $en_input_en_ptr->{num_of_batches},
        doctheory_resolver_template        => $p->{throw_out_of_ontology_events}->{par_file},
        doctheory_resolver_template_inject => $p->{throw_out_of_ontology_events}->{runjobs_par},
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = doctheory_resolver(
        job_prefix                         => $p->{job_prefix} . "/throw_out_of_ontology_events/cn",
        stage_processing_dir               => "$expts/throw_out_of_ontology_events/cn",
        dependant_job_ids                  => $last_jobs_ptr_cn,
        input_serifxml_list                => $cn_input_en_ptr->{file_list},
        num_of_batches                     => $cn_input_en_ptr->{num_of_batches},
        doctheory_resolver_template        => $p->{throw_out_of_ontology_events}->{par_file},
        doctheory_resolver_template_inject => $p->{throw_out_of_ontology_events}->{runjobs_par},
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"nlplingo_event_args"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "nlplingo_event_args/en",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_event_args}->{par_file}->{en},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
        template_inject   => {
            hume_root => $p->{HUME_RELEASE_DIR},
        }

    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "nlplingo_event_args/cn",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{nlplingo_event_args}->{par_file}->{zh},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
        template_inject   => {
            hume_root => $p->{HUME_RELEASE_DIR},
        }

    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"nlplingo_eer"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name           => "nlplingo_eer/en",
        job_queue            => $p->{runjobs_pars}->{batch_gpu_queue},
        template             => $p->{nlplingo_eer}->{par_file},
        python               => $p->{PYTHON_GPU_NLPLINGO},
        num_of_batches       => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids    => $last_jobs_ptr_en,
        input_serif_list     => $en_input_en_ptr->{file_list},
        custom_driver        => "$p->{TEXT_OPEN_PYTHONPATH_EER}/serif/driver/pipeline.py",
        text_open_pythonpath => "$p->{TEXT_OPEN_PYTHONPATH_EER}",
        template_inject      => {
            hume_root                         => $p->{HUME_RELEASE_DIR},
            max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence}

        },

    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name           => "nlplingo_eer/cn",
        job_queue            => $p->{runjobs_pars}->{batch_gpu_queue},
        template             => $p->{nlplingo_eer}->{par_file},
        python               => $p->{PYTHON_GPU_NLPLINGO},
        num_of_batches       => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids    => $last_jobs_ptr_cn,
        input_serif_list     => $cn_input_en_ptr->{file_list},
        custom_driver        => "$p->{TEXT_OPEN_PYTHONPATH_EER}/serif/driver/pipeline.py",
        text_open_pythonpath => "$p->{TEXT_OPEN_PYTHONPATH_EER}",
        template_inject      => {
            hume_root                         => $p->{HUME_RELEASE_DIR},
            max_number_of_tokens_per_sentence => $p->{max_number_of_tokens_per_sentence}
        },

    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"doctheory_resolver"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = doctheory_resolver(
        job_prefix                         => $p->{job_prefix} . "/doctheory_resolver/en",
        stage_processing_dir               => "$expts/doctheory_resolver/en",
        dependant_job_ids                  => $last_jobs_ptr_en,
        input_serifxml_list                => $en_input_en_ptr->{file_list},
        num_of_batches                     => $en_input_en_ptr->{num_of_batches},
        doctheory_resolver_template        => $p->{doctheory_resolver}->{par_file},
        doctheory_resolver_template_inject => $p->{doctheory_resolver}->{runjobs_par}->{en},
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = doctheory_resolver(
        job_prefix                         => $p->{job_prefix} . "/doctheory_resolver/cn",
        stage_processing_dir               => "$expts/doctheory_resolver/cn",
        dependant_job_ids                  => $last_jobs_ptr_cn,
        input_serifxml_list                => $cn_input_en_ptr->{file_list},
        num_of_batches                     => $cn_input_en_ptr->{num_of_batches},
        doctheory_resolver_template        => $p->{doctheory_resolver}->{par_file},
        doctheory_resolver_template_inject => $p->{doctheory_resolver}->{runjobs_par}->{cn},
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"mtdp"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "mtdp/en",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{mtdp}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list}

    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "mtdp/cn",
        job_queue         => $p->{runjobs_pars}->{batch_gpu_queue},
        template          => $p->{mtdp}->{par_file},
        python            => $p->{PYTHON_GPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list}

    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"entity_coreference"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "entity_coreference/en",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{entity_coreference}->{par_file}->{en},
        python            => $p->{PYTHON_CPU_ALLENNLP},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
        template_inject   => {
            TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
            SGE_VIRTUAL_FREE     => ["15.5G","47.5G","95.5G"]
        }
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "entity_coreference/cn",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{entity_coreference}->{par_file}->{zh},
        python            => $p->{UWCOREF_PYTHON_CPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
        template_inject   => {
            TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
            SGE_VIRTUAL_FREE     => ["15.5G","47.5G","95.5G"]
        }
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"entity_linking"}) {
    # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "entity_linking/en",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{entity_linking}->{par_file}->{en},
        python            => $p->{PYTHON_CPU_SPACY},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
        template_inject   => {
            TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
        }
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "entity_linking/cn",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{entity_linking}->{par_file}->{zh},
        python            => $p->{PYTHON_CPU_SPACY},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
        template_inject   => {
            TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
        }
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"special_pyserif_stage"}){
        # en call
    ($last_jobs_ptr_en, my $en_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "special_pyserif_stage/en",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{special_pyserif_stage}->{par_file}->{en},
        python            => $p->{PYTHON_CPU},
        num_of_batches    => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_en,
        input_serif_list  => $en_input_en_ptr->{file_list},
        template_inject   => {
            TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
        }
    );
    $en_input_en_ptr->{file_list} = $en_serif_list_ptr_local;
    # cn call
    ($last_jobs_ptr_cn, my $cn_serif_list_ptr_local) = pyserif_processing_corpus(
        stage_name        => "special_pyserif_stage/cn",
        job_queue         => $p->{runjobs_pars}->{batch_queue},
        template          => $p->{special_pyserif_stage}->{par_file}->{zh},
        python            => $p->{PYTHON_CPU},
        num_of_batches    => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids => $last_jobs_ptr_cn,
        input_serif_list  => $cn_input_en_ptr->{file_list},
        template_inject   => {
            TEXT_OPEN_PYTHONPATH => $p->{TEXT_OPEN_PYTHONPATH},
        }
    );
    $cn_input_en_ptr->{file_list} = $cn_serif_list_ptr_local;
}

if (exists $stages{"serilize_fillables"}) {
    simple_mapper(
        job_prefix          => "$p->{job_prefix}/serilize_fillables/en",
        output_dir          => "$expts/serilize_fillables/en",
        num_of_batches      => $en_input_en_ptr->{num_of_batches},
        dependant_job_ids   => $last_jobs_ptr_en,
        input_serifxml_list => $en_input_en_ptr->{file_list}
    );
    simple_mapper(
        job_prefix          => "$p->{job_prefix}/serilize_fillables/cn",
        output_dir          => "$expts/serilize_fillables/cn",
        num_of_batches      => $cn_input_en_ptr->{num_of_batches},
        dependant_job_ids   => $last_jobs_ptr_cn,
        input_serifxml_list => $cn_input_en_ptr->{file_list}
    );
}

my $serialization_root = $p->{input_files}->{serialization_root};
my @en_serialization_jobids = ();
my @cn_serialization_jobids = ();
if (exists $stages{"kb_constructor"}) {
    $serialization_root = "$expts/kb_constructor";
    # en call
    @en_serialization_jobids = kb_constructor(
        job_prefix           => "$p->{job_prefix}/kb_constructor/en",
        stage_processing_dir => "$expts/kb_constructor/en",
        dependant_job_ids    => $last_jobs_ptr_en,
        num_of_batches       => $en_input_en_ptr->{num_of_batches},
        input_serifxml_list  => $en_input_en_ptr->{file_list},
        input_metadata_file  => $en_input_en_ptr->{metadata},
        serialize_fillables  => $p->{kb_constructor_par}->{serialize_fillables}
    );
    # cn call
    @cn_serialization_jobids = kb_constructor(
        job_prefix           => "$p->{job_prefix}/kb_constructor/cn",
        stage_processing_dir => "$expts/kb_constructor/cn",
        dependant_job_ids    => $last_jobs_ptr_cn,
        num_of_batches       => $cn_input_en_ptr->{num_of_batches},
        input_serifxml_list  => $cn_input_en_ptr->{file_list},
        input_metadata_file  => $cn_input_en_ptr->{metadata},
        serialize_fillables  => $p->{kb_constructor_par}->{serialize_fillables}
    );
}
if (exists $stages{"merge_visualization_graph"}) {
    my $stage_name = "merge_visualization_graph";
    my $job_prefix = $p->{job_prefix} . "/$stage_name";
    my $stage_processing_dir = "$expts/$stage_name";

    my $merge_eer_json_jobid = runjobs(
        [ @en_serialization_jobids, @cn_serialization_jobids ], "$job_prefix/merge_eer_json",
        {

        },
        [ "mkdir -p $stage_processing_dir" ],
        [ "$p->{PYTHON3_SYSTEM} $p->{LEARNIT_RELEASE_DIR}/HAT/new_backend/utils/aggr_ui_data_from_kb_constructor.py --dir_of_serialization $serialization_root --output_path $stage_processing_dir/output_eer.json" ]
    );
    my $merge_event_frame_jobid = runjobs(
        [ @en_serialization_jobids, @cn_serialization_jobids ], "$job_prefix/merge_event_frame",
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
    my $text_open_pythonpath = $args{text_open_pythonpath} || $p->{TEXT_OPEN_PYTHONPATH};
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
                        TEXT_OPEN_PYTHONPATH => $text_open_pythonpath,
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
                        TEXT_OPEN_PYTHONPATH => $text_open_pythonpath,
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
sub translate {
    my %args = @_;
    my $source_serifxml_list = $args{source_serifxml_list};
    my $number_of_batches = $args{num_of_batches};
    my $dependant_job_ids = $args{dependant_job_ids};
    my $corpus_name = "corpus";
    my $job_prefix = $args{job_prefix};
    my $stage_processing_dir = $args{stage_processing_dir};

    my $convert_serifxml_to_mt_xml_script =
        "$p->{BETTER_RELEASE_DIR}/python/clever/annotation/convert_serifxml_to_mt_input.py";

    my $mt_json_dir = "$stage_processing_dir/final_json";
    my $mt_json_filelist = "$stage_processing_dir/final_json.list";

    my $batch_file_dir = "$stage_processing_dir/batch/batch";
    my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $p->{PYTHON3_SYSTEM},
        CREATE_FILELIST_PY_PATH => "$p->{TEXT_OPEN_PYTHONPATH}/util/common/create_filelist_with_batch_size.py",
        num_of_batches          => $number_of_batches,
        suffix                  => "",
        output_file_prefix      => $batch_file_dir,
        list_file_path          => $source_serifxml_list,
        job_prefix              => "$job_prefix/",
        dependant_job_ids       => $dependant_job_ids,
    );

    my @convert_mt_json_to_docs_job_ids = ();

    for (my $batch = 0; $batch < $number_of_batches; $batch++) {
        my $source_serifxml_batch_filelist = $batch_files[$batch];
        my $batch_job_prefix = "$job_prefix/split/$batch";
        my $batch_processing_dir = "$stage_processing_dir/split/$batch";
        my $untranslated_mt_xml_file =
            "$batch_processing_dir/preprocessing/$corpus_name.$batch.mt.xml";
        my $untranslated_mt_xml_file_gzipped =
            "$batch_processing_dir/preprocessing/$corpus_name.$batch.mt.xml.gz";
        my $convert_serifxml_to_mt_xml_job_id = runjobs(
            $split_jobid,
            "$batch_job_prefix/preprocessing", {},
            [ "mkdir -p $batch_processing_dir/preprocessing" ],
            [ "$p->{PYTHON_CPU} " .
                "$convert_serifxml_to_mt_xml_script " .
                "$source_serifxml_batch_filelist " .
                "$corpus_name " .
                "$untranslated_mt_xml_file " .
                "xml" ],
            [ "gzip $untranslated_mt_xml_file" ]
        );

        ################################
        # NMT DECODE INTEGRATION BEGIN #
        ################################
        # point data to decode in BBN XML format
        # one can decode multiple sets in parallel
        my $decode_data_sets = [
            {
                name       => $corpus_name, # can be any string
                # in the xml, only 'GUID' and input_field below needs to be defined
                input_file => $untranslated_mt_xml_file_gzipped,
                # http://e-gitlab.bbn.com/sage/hycube/issues/2#jsonxml-segment-format
            }
        ];

        my $decode_pars = {
            # where trained model is located
            model_dir                 => $p->{nmt_pars}->{model_dir},
            checkpoint_path           => $p->{nmt_pars}->{checkpoint_path},
            input_field               => "SERIF_TOKENIZED_SOURCE",
            output_field              => "SERIF_TOKENIZED_MT",
            alignment_output_field    => 'SERIF_TOKENIZED_ALIGNMENT',
            data_format               => 'bbn_xml_segment',
            data_sets                 => $decode_data_sets,
            max_output_length         => 1020,

            # Split decoding jobs per data set.
            # This can also be set at per-data-set level
            num_splits                => 1, # use a large number for decoding big set
            # or to run decoding on CPU

            # decoding can run on either CPU or GPU (gpu_queue)
            # Some GPU machines have lower onboard GPU RAM and may give an out of
            # memory error. If this happens, just re-submit the job to another machine.
            run_decoding_on_gpu       => $use_gpus,

            fairseq_generate_params   => {
                print_alignment => '',
            },

            PYTHON_GPU                => $p->{MT_PYTHON_GPU},
            PYTHON                    => $p->{MT_PYTHON_CPU},
            gpu_queue                 => $p->{runjobs_pars}->{batch_gpu_queue},
            CUBE_PM_RELEASE_DIR       => $p->{CUBE_PM_RELEASE_DIR},
            PYCUBE_RELEASE_DIR        => $p->{PYCUBE_RELEASE_DIR},
            FAIRSEQ_RELEASE_DIR       => $p->{FAIRSEQ_RELEASE_DIR},
            TENSOR2TENSOR_RELEASE_DIR => '',
            MOSES_RELEASE_DIR         => '',
            CENTOS7_MOSES             => '',
        };

        my $prev_jobs = [ $convert_serifxml_to_mt_xml_job_id ];
        my $decode = make MT::NmtDecode(
            $prev_jobs, "run",
            {
                dir        => "$batch_processing_dir/run_mt", # directory to store output
                job_prefix => "$batch_job_prefix/run_mt",     # decoding job prefix
                %$decode_pars,
            }
        );

        my $decode_job_id = $decode->{last_jobs};

        ################################
        # NMT DECODE INTEGRATION END   #
        ################################

        ####################################
        # Convert MT output into doc files #
        ####################################

        my $convert_mt_json_to_docs_script =
            "$p->{BETTER_RELEASE_DIR}/python/clever/mt/serif_tokenized_mt_json_to_docs.py";
        my $convert_mt_json_to_docs_job_id = runjobs(
            $decode_job_id,
            "$batch_job_prefix/postprocessing",
            {},
            [
                "$p->{PYTHON_CPU} $convert_mt_json_to_docs_script " .
                    "$batch_processing_dir/run_mt/$corpus_name.json.gz " .
                    "$batch_processing_dir " .
                    "$batch_processing_dir " .
                    "$mt_json_dir " .
                    "none"
            ]
        );
        push @convert_mt_json_to_docs_job_ids, $convert_mt_json_to_docs_job_id;
    }
    my $gather_mt_json_job_ids = runjobs(
        \@convert_mt_json_to_docs_job_ids, "$job_prefix/collect",
        {
            SCRIPT => 1
        },
        [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/create_filelist.py --unix_style_pathname \"$mt_json_dir/*.json\" --output_list_path $mt_json_filelist" ]
    );
    return [ $gather_mt_json_job_ids ], $mt_json_filelist
}

sub doctheory_resolver {
    my %args = @_;
    my $job_prefix = $args{job_prefix};
    my $stage_processing_dir = $args{stage_processing_dir};
    my $dependant_job_ids = $args{dependant_job_ids};
    my $input_serifxml_list = $args{input_serifxml_list};
    my $num_of_batches = $args{num_of_batches};
    my $doctheory_resolver_template_inject = $args{doctheory_resolver_template_inject};
    my $doctheory_resolver_template = $args{doctheory_resolver_template};

    my $batch_file_dir = "$stage_processing_dir/batch/batch";

    my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $p->{PYTHON3_SYSTEM},
        CREATE_FILELIST_PY_PATH => "$p->{TEXT_OPEN_PYTHONPATH}/util/common/create_filelist_with_batch_size.py",
        num_of_batches          => $num_of_batches,
        suffix                  => "",
        output_file_prefix      => $batch_file_dir,
        list_file_path          => $input_serifxml_list,
        job_prefix              => "$job_prefix/",
        dependant_job_ids       => $dependant_job_ids,
    );
    my @doctheory_resolver_jobs = ();
    for (my $n = 0; $n < $num_of_batches; $n++) {
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
                    %{$doctheory_resolver_template_inject}
                },
                [ "mkdir -p $doctheory_resolver_batch_job_output_dir" ],
                [ "env java -cp $p->{HUME_RELEASE_DIR}/src/java/serif-util/target/causeex-serif-util-1.0.0-jar-with-dependencies.jar com.bbn.serif.util.resolver.DocTheoryResolver", $doctheory_resolver_template ]
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
    return [ $gather_results_jobid ], $output_list_path
}

sub simple_mapper {
    my %args = @_;
    my $job_prefix = $args{job_prefix};
    my $stage_processing_dir = $args{output_dir};
    my $num_of_batches = $args{num_of_batches};
    my $dependant_job_ids = $args{dependant_job_ids};
    my $input_serifxml_list = $args{input_serifxml_list};
    my $batch_file_dir = "$stage_processing_dir/batch/batch";
    my $job_output_dir = "$stage_processing_dir/output";

    my ($split_jobid, @batch_files) = Utils::split_file_list_with_num_of_batches(
        PYTHON                  => $p->{PYTHON3_SYSTEM},
        CREATE_FILELIST_PY_PATH => "$p->{TEXT_OPEN_PYTHONPATH}/util/common/create_filelist_with_batch_size.py",
        num_of_batches          => $num_of_batches,
        suffix                  => "",
        output_file_prefix      => $batch_file_dir,
        list_file_path          => $input_serifxml_list,
        job_prefix              => "$job_prefix/",
        dependant_job_ids       => $dependant_job_ids,
    );

    my @simple_mapper_jobs = ();
    for (my $n = 0; $n < $num_of_batches; $n++) {
        my $batch_job_name = "$job_prefix/split/$n";
        my $job_batch_num = $n;
        my $batch_file = $batch_files[$n];
        my $simple_mapper_batch_job_output_dir = "$stage_processing_dir/split/$job_batch_num";
        my $simple_batch_jobid =
            runjobs(
                $split_jobid, $batch_job_name,
                {
                    BATCH_QUEUE => $p->{runjobs_pars}->{batch_queue},

                },
                [ "mkdir -p $simple_mapper_batch_job_output_dir" ],
                [ "env PYTHONPATH=\"$p->{TEXT_OPEN_PYTHONPATH}:\$PYTHONPATH\" $p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/util/new_eer_slot_generator.py --input_serifxml_list $batch_file --output_fillable_eer_path $simple_mapper_batch_job_output_dir/output_eer.info" ]
            );
        push(@simple_mapper_jobs, $simple_batch_jobid);
    }
    my $output_list_path = "$stage_processing_dir/eer_info.list";
    my $gather_results_jobid = runjobs(
        \@simple_mapper_jobs, "$job_prefix/collect",
        {
            SCRIPT => 1
        },
        [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/create_filelist.py --unix_style_pathname \"$stage_processing_dir/split/*/output_eer.info\" --output_list_path $output_list_path" ]
    );
    return [ $gather_results_jobid ], $output_list_path
}

sub kb_constructor {
    my %args = @_;
    my $job_prefix = $args{job_prefix};
    my $stage_processing_dir = $args{stage_processing_dir};
    my $dependant_job_ids = $args{dependant_job_ids};
    my $num_of_batches = $args{num_of_batches};
    my $input_serifxml_list = $args{input_serifxml_list};
    my $input_metadata_file = $args{input_metadata_file};
    my $serialize_fillables = $args{serialize_fillables};

    my $serializer_name = "VisualizationSerializer";
    if ($serialize_fillables) {
        $serializer_name = "FillableTCAGSerializer"
    }

    my $batch_job_dir = "$stage_processing_dir/batch";
    my $job_output_dir = "$stage_processing_dir/output";
    my $copy_serifxml_jobid =
        runjobs(
            $dependant_job_ids, "$job_prefix/creating_batch",
            {
                BATCH_QUEUE => $p->{runjobs_pars}->{batch_queue},
            },
            [ "$p->{PYTHON3_SYSTEM} $p->{HUME_RELEASE_DIR}/src/python/pipeline/scripts/copy_serifxml_by_document_type.py --input_serif_list $input_serifxml_list --output_dir $batch_job_dir --input_metadata_file $input_metadata_file --num_of_batches $num_of_batches" ]
        );
    my @serialization_jobs = ();
    for (my $n = 0; $n < $num_of_batches; $n++) {
        my $batch_job_name = "$job_prefix/split/$n";
        my $batch_job_output = "$job_output_dir/$n";
        my $batch_job_input = "$batch_job_dir/batch_$n";
        my $batch_job_id = runjobs(
            [ $copy_serifxml_jobid ], "$batch_job_name",
            {
                event_coreference_file => "NULL",
                batch_file_dir         => $batch_job_input,
                pickle_output_file     => "$batch_job_output/output.pickle",
                json_graph_file        => "$batch_job_output/visualization",
                SGE_VIRTUAL_FREE       => [ "2G", "4G" ],
                serializer_name        => $serializer_name,
                % {$p->{kb_constructor_par}->{runjobs_par}}
            },
            [ "mkdir -p $batch_job_output" ],
            [ "$p->{kb_constructor_par}->{python} $p->{HUME_RELEASE_DIR}/src/python/knowledge_base/kb_constructor.py", "$p->{kb_constructor_par}->{par_file}" ]
        );
        push(@serialization_jobs, $batch_job_id);
    }
    return @serialization_jobs
}

1;
