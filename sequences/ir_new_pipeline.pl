#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';

use FindBin qw($Bin $Script);
use Cwd;

use File::Basename;
use File::Path;
use File::Copy;

use Getopt::Long;
use List::Util qw[min max];
use JSON::Parse;

my $textopen_root;
my $hume_repo_root;
my $learnit_root;

BEGIN{
    $textopen_root = "/d4m/nlp/releases/text-open/R2021_08_17";
    # $hume_repo_root = "/d4m/nlp/releases/Hume/R2020_08_06_1";
    $hume_repo_root = Cwd::abs_path(__FILE__ . "/../..");
    $learnit_root = "/nfs/raid88/u10/users/hqiu_ad/repos/learnit";
    unshift(@INC, "/nfs/raid88/u10/users/hqiu_ad/repos_prod/runjobs4/lib");
    unshift(@INC, "$textopen_root/src/perl/text_open/lib");
}
my $PYTHON3 = "/home/hqiu/ld100/miniconda_dev/envs/py3-general/bin/python";
my $learnit_jar_path = "$learnit_root/neolearnit/target/neolearnit-2.0-SNAPSHOT-jar-with-dependencies.jar";

my $ir_proj_root = "$hume_repo_root/src/python/fuzzy_search/similarity/event_and_arg_emb_pairwise";
my $CREATE_FILELIST_PY_PATH = "$textopen_root/src/python/util/common/create_filelist_with_batch_size.py";
use runjobs4;
use Utils;

my $config_path;

Getopt::Long::Configure("pass_through");
GetOptions(
    "params=s" => \$config_path
); #optional for yield view/seed initialization
Getopt::Long::Configure("no_pass_through");

my $config_hash = JSON::Parse::json_file_to_perl($config_path);

my $QUEUE_PRIO = '5'; # Default queue priority
my ($exp_root, $exp) = runjobs4::startjobs("queue_mem_limit" => '15G', "max_memory_over" => '0.5G', "queue_priority" => $QUEUE_PRIO);

my $JOB_NAME = $config_hash->{"runjobs_config"}->{"job_name"};
runjobs4::max_jobs("$JOB_NAME" => 200,);
my $batch_queue = "cpunodes";

(my $processing_dir, undef) = Utils::make_output_dir("$exp_root/expts/$JOB_NAME", "$JOB_NAME/mkdir_job_directory", []);

my $feature_id_to_feature_deps = {};
my $feature_id_to_feature_list = {};

{
    # Extract feature
    my $stage_name = "extract_features";
    (my $stage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    foreach my $feature_extractor_config (@{$config_hash->{"feature_extractors"}}) {
        my $feature_extractor_id = $feature_extractor_config->{"id"};
        my $number_of_batches = $feature_extractor_config->{"number_of_batches"};
        my ($feature_extractor_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$feature_extractor_id", "$JOB_NAME/$stage_name/$feature_extractor_id/mkdir", []);
        my ($feature_extractor_batching_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$feature_extractor_id/batch_file", "$JOB_NAME/$stage_name/$feature_extractor_id/mkdir_batch", []);
        my ($split_jobid, undef) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            num_of_batches          => $number_of_batches,
            suffix                  => "",
            output_file_prefix      => "$feature_extractor_batching_dir/",
            list_file_path          => $feature_extractor_config->{"original_serif_list"},
            job_prefix              => "$JOB_NAME/$stage_name/$feature_extractor_id/",
            dependant_job_ids       => [],
        );
        my @extract_feature_split_jobs = ();
        for (my $n = 0; $n < $number_of_batches; $n++) {
            my $batch_file = "$feature_extractor_batching_dir/$n";
            my ($batch_output_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$feature_extractor_id/$n", "$JOB_NAME/$stage_name/$feature_extractor_id/mkdir_$n", []);
            my $feature_extractor_job_id =
                runjobs4::runjobs(
                    $split_jobid, "$JOB_NAME/$stage_name/$feature_extractor_id/extract_feature_$n",
                    {
                        BATCH_QUEUE       => $batch_queue,
                        serif_list_slice  => $batch_file,
                        output_path       => $batch_output_dir,
                        partial_expansion => 1,
                        learnit_jar_path  => $learnit_jar_path,

                    },
                    [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/pipeline/extracting.py", $config_path, "$feature_extractor_id" ]
                );
            push(@extract_feature_split_jobs, $feature_extractor_job_id);
        }
        my $list_feature_extraction_jobid = runjobs(
            \@extract_feature_split_jobs, "$JOB_NAME/$stage_name/$feature_extractor_id/list_feature_extraction",
            {
                BATCH_QUEUE => $batch_queue,
                SCRIPT      => 1
            },
            [ "find $processing_dir/$stage_name/$feature_extractor_id -type f -name 'features.npz' > $processing_dir/$stage_name/$feature_extractor_id/features.list" ]
        );
        $feature_id_to_feature_deps->{$feature_extractor_id} = [ $list_feature_extraction_jobid ];
        $feature_id_to_feature_list->{$feature_extractor_id} = "$processing_dir/$stage_name/$feature_extractor_id/features.list";
    }
}

{
    # Merge feature
    my $stage_name = "merge_features";
    (my $stage_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name", "$JOB_NAME/$stage_name/mkdir_stage_processing", []);
    foreach my $feature_extractor_config (@{$config_hash->{"feature_extractors"}}) {
        if ($feature_extractor_config->{"need_merge"}) {
            my $feature_extractor_id = $feature_extractor_config->{"id"};
            # We're doing this for avoiding large feature file

            my ($merge_feature_extractor_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$feature_extractor_id", "$JOB_NAME/$stage_name/$feature_extractor_id/mkdir", []);
            my ($merge_feature_batch_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$feature_extractor_id/batch", "$JOB_NAME/$stage_name/$feature_extractor_id/mkdir_batch", []);
            my $create_feature_batch_index_jobid = runjobs4::runjobs(
                $feature_id_to_feature_deps->{$feature_extractor_id},
                "$JOB_NAME/$stage_name/$feature_extractor_id/divide_feature_into_list",
                {
                    BATCH_QUEUE        => $batch_queue,
                    partial_expansion  => 1,
                    input_feature_list => $feature_id_to_feature_list->{$feature_extractor_id},
                    output_path        => $merge_feature_batch_processing_dir
                },
                [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/utils/create_feature_batches.py", $config_path, "$feature_extractor_id" ]
            );
            my $number_of_batches = $feature_extractor_config->{"number_of_batches"};
            my @merge_feature_jobs = ();
            for (my $n = 0; $n < $number_of_batches; $n++) {
                my $batch_file = "$merge_feature_batch_processing_dir/$n.list";
                my ($batch_output_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$feature_extractor_id/$n", "$JOB_NAME/$stage_name/$feature_extractor_id/$n/mkdir", []);
                my $merge_feature_extractor_job_id =
                    runjobs4::runjobs(
                        [ $create_feature_batch_index_jobid ], "$JOB_NAME/$stage_name/$feature_extractor_id/merge_feature_$n",
                        {
                            BATCH_QUEUE        => $batch_queue,
                            partial_expansion  => 1,
                            input_feature_list => $feature_id_to_feature_list->{$feature_extractor_id},
                            output_path        => "$batch_output_dir"
                        },
                        [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/pipeline/extracting_merger.py", $config_path, "$feature_extractor_id $batch_file" ]
                    );
                push(@merge_feature_jobs, $merge_feature_extractor_job_id);
            }

            my $list_feature_extraction_jobid = runjobs(
                \@merge_feature_jobs, "$JOB_NAME/$stage_name/$feature_extractor_id/list_feature_extraction",
                {
                    BATCH_QUEUE => $batch_queue,
                    SCRIPT      => 1
                },
                [ "find $merge_feature_extractor_processing_dir -type f -name 'features.npz' > $processing_dir/$stage_name/$feature_extractor_id/features.list" ]
            );
            $feature_id_to_feature_deps->{$feature_extractor_id} = [ $list_feature_extraction_jobid ];
            $feature_id_to_feature_list->{$feature_extractor_id} = "$processing_dir/$stage_name/$feature_extractor_id/features.list";
        }

    }
}


my $index_id_to_dep = {};
my $index_id_to_list = {};

{
    # Build Index
    my $stage_name = "build_index";
    foreach my $index_ctr_obj (@{$config_hash->{"indexing_features"}}) {
        my $index_id = $index_ctr_obj->{"id"};
        my $feature_id = $index_ctr_obj->{"feature_id"};
        my $number_of_batches = $index_ctr_obj->{"number_of_batches"};
        my ($index_processing_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$index_id", "$JOB_NAME/$stage_name/$index_id/mkdir", []);
        my ($index_batching_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$index_id/batch_file", "$JOB_NAME/$stage_name/$index_id/mkdir_batch", []);
        my $feature_list;
        my $dep_jobs = [];

        if ($feature_id_to_feature_deps->{$feature_id}) {
            $feature_list = $feature_id_to_feature_list->{$feature_id};
            $dep_jobs = $feature_id_to_feature_deps->{$feature_id};
        }
        my ($split_jobid, undef) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            num_of_batches          => $number_of_batches,
            suffix                  => "",
            output_file_prefix      => "$index_batching_dir/",
            list_file_path          => $feature_list,
            job_prefix              => "$JOB_NAME/$stage_name/$index_id/",
            dependant_job_ids       => $dep_jobs,
        );
        my @index_split_jobs = ();
        for (my $n = 0; $n < $number_of_batches; $n++) {
            my $batch_file = "$index_batching_dir/$n";
            my ($batch_output_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$index_id/$n", "$JOB_NAME/$stage_name/$index_id/mkdir_$n", []);
            my $index_job_id =
                runjobs4::runjobs(
                    $split_jobid, "$JOB_NAME/$stage_name/$index_id/build_index_$n",
                    {
                        BATCH_QUEUE        => $batch_queue,
                        input_feature_list => "$batch_file",
                        output_path        => "$batch_output_dir",
                        partial_expansion  => 1,
                    },
                    [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/pipeline/indexing.py", $config_path, "$index_id" ]
                );
            push(@index_split_jobs, $index_job_id);
        }
        my $list_index_jobid = runjobs(
            \@index_split_jobs, "$JOB_NAME/$stage_name/$index_id/list_index",
            {
                BATCH_QUEUE => $batch_queue,
                SCRIPT      => 1
            },
            [ "find $processing_dir/$stage_name/$index_id -type f -name 'cache_config.json' > $processing_dir/$stage_name/$index_id/index.list" ]
        );
        $index_id_to_dep->{$index_id} = [ $list_index_jobid ];
        $index_id_to_list->{$index_id} = "$processing_dir/$stage_name/$index_id/index.list";
    }
}
my $query_id_to_dep = {};
my $query_id_to_list = {};


{
    # query and build similarity matrix
    my $stage_name = "querying";
    foreach my $query_obj (@{$config_hash->{"queries"}}) {
        my $query_id = $query_obj->{"id"};
        my $index_id = $query_obj->{"index_id"};
        my $dep_index_jobs = [];
        my $cache_list_path;
        if ($query_obj->{"index_cache_list"}) {
            $cache_list_path = $query_obj->{"index_cache_list"};
        }
        elsif ($index_id_to_dep->{$index_id}) {
            $dep_index_jobs = $index_id_to_dep->{$index_id};
            $cache_list_path = $index_id_to_list->{$index_id};
        }
        my $query_feature_id = $query_obj->{"query_feature_id"};
        my $dep_feature_jobs = [];
        my $feature_list_path;
        if ($feature_id_to_feature_deps->{$query_feature_id}) {
            $dep_feature_jobs = $feature_id_to_feature_deps->{$query_feature_id};
            $feature_list_path = $feature_id_to_feature_list->{$query_feature_id};
        }
        my $number_of_batches = $query_obj->{"number_of_batches"};
        my ($query_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$query_id", "$JOB_NAME/$stage_name/$query_id/mkdir", []);
        my ($query_batching_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$query_id/batch_file", "$JOB_NAME/$stage_name/$query_id/mkdir_batch", []);
        my ($split_jobid, undef) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            num_of_batches          => $number_of_batches,
            suffix                  => "",
            output_file_prefix      => "$query_batching_dir/",
            list_file_path          => $feature_list_path,
            job_prefix              => "$JOB_NAME/$stage_name/$query_id/",
            dependant_job_ids       => $dep_feature_jobs,
        );

        my @waiting_jobs = ();
        foreach my $split_jobid_i (@{$split_jobid}) {
            push(@waiting_jobs, $split_jobid_i);
        }
        foreach my $index_jobid (@{$dep_index_jobs}) {
            push(@waiting_jobs, $index_jobid);
        }

        my @query_split_jobs = ();
        for (my $n = 0; $n < $number_of_batches; $n++) {
            my $batch_file = "$query_batching_dir/$n";
            my ($batch_output_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$query_id/$n", "$JOB_NAME/$stage_name/$query_id/mkdir_$n", []);

            my $query_job_id =
                runjobs4::runjobs(
                    \@waiting_jobs, "$JOB_NAME/$stage_name/$query_id/query_$n",
                    {
                        BATCH_QUEUE        => $batch_queue,
                        partial_expansion  => 1,
                        query_feature_list => $batch_file,
                        input_cache_list   => $cache_list_path,
                        output_path        => $batch_output_dir
                    },
                    [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/pipeline/querying.py", $config_path, "$query_id" ]
                );
            push(@query_split_jobs, $query_job_id);
        }
        my $list_query_jobid = runjobs(
            \@query_split_jobs, "$JOB_NAME/$stage_name/$query_id/list_query",
            {
                BATCH_QUEUE => $batch_queue,
                SCRIPT      => 1
            },
            [ "find $processing_dir/$stage_name/$query_id -type f -name 'sim.npz' > $processing_dir/$stage_name/$query_id/query.list" ]
        );
        $query_id_to_dep->{$query_id} = [ $list_query_jobid ];
        $query_id_to_list->{$query_id} = "$processing_dir/$stage_name/$query_id/query.list";
    }
}

{
    # dump
    my $stage_name = "dumping";
    foreach my $dumpers_obj (@{$config_hash->{"dumpers"}}) {
        my $dumper_id = $dumpers_obj->{"id"};
        my $query_obj;
        foreach my $query_i (@{$config_hash->{"queries"}}) {
            if ($query_i->{"id"} eq $dumpers_obj->{"query_id"}) {
                $query_obj = $query_i;
                last;
            }
        }
        my $index_feature_obj;
        foreach my $index_i (@{$config_hash->{"indexing_features"}}) {
            if ($index_i->{"id"} eq $query_obj->{"index_id"}) {
                $index_feature_obj = $index_i;
                last;
            }
        }
        my $index_feature_list;
        my $index_feature_id = undef;
        if ($dumpers_obj->{"index_feature_list"}) {
            $index_feature_list = $dumpers_obj->{"index_feature_list"};
        }
        elsif ($query_obj->{"index_feature_list"}) {
            $index_feature_list = $query_obj->{"index_feature_list"};
        }
        else {
            $index_feature_list = $feature_id_to_feature_list->{$index_feature_obj->{"feature_id"}};
            $index_feature_id = $index_feature_obj->{"feature_id"};
        }

        my $query_feature_list = $feature_id_to_feature_list->{$query_obj->{"query_feature_id"}};
        my @previous_query_jobs = ();

        my $number_of_batches = $query_obj->{"number_of_batches"};
        my ($dumper_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$dumper_id", "$JOB_NAME/$stage_name/$dumper_id/mkdir", []);
        my ($dumper_batch_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$dumper_id/batch_file", "$JOB_NAME/$stage_name/$dumper_id/mkdir_batch", []);

        my $query_list;
        if ($query_id_to_dep->{$dumpers_obj->{"query_id"}}) {
            foreach my $query_jobid (@{$query_id_to_dep->{$dumpers_obj->{"query_id"}}}) {
                push(@previous_query_jobs, $query_jobid);
            }
            $query_list = $query_id_to_list->{$dumpers_obj->{"query_id"}};
        }
        if ($dumpers_obj->{"merge_feature_list"}) {
            my ($merge_feature_list_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$dumper_id", "$JOB_NAME/$stage_name/$dumper_id/mkdir_merge_feature_list", []);
            my $dep_jobs = [];
            if ($index_feature_id) {
                $dep_jobs = $feature_id_to_feature_deps->{$index_feature_id};
            }
            my $merge_feature_list_job_id =
                runjobs4::runjobs(
                    $dep_jobs, "$JOB_NAME/$stage_name/$dumper_id/merge_feature_list",
                    {
                        BATCH_QUEUE       => $batch_queue,
                        partial_expansion => 1,
                        SGE_VIRTUAL_FREE  => ["16G","64G","128G","160G"]
                    },
                    [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/utils/merge_feature_list.py $index_feature_list $merge_feature_list_dir" ]
                );
            my $list_feature_merging_jobid = runjobs(
                [ $merge_feature_list_job_id ], "$JOB_NAME/$stage_name/$dumper_id/list_feature_merging",
                {
                    BATCH_QUEUE      => $batch_queue,
                    SCRIPT           => 1
                },
                [ "find $merge_feature_list_dir -type f -name 'features.npz' > $merge_feature_list_dir/features.list" ]
            );
            $index_feature_list = "$merge_feature_list_dir/features.list";
            push(@previous_query_jobs, $list_feature_merging_jobid);
        }
        my ($split_jobid, undef) = Utils::split_file_list_with_num_of_batches(
            PYTHON                  => $PYTHON3,
            CREATE_FILELIST_PY_PATH => $CREATE_FILELIST_PY_PATH,
            num_of_batches          => $number_of_batches,
            suffix                  => "",
            output_file_prefix      => "$dumper_batch_dir/",
            list_file_path          => $query_list,
            job_prefix              => "$JOB_NAME/$stage_name/$dumper_id/",
            dependant_job_ids       => \@previous_query_jobs,
        );
        for (my $n = 0; $n < $number_of_batches; $n++) {
            my $batch_file = "$dumper_batch_dir/$n";
            my ($batch_output_dir, undef) = Utils::make_output_dir("$processing_dir/$stage_name/$dumper_id/$n", "$JOB_NAME/$stage_name/$dumper_id/mkdir_$n", []);
            my $dump_job_id =
                runjobs4::runjobs(
                    $split_jobid, "$JOB_NAME/$stage_name/$dumper_id/dump_$n",
                    {
                        BATCH_QUEUE           => $batch_queue,
                        partial_expansion     => 1,
                        input_sim_matrix_list => $batch_file,
                        query_feature_list    => $query_feature_list,
                        index_feature_list    => $index_feature_list,
                        output_path           => $batch_output_dir,
                        SGE_VIRTUAL_FREE  => ["16G","64G","128G","160G"]
                    },
                    [ "env PYTHONPATH=$textopen_root/src/python $PYTHON3 $ir_proj_root/pipeline/dumping.py", $config_path, "$dumper_id" ]
                );
        }
    }
}


runjobs4::dojobs();
runjobs4::endjobs();

sub get_expanded_template_path {
    my $template_file_name = $_[0];
    my $exp_root = $_[1];
    my $exp = $_[2];
    my $job_name = $_[3];
    (my $basic_file_name, undef, undef) = fileparse($template_file_name);
    (my $job_name_leaf, my $job_name_root, undef) = fileparse($job_name);
    my $expanded_template_path = "$exp_root/etemplates/$job_name_root/$exp-$job_name_leaf.$basic_file_name";
    return $expanded_template_path;
}


1;