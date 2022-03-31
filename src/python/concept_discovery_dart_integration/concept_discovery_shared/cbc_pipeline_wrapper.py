import os
import shlex
import shutil
import subprocess


def modify_run_pl(original_run_pl_path, hume_root, dst_run_pl_path):
    output_buf = list()
    with open(original_run_pl_path) as fp:
        for i in fp:
            if "# $hume_repo_root =" in i:
                output_buf.append("\n")
            elif "$hume_repo_root =" in i:
                output_buf.append("$hume_repo_root = \"{}\";\n".format(hume_root))
            else:
                output_buf.append(i)
    with open(dst_run_pl_path, 'w') as wfp:
        for i in output_buf:
            wfp.write(i)


def setup_runjobs(runjob_experiment_dir):
    shutil.rmtree(runjob_experiment_dir, ignore_errors=True)
    os.makedirs(runjob_experiment_dir, exist_ok=True)
    shutil.rmtree(os.path.join(runjob_experiment_dir, "ckpts"), ignore_errors=True)
    shutil.rmtree(os.path.join(runjob_experiment_dir, "etemplates"), ignore_errors=True)
    shutil.rmtree(os.path.join(runjob_experiment_dir, "expts"), ignore_errors=True)
    shutil.rmtree(os.path.join(runjob_experiment_dir, "logfiles"), ignore_errors=True)
    os.makedirs(os.path.join(runjob_experiment_dir, "ckpts"), exist_ok=True)
    os.makedirs(os.path.join(runjob_experiment_dir, "etemplates"), exist_ok=True)
    os.makedirs(os.path.join(runjob_experiment_dir, "expts"), exist_ok=True)
    os.makedirs(os.path.join(runjob_experiment_dir, "logfiles"), exist_ok=True)


def run_runjobs_stage_2_online(stage_2_dir, saliency_list, ontology_metadata_path, trimmed_annotation_npz,
                               annotation_event_jsonl, hume_repo_root, conda_root,
                               output_dir_path):
    online_service_stage_path = os.path.join(output_dir_path, "online_service")
    shutil.rmtree(online_service_stage_path, ignore_errors=True)
    os.makedirs(online_service_stage_path, exist_ok=True)
    previous_online_service_stage_path = os.path.join(stage_2_dir, 'online_service')
    similarity_dir = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                  'similarity')
    sentence_jsonl_path = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                       'generate_candidates', 'sentence.ljson')
    corpus_annoy_cache_path = os.path.join(previous_online_service_stage_path, 'expts', 'default', 'corpus_cache')
    npz_dir = os.path.join(previous_online_service_stage_path, 'expts', 'default', 'npzs')
    filter_clusters_by_example_file = os.path.join(hume_repo_root, "resource", "wm", "junk_cluster_examples.json")
    # run perl
    setup_runjobs(online_service_stage_path)
    par_file_path = os.path.join(online_service_stage_path, "config.par")
    npz_list_output_path = os.path.join(online_service_stage_path, "npz.list")
    averaged_embeddings_path = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                            'sample_avg_embeddings', 'word_to_ave_emb.npz')
    existing_ontology_cache_path = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                                "build_ontology_cache")
    with open(npz_list_output_path, 'w') as wfp:
        for root, dirs, files in os.walk(npz_dir):
            for file in files:
                if file.endswith(".npz"):
                    wfp.write("{}\n".format(os.path.join(root, file)))
    with open(par_file_path, 'w') as wfp:
        wfp.write("""
job_name: default
stages_to_run: cbc,build-ontology-cache,map-to-ontology,json

ANACONDA_ROOT: {}
saliency_list: {}

similarity_dir: {}
sentence_jsonl: {}
input_npz_list: {}
corpus_cache: {}

averaged_embeddings: {}
ontology_metadata_path: {}
trimmed_annotation_npz: {}
annotation_event_jsonl: {}
existing_ontology_cache: {}

filter_clusters_by_example_file: {}
                """.format(conda_root, saliency_list, similarity_dir, sentence_jsonl_path, npz_list_output_path,
                           corpus_annoy_cache_path, averaged_embeddings_path, ontology_metadata_path,
                           trimmed_annotation_npz, annotation_event_jsonl, existing_ontology_cache_path,
                           filter_clusters_by_example_file))
    modify_run_pl(os.path.join(hume_repo_root, "sequences", "cbc_clustering.pl"), hume_repo_root,
                  os.path.join(hume_repo_root, "sequences", "cbc_clustering_modified.pl"))
    RUNJOB_COPY_ENVIRON = os.environ.copy()
    RUNJOB_COPY_ENVIRON['PWD'] = os.path.join(hume_repo_root)
    subprocess.check_call(shlex.split(
        "env perl sequences/cbc_clustering_modified.pl {} -copy {} {}".format("default", online_service_stage_path,
                                                                              par_file_path)),
        cwd=hume_repo_root, env=RUNJOB_COPY_ENVIRON)

    RUNJOB_RUN_ENVIRON = os.environ.copy()
    RUNJOB_RUN_ENVIRON['PWD'] = os.path.join(online_service_stage_path)
    subprocess.check_call(shlex.split(
        "env perl sequences/sequencescbc_clustering_modified.pl {} -local ".format(par_file_path)),
        cwd=online_service_stage_path, env=RUNJOB_RUN_ENVIRON)


def run_runjobs_stage_2_online_no_recluster(stage_2_dir, previous_cluster_dir, ontology_metadata_path,
                                            trimmed_annotation_npz, annotation_event_jsonl, remaining_clusters_file,
                                            hume_repo_root, conda_root, output_dir_path):
    online_service_stage_path = os.path.join(output_dir_path, "online_service")
    shutil.rmtree(online_service_stage_path, ignore_errors=True)
    os.makedirs(online_service_stage_path, exist_ok=True)
    previous_online_service_stage_path = os.path.join(stage_2_dir, 'online_service')
    previous_cluster_online_service_path = os.path.join(previous_cluster_dir, 'online_service')
    similarity_dir = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                  'similarity')
    sentence_jsonl_path = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                       'generate_candidates', 'sentence.ljson')
    corpus_annoy_cache_path = os.path.join(previous_online_service_stage_path, 'expts', 'default', 'corpus_cache')
    npz_dir = os.path.join(previous_online_service_stage_path, 'expts', 'default', 'npzs')
    filter_clusters_by_example_file = os.path.join(hume_repo_root, "resource", "wm", "junk_cluster_examples.json")

    # run perl
    setup_runjobs(online_service_stage_path)
    par_file_path = os.path.join(online_service_stage_path, "config.par")
    npz_list_output_path = os.path.join(online_service_stage_path, "npz.list")
    averaged_embeddings_path = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                            'sample_avg_embeddings', 'word_to_ave_emb.npz')
    existing_ontology_cache_path = os.path.join(previous_online_service_stage_path, 'expts', 'default',
                                                "build_ontology_cache")
    previous_clusters_path = os.path.join(previous_cluster_online_service_path, 'expts', 'default', 'cbc',
                                          'cbc.finalClustering')
    with open(npz_list_output_path, 'w') as wfp:
        for root, dirs, files in os.walk(npz_dir):
            for file in files:
                if file.endswith(".npz"):
                    wfp.write("{}\n".format(os.path.join(root, file)))
    with open(par_file_path, 'w') as wfp:
        wfp.write("""
job_name: default
stages_to_run: build-ontology-cache,map-to-ontology,json

ANACONDA_ROOT: {}

similarity_dir: {}
sentence_jsonl: {}
input_npz_list: {}
corpus_cache: {}

averaged_embeddings: {}
ontology_metadata_path: {}
trimmed_annotation_npz: {}
annotation_event_jsonl: {}
existing_ontology_cache: {}

cluster_file: {}
remaining_clusters_file: {}
filter_clusters_by_example_file: {}
                """.format(conda_root, similarity_dir, sentence_jsonl_path, npz_list_output_path,
                           corpus_annoy_cache_path, averaged_embeddings_path, ontology_metadata_path,
                           trimmed_annotation_npz, annotation_event_jsonl, existing_ontology_cache_path,
                           previous_clusters_path, remaining_clusters_file,
                           filter_clusters_by_example_file))
    modify_run_pl(os.path.join(hume_repo_root, "sequences", "cbc_clustering.pl"), hume_repo_root,
                  os.path.join(hume_repo_root, "sequences", "cbc_clustering_modified.pl"))
    RUNJOB_COPY_ENVIRON = os.environ.copy()
    RUNJOB_COPY_ENVIRON['PWD'] = os.path.join(hume_repo_root)
    subprocess.check_call(shlex.split(
        "env perl sequences/cbc_clustering_modified.pl {} -copy {} {}".format("default", online_service_stage_path,
                                                                              par_file_path)),
        cwd=hume_repo_root, env=RUNJOB_COPY_ENVIRON)

    RUNJOB_RUN_ENVIRON = os.environ.copy()
    RUNJOB_RUN_ENVIRON['PWD'] = os.path.join(online_service_stage_path)
    subprocess.check_call(shlex.split(
        "env perl sequences/sequencescbc_clustering_modified.pl {} -local ".format(par_file_path)),
        cwd=online_service_stage_path, env=RUNJOB_RUN_ENVIRON)


def run_runjobs_stage_2_full(stage_1_cache_folder, saliency_list, ontology_metadata_path, hume_repo_root, conda_root,
                             trimmed_annotation_npz, event_annotation_jsonl, output_dir_path):
    online_service_stage_path = os.path.join(output_dir_path, "online_service")
    shutil.rmtree(online_service_stage_path, ignore_errors=True)
    os.makedirs(online_service_stage_path, exist_ok=True)
    cserif_distilbert_stage_expt_root = os.path.join(stage_1_cache_folder, 'cserif_distilbert_stage', 'expts',
                                                     'default')
    serif_file_list_path = os.path.join(cserif_distilbert_stage_expt_root, 'serif_serifxml.list')
    bert_npz_path = os.path.join(cserif_distilbert_stage_expt_root, 'distilbert_npz.list')
    ontology_annoy_cache_expt_root = os.path.join(stage_1_cache_folder, "build_ontology_annoy_cache", 'expts',
                                                  'default')
    ontology_annoy_cache_dir = os.path.join(ontology_annoy_cache_expt_root, 'build_ontology_cache')
    averaged_emb_dir = os.path.join(ontology_annoy_cache_expt_root, 'sample_avg_embeddings')
    averaged_embeddings_path = os.path.join(averaged_emb_dir, 'word_to_ave_emb.npz')
    filter_clusters_by_example_file = os.path.join(hume_repo_root, "resource", "wm", "junk_cluster_examples.json")

    # run perl
    # Get SerifXMLs and distilbert
    setup_runjobs(online_service_stage_path)
    par_file_path = os.path.join(online_service_stage_path, "config.par")
    with open(par_file_path, 'w') as wfp:
        wfp.write("""
job_name: default
stages_to_run: generate-candidates,build-corpus-cache,similarity,cbc,build-ontology-cache,map-to-ontology,json

ANACONDA_ROOT: {}

input_npz_list: {}
input_serifxml_list: {}
saliency_list: {}
ontology_cache: {}

averaged_embeddings: {}
ontology_metadata_path: {}
trimmed_annotation_npz: {}
annotation_event_jsonl: {}

filter_clusters_by_example_file: {}
            """.format(conda_root, bert_npz_path, serif_file_list_path, saliency_list, ontology_annoy_cache_dir,
                       averaged_embeddings_path, ontology_metadata_path, trimmed_annotation_npz,
                       event_annotation_jsonl, filter_clusters_by_example_file))
    modify_run_pl(os.path.join(hume_repo_root, "sequences", "cbc_clustering.pl"), hume_repo_root,
                  os.path.join(hume_repo_root, "sequences", "cbc_clustering_modified.pl"))
    RUNJOB_COPY_ENVIRON = os.environ.copy()
    RUNJOB_COPY_ENVIRON['PWD'] = os.path.join(hume_repo_root)
    subprocess.check_call(shlex.split(
        "env perl sequences/cbc_clustering_modified.pl {} -copy {} {}".format("default", online_service_stage_path,
                                                                              par_file_path)),
        cwd=hume_repo_root, env=RUNJOB_COPY_ENVIRON)

    RUNJOB_RUN_ENVIRON = os.environ.copy()
    RUNJOB_RUN_ENVIRON['PWD'] = os.path.join(online_service_stage_path)
    subprocess.check_call(shlex.split(
        "env perl sequences/sequencescbc_clustering_modified.pl {} -local ".format(par_file_path)),
        cwd=online_service_stage_path, env=RUNJOB_RUN_ENVIRON)

    # Copy averaged embeddings to full run of cbc clustering so we can easily ignore the dependency
    shutil.copytree(averaged_emb_dir,
                    os.path.join(online_service_stage_path, 'expts', 'default', 'sample_avg_embeddings'))
    output_npz_root = os.path.join(online_service_stage_path, 'expts', 'default', 'npzs')
    os.makedirs(output_npz_root, exist_ok=True)
    subprocess.check_call(shlex.split("rsync -vrlptP --files-from={} / {}".format(bert_npz_path, output_npz_root)))


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--previous_stage_2_cache_folder', required=True)
    arg_parser.add_argument('--saliency_list', required=True)
    arg_parser.add_argument('--hume_repo_root', required=True)
    arg_parser.add_argument("--conda_root", required=True)
    arg_parser.add_argument('--output_folder', required=True)
    arg_parser.add_argument('--ontology_metadata_path', required=True)
    arg_parser.add_argument('--recluster', action='store_true')
    arg_parser.add_argument('--previous_cluster_folder', required=False)
    arg_parser.add_argument('--remaining_clusters_file', required=False)
    arg_parser.add_argument('--trimmed_annotation_npz', required=True)
    arg_parser.add_argument('--annotation_event_jsonl', required=True)
    args = arg_parser.parse_args()

    if args.recluster:
        run_runjobs_stage_2_online(args.previous_stage_2_cache_folder, args.saliency_list,
                                   args.ontology_metadata_path, args.trimmed_annotation_npz,
                                   args.annotation_event_jsonl, args.hume_repo_root, args.conda_root,
                                   args.output_folder)
    else:
        run_runjobs_stage_2_online_no_recluster(args.previous_stage_2_cache_folder, args.previous_cluster_folder,
                                                args.ontology_metadata_path, args.trimmed_annotation_npz,
                                                args.annotation_event_jsonl, args.remaining_clusters_file,
                                                args.hume_repo_root, args.conda_root, args.output_folder)
    # run_runjobs_stage_2_full(args.previous_stage_2_cache_folder, args.saliency_list, args.ontology_metadata_path,
    #                          args.hume_repo_root, args.conda_root, args.annotation_npz_list,
    #                          args.event_annotation_jsonl, args.output_folder)
