#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';
use FindBin qw($Bin $Script);
use Cwd;

use lib Cwd::abs_path(__FILE__ . "/../../../text-open/src/perl/text_open/");

use lib::constants;
use lib::Utils;

my $config_file = $ARGV[0];
my $params = Utils::load_params($config_file); # $params is a hash reference

my $hume_root = Cwd::abs_path(__FILE__ . "/../../");

constants::assemble_par({
    "project_roots" => {
        "hume" => $hume_root
    }
});

my $JOB_NAME = Utils::get_param($params, "job_name");

my ($exp_root, $exp) = runjobs4::startjobs("queue_mem_limit" => '8G', "max_memory_over" => '0.5G');
runjobs4::max_jobs("$JOB_NAME" => 250,);
my $processing_dir = Utils::make_output_dir("$exp_root/expts/$JOB_NAME");

my $SERIF_PROCESSING_BATCH_SIZE = Utils::get_param($params, "serif_batch_size", 25);
my $PAIRWISE_QUERY_BATCH_SIZE = Utils::get_param($params, "pairwise_batch_size", 1);
my $LINUX_QUEUE = Utils::get_param($params, "cpu_queue", "nongale-sl6");

my $unmanaged_external_dependencies_root = "/nfs/raid87/u11/users/hqiu/external_dependencies_unmanaged";
my $ANACONDA_ROOT = "$unmanaged_external_dependencies_root/anaconda";
my $CONDA_ENV_FOR_FUZZY_SEARCH = "py3-ml-general";
my $PY_SERIFXML_PATH = Cwd::abs_path(constants::get_par()->{"project_roots"}->{"text_open"}) . "/src/python";

my $PYTHON3_FOR_FUZZY_SEARCH = "env PYTHONPATH=$PY_SERIFXML_PATH:\$PYTHONPATH $ANACONDA_ROOT/envs/$CONDA_ENV_FOR_FUZZY_SEARCH/bin/python";
my $event_and_event_arg_emb_entry_script = "$hume_root/src/python/fuzzy_search/similarity/event_and_arg_emb_pairwise/run.py";

# Share variable area

my $feature_npz_list = "$processing_dir/features.list"; # This is seperate feature list
my $list_generate_all_serifxml_features_npz_jobid;
my $annoy_cache_dir = Utils::make_output_dir("$processing_dir/build_annoy_cache");
my $merged_feature_npz_list = "$processing_dir/merged_features.list"; # This is merged feature list
# End share variable area


{
    # Step 1: Dump serifxml into features

    my $stage_name = "dump_serifxml_into_pairwise_similarity_cache";
    my $stage_processing_dir = Utils::make_output_dir("$processing_dir/$stage_name");
    my $input_serif_list = Utils::get_param($params, "input_serif_list");
    my $input_serif_npz_dir = Utils::get_param($params, "input_serif_npz_dir");
    my $input_bert_npz_list = Utils::get_param($params, "input_bert_npz_list");
    my $key_getter_str = Utils::get_param($params, "key_getter_str");

    my $stage_batch_folder = Utils::make_output_dir("$stage_processing_dir/batch_files");

    my ($NUM_JOBS, $split_job_id) = Utils::split_file_for_processing("$JOB_NAME/$stage_name/split_job", $input_serif_list, "$stage_batch_folder/", $SERIF_PROCESSING_BATCH_SIZE);

    my @feature_extraction_jobs = ();
    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$stage_batch_folder/$job_batch_num";
        my $batch_runtime_output_folder = Utils::make_output_dir("$stage_processing_dir/$job_batch_num");
        my $batch_feature_list = "$batch_runtime_output_folder/features.list";

        my $feature_output_dir = Utils::make_output_dir("$batch_runtime_output_folder/features_dir");
        my $annoy_cache_output_dir = Utils::make_output_dir("$batch_runtime_output_folder/annoy_cache");
        my $dump_serifxml_into_features_split_jobid = runjobs4::runjobs(
            [ $split_job_id ], "$JOB_NAME/$stage_name/$job_batch_num/dump_serifxml_into_features",
            {
                BATCH_QUEUE      => $LINUX_QUEUE,
                SGE_VIRTUAL_FREE => "8G",
            },
            [ "$PYTHON3_FOR_FUZZY_SEARCH $event_and_event_arg_emb_entry_script --mode BUILD_SERIF_DOC_NLPLINGO_FEATURE --input_serif_list $batch_file --input_serif_npz_dir $input_serif_npz_dir --output_path $feature_output_dir --output_prefix $job_batch_num --key_getter_str $key_getter_str --input_bert_npz_list $input_bert_npz_list" ]
        );
        push(@feature_extraction_jobs, $dump_serifxml_into_features_split_jobid);

    }

    $list_generate_all_serifxml_features_npz_jobid = Utils::generate_file_list(\@feature_extraction_jobs, "$JOB_NAME/$stage_name/dump_serifxml_into_features_generate_npz_list_all", "$stage_processing_dir/*/features_dir/*features.npz", $feature_npz_list);
}
{
    # Step 2: Build Annoy cache
    my $stage_name = "build_annoy_cache";
    my $stage_processing_dir = $annoy_cache_dir;
    my $annoy_metric = Utils::get_param($params, "annoy_metric");
    my $n_trees = Utils::get_param($params, "n_trees");

    my $build_annoy_index_jobid = runjobs4::runjobs(
        [ $list_generate_all_serifxml_features_npz_jobid ], "$JOB_NAME/$stage_name/build_annoy_index",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "64G",
        },
        [ "$PYTHON3_FOR_FUZZY_SEARCH $event_and_event_arg_emb_entry_script --mode BUILD_ANNOY_INDEX --input_feature_list $feature_npz_list --annoy_metric $annoy_metric --n_trees $n_trees --output_path $stage_processing_dir" ]
    );

    my $shrink_and_merge_feature_file_jobid = runjobs4::runjobs(
        [$list_generate_all_serifxml_features_npz_jobid],"$JOB_NAME/$stage_name/shrink_and_merge_feature_file",
        {
            BATCH_QUEUE      => $LINUX_QUEUE,
            SGE_VIRTUAL_FREE => "32G",
        },
        ["$PYTHON3_FOR_FUZZY_SEARCH $event_and_event_arg_emb_entry_script --mode MERGE_FEATURE_NPZ --input_feature_list $feature_npz_list --should_drop_features_array_when_merging true --output_path $stage_processing_dir/merged_feature.npz"]
    );


    my $list_annoy_cache_jobid = Utils::generate_file_list([ $build_annoy_index_jobid ], "$JOB_NAME/$stage_name/build_annoy_cache_list", "$stage_processing_dir/*.ann", "$stage_processing_dir/annoy_cache.list");

    my $list_merged_npz_jobid = Utils::generate_file_list([$shrink_and_merge_feature_file_jobid],"$JOB_NAME/$stage_name/merged_feature_npz_list","$stage_processing_dir/merged_feature.npz",$merged_feature_npz_list)
}
runjobs4::dojobs();
{
    # Step 3: Build similarity cache

    my $stage_name = "build_pairwise_cache";
    my $threshold = Utils::get_param($params, "threshold");
    my $cutoff = Utils::get_param($params, "cutoff");
    my $annoy_metric = Utils::get_param($params, "annoy_metric");
    my $key_getter_str = Utils::get_param($params, "key_getter_str");

    my $stage_processing_dir = Utils::make_output_dir("$processing_dir/$stage_name");
    my $stage_output_dir = Utils::make_output_dir("$stage_processing_dir/output");
    my $stage_batch_folder = Utils::make_output_dir("$stage_processing_dir/batch_files");
    my $annoy_cache_list = "$annoy_cache_dir/annoy_cache.list";
    my $feature_name_to_dimension_path = "$annoy_cache_dir/feature_name_to_dimension.npz";
    my $feature_id_to_annoy_idx_npz_path = "$annoy_cache_dir/feature_id_to_annoy_idx.npz";
    my ($NUM_JOBS, $split_job_id) = Utils::split_file_for_processing("$JOB_NAME/$stage_name/split_job", $feature_npz_list, "$stage_batch_folder/", $PAIRWISE_QUERY_BATCH_SIZE);

    for (my $n = 0; $n < $NUM_JOBS; $n++) {
        my $job_batch_num = sprintf("%05d", $n);
        my $batch_file = "$stage_batch_folder/$job_batch_num";
        my $pairwise_output_path = "$stage_output_dir/$job_batch_num" . "_sim.npz";
        my $pairwise_dump_path = "$stage_output_dir/$job_batch_num" . "_dump.log";
        my $build_pairwise_cache_jobid = runjobs4::runjobs(
            [ $split_job_id ], "$JOB_NAME/$stage_name/build_pairwise_cache_$job_batch_num",
            {
                BATCH_QUEUE      => $LINUX_QUEUE,
                SGE_VIRTUAL_FREE => "48G",
            },
            [ "$PYTHON3_FOR_FUZZY_SEARCH $event_and_event_arg_emb_entry_script --mode BUILD_PAIRWISE_CACHE --input_feature_list $batch_file --output_path $pairwise_output_path --key_getter_str $key_getter_str --annoy_metric $annoy_metric --input_annoy_cache_list $annoy_cache_list --feature_name_to_dimension_path $feature_name_to_dimension_path --feature_id_to_annoy_idx_path $feature_id_to_annoy_idx_npz_path --threshold $threshold --cutoff $cutoff" ]
        );
        my $dump_pairwise_jobid = runjobs4::runjobs(
            [ $build_pairwise_cache_jobid ], "$JOB_NAME/$stage_name/dump_pairwise_result_$job_batch_num",
            {
                BATCH_QUEUE      => $LINUX_QUEUE,
                SGE_VIRTUAL_FREE => "16G",
            },
            [ "$PYTHON3_FOR_FUZZY_SEARCH $event_and_event_arg_emb_entry_script --mode DUMP_PAIRWISE_CACHE_TO_FILE --input_feature_list $merged_feature_npz_list --sim_matrix_path $pairwise_output_path --output_path $pairwise_dump_path" ]
        );
    }
}
runjobs4::dojobs();
runjobs4::endjobs();

1;