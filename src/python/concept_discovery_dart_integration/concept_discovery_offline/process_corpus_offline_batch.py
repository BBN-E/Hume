import argparse
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from concept_discovery_shared.cbc_pipeline_wrapper import run_runjobs_stage_2_full
from concept_discovery_shared.cdr_cache import CDRCache

logger = logging.getLogger(__name__)


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


def run_runjobs_stage_1_part1(conda_root, ontology_metadata_path, cdr_list_path, hume_repo_root, num_of_jobs_for_nn,
                              output_dir_path, local_mode, use_regrounding_cache, regrounding_cache_path, from_docker):
    cdr_list = list()
    with open(cdr_list_path) as fp:
        for i in fp:
            p = i.strip()
            cdr_list.append([p, os.stat(p).st_size])
    if len(cdr_list) < 1:
        return
    total_file_size = sum((x[1] for x in cdr_list))
    total_file_size_in_mb = total_file_size / 1024 / 1024
    num_of_batches_in_size = int(total_file_size_in_mb * 0.5)
    adjusted_num_of_batches = num_of_jobs_for_nn
    adjusted_num_of_batches = max(num_of_batches_in_size, adjusted_num_of_batches)
    # run perl
    # Get SerifXMLs and distilbert
    cserif_distilbert_stage_path = os.path.join(output_dir_path, "cserif_distilbert_stage")
    setup_runjobs(cserif_distilbert_stage_path)
    par_file_path = os.path.join(cserif_distilbert_stage_path, "config.par")
    with open(par_file_path, 'w') as wfp:
        wfp.write("""
job_name: default
stages_to_run: cdr-ingestion,serif,distilbert
mode: WorldModelers
use_compositional_ontology: true
only_cpu_available: true
single_bert_thread_mode: {}
use_distilbert: true
ANACONDA_ROOT: {}

num_of_batches_global: {}
max_number_of_tokens_per_sentence: 128

input_cdr_list: {}
breaking_point: 10000
metadata_file: GENERATED

serif_input_sgm_list: GENERATED
serif_input_awake_db: /nfs/raid87/u10/shared/Hume/common/serif/wm_eval_before_060119.sqlite
serif_fast_mode: true
use_cserif: true
distilbert_input_serifxml_list: GENERATED
external_ontology_path: {}
external_ontology_version: DOESNOT_MATTER
use_regrounding_cache: {}
regrounding_cache_path: {}
use_basic_cipher_stream: {}
        """.format("true" if local_mode is True else "false", conda_root, adjusted_num_of_batches, cdr_list_path,
                   ontology_metadata_path, "true" if use_regrounding_cache else "false", regrounding_cache_path,
                   from_docker))
    modify_run_pl(os.path.join(hume_repo_root, "sequences", "run.pl"), hume_repo_root,
                  os.path.join(hume_repo_root, "sequences", "run_modified.pl"))
    RUNJOB_COPY_ENVIRON = os.environ.copy()
    RUNJOB_COPY_ENVIRON['PWD'] = os.path.join(hume_repo_root)
    subprocess.check_call(shlex.split(
        "env perl sequences/run_modified.pl {} -copy {} {}".format("default", cserif_distilbert_stage_path,
                                                                   par_file_path)),
        cwd=hume_repo_root, env=RUNJOB_COPY_ENVIRON)

    RUNJOB_RUN_ENVIRON = os.environ.copy()
    RUNJOB_RUN_ENVIRON['PWD'] = os.path.join(cserif_distilbert_stage_path)
    runtime_flag = "-sge"
    if local_mode:
        runtime_flag = "-local"
    subprocess.check_call(shlex.split(
        "env perl sequences/sequencesrun_modified.pl {} {} ".format(par_file_path, runtime_flag)),
        cwd=cserif_distilbert_stage_path, env=RUNJOB_RUN_ENVIRON)


# build_ontology_annoy_cache_stage
def run_runjobs_stage_1_part2(hume_repo_root, conda_root, output_dir_path, local_mode):
    cserif_distilbert_stage_path = os.path.join(output_dir_path, "cserif_distilbert_stage")
    stage_1_expt_root = os.path.join(cserif_distilbert_stage_path, 'expts', 'default')
    serif_file_list_path = os.path.join(stage_1_expt_root, 'serif_serifxml.list')
    bert_npz_path = os.path.join(stage_1_expt_root, 'distilbert_npz.list')
    build_ontology_annoy_cache_stage_path = os.path.join(output_dir_path, "build_ontology_annoy_cache")
    setup_runjobs(build_ontology_annoy_cache_stage_path)
    par_file_path = os.path.join(build_ontology_annoy_cache_stage_path, "config.par")
    with open(par_file_path, 'w') as wfp:
        wfp.write("""
job_name: default
stages_to_run: generate-candidates,sample-avg-embeddings

ANACONDA_ROOT: {}

input_npz_list: {}
input_serifxml_list: {}
        """.format(conda_root, bert_npz_path, serif_file_list_path))
    RUNJOB_COPY_ENVIRON = os.environ.copy()
    RUNJOB_COPY_ENVIRON['PWD'] = os.path.join(hume_repo_root)
    modify_run_pl(os.path.join(hume_repo_root, "sequences", "cbc_cluster_to_ontology_mapping.pl"), hume_repo_root,
                  os.path.join(hume_repo_root, "sequences", "cbc_cluster_to_ontology_mapping_modified.pl"))
    subprocess.check_call(shlex.split(
        "env perl sequences/cbc_cluster_to_ontology_mapping_modified.pl {} -copy {} {}".format("default",
                                                                                               build_ontology_annoy_cache_stage_path,
                                                                                               par_file_path)),
        cwd=hume_repo_root, env=RUNJOB_COPY_ENVIRON)

    RUNJOB_RUN_ENVIRON = os.environ.copy()
    RUNJOB_RUN_ENVIRON['PWD'] = os.path.join(build_ontology_annoy_cache_stage_path)
    runtime_mode = "-sge"
    if local_mode:
        runtime_mode = "-local"
    subprocess.check_call(shlex.split(
        "env perl sequences/sequencescbc_cluster_to_ontology_mapping_modified.pl {} {} ".format(par_file_path,
                                                                                                runtime_mode)),
        cwd=build_ontology_annoy_cache_stage_path, env=RUNJOB_RUN_ENVIRON)


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--cdr_job_info',
                            required=True)
    arg_parser.add_argument('--hume_repo_root', required=True)
    arg_parser.add_argument("--conda_root", required=True)
    arg_parser.add_argument('--output_dir',
                            required=True)
    arg_parser.add_argument('--saliency_list',
                            required=True)
    arg_parser.add_argument("--num_batches", type=int, default=10)
    arg_parser.add_argument('--ontology_metadata_path', default=None)
    arg_parser.add_argument('--trimmed_annotation_npz',
                            required=True)
    arg_parser.add_argument('--event_annotation_jsonl',
                            required=True)
    arg_parser.add_argument('--previous_stage_2_cache_folder', required=False, default=None)
    arg_parser.add_argument('--use_local_mode', type=str, required=False, default="false")
    arg_parser.add_argument('--use_regrounding_cache', type=str, required=False, default="false")
    arg_parser.add_argument('--regrounding_cache_path', type=str, required=False, default="NON_EXISTED_PATH")
    args = arg_parser.parse_args()

    cdr_job_info = args.cdr_job_info
    hume_repo_root = args.hume_repo_root
    conda_root = args.conda_root
    num_batches = args.num_batches
    output_dir = args.output_dir
    saliency_list = args.saliency_list
    trimmed_annotation_npz = args.trimmed_annotation_npz
    annotation_jsonl = args.event_annotation_jsonl
    previous_stage_2_cache_folder = args.previous_stage_2_cache_folder
    local_mode = args.use_local_mode.lower() == "true"
    use_regrounding_cache = args.use_regrounding_cache.lower() == "true"
    regrounding_cache_path = args.regrounding_cache_path

    stage1_output_dir = "{}-p1".format(output_dir)
    stage2_output_dir = "{}-p2".format(output_dir)
    os.makedirs(stage1_output_dir, exist_ok=True)
    input_cdr_list = os.path.join(stage1_output_dir, "cdrs.list")

    with open(cdr_job_info) as fp:
        cdr_job_info_d = json.load(fp)

    cdr_cache = CDRCache(cdr_job_info_d["cdr_cache_dir"], url=cdr_job_info_d["CDR_retrieval"],
                         username=cdr_job_info_d.get("auth", dict()).get("username", None),
                         password=cdr_job_info_d.get("auth", dict()).get("password", dict()))
    cdr_cache.get_cdr_list_from_uuid_list(cdr_job_info_d["doc_uuids"], input_cdr_list)

    if args.ontology_metadata_path is not None:
        ontology_metadata_path = args.ontology_metadata_path
    else:
        ontology_metadata_path = os.path.join(hume_repo_root,
                                              "resource/dependencies/probabilistic_grounding/WM_Ontologies/CompositionalOntology_metadata.yml")

    from_docker = "true" if os.path.exists("/.dockerenv") else "false"

    run_runjobs_stage_1_part1(conda_root, ontology_metadata_path, input_cdr_list, hume_repo_root, num_batches,
                              stage1_output_dir, local_mode, use_regrounding_cache, regrounding_cache_path, from_docker)
    run_runjobs_stage_1_part2(hume_repo_root, conda_root, stage1_output_dir, local_mode)
    run_runjobs_stage_2_full(stage1_output_dir, saliency_list, ontology_metadata_path, hume_repo_root, conda_root,
                             trimmed_annotation_npz, annotation_jsonl, stage2_output_dir)
    if previous_stage_2_cache_folder is not None:
        os.rename(previous_stage_2_cache_folder, previous_stage_2_cache_folder + ".{}.bk".format(time.time()))
        os.symlink(stage2_output_dir, previous_stage_2_cache_folder)
