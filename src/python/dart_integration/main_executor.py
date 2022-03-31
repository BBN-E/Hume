import json
import logging
import os
import shlex
import subprocess

from domain_factory import domain

logger = logging.getLogger(__name__)


def modify_config_file(arg_file_path, num_of_batches, num_of_jobs_for_nn, out_par_file_path,
                       should_output_unification_json, external_ontology_path, external_ontology_version,
                       use_regrounding_cache, regrounding_cache_path, cdr_list_path):
    output_buf = list()
    with open(arg_file_path) as fp:
        for i in fp:
            i = i.replace("[PENDING_NUM_OF_BATCHES]", str(num_of_batches))
            i = i.replace("[PENDING_NUM_OF_SCHEDULING_JOBS_FOR_NN]", str(num_of_jobs_for_nn))
            i = i.replace("[PENDING_EXTERNAL_ONTOLOGY_PATH]", str(external_ontology_path))
            i = i.replace("[PENDING_EXTERNAL_ONTOLOGY_VERSION]", str(external_ontology_version))
            i = i.replace("[SHOULD_OUTPUT_UNIFICATION_JSON]", str(should_output_unification_json))
            i = i.replace("[PENDING_USE_REGROUNDING_CACHE]", "true" if use_regrounding_cache is True else "false")
            i = i.replace("[PENDING_REGROUNDING_CACHE_PATH]", str(regrounding_cache_path))
            i = i.replace("[PENDING_CDR_LIST_PATH]", str(cdr_list_path))
            output_buf.append(i)
    with open(out_par_file_path, 'w') as wfp:
        for i in output_buf:
            wfp.write(i)


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


def main_executor(config_path, cdr_dir_path, runtime_dir_path, ontology_version, ontology_path):
    if ontology_version is None:
        ontology_version = "DEFAULT"
    if ontology_path is None:
        ontology_path = "DEFAULT"
    with open(config_path) as fp:
        config = json.load(fp)

    hume_root_in_docker = "/wm_rootfs/git/Hume"
    modify_run_pl(os.path.join(hume_root_in_docker,"sequences","run.pl"), hume_root_in_docker, os.path.join(hume_root_in_docker,"sequences","run_modified.pl"))
    os.makedirs(runtime_dir_path, exist_ok=True)
    cdr_list_path = os.path.join(runtime_dir_path, "cdrs.list")
    cdr_list = list()
    with open(cdr_list_path, 'w') as wfp:
        for cdr_path in os.listdir(cdr_dir_path):
            if cdr_path.endswith(".json"):
                full_path = os.path.join(cdr_dir_path, cdr_path)
                cdr_list.append([full_path, os.stat(full_path).st_size])
                wfp.write("{}\n".format(full_path))
    if len(cdr_list) < 1:
        return
    total_file_size = sum((x[1] for x in cdr_list))
    total_file_size_in_mb = total_file_size / 1024 / 1024
    num_of_batches_in_size = int(total_file_size_in_mb * 0.5)
    num_of_jobs_for_nn = config.get('hume.num_of_vcpus', 8)
    adjusted_num_of_batches = num_of_jobs_for_nn
    adjusted_num_of_batches = max(num_of_batches_in_size, adjusted_num_of_batches)
    domain_config_name = domain[config['hume.domain']]['config_template_name']
    if config.get("hume.laptop_mode", False) is True:
        laptop_config_name = domain[config['hume.domain']].get("laptop_config_template_name", "")
        laptop_config_path = os.path.join(hume_root_in_docker, 'lib/runs', laptop_config_name)
        if os.path.exists(laptop_config_path) and os.path.isfile(laptop_config_path):
            domain_config_name = laptop_config_name
    filled_config_path = os.path.join(runtime_dir_path, "{}.par".format(domain_config_name))
    modify_config_file(os.path.join(hume_root_in_docker, 'lib/runs', domain_config_name), adjusted_num_of_batches,
                       num_of_jobs_for_nn,
                       filled_config_path,
                       domain[config['hume.domain']].get("should_output_unification_json", False),
                       ontology_path,
                       ontology_version,
                       config.get("hume.use_regrounding_cache", False),
                       config.get("hume.regrounding_cache_path", "DUMMY"),
                       cdr_list_path
                       )
    if os.path.exists(os.path.join(runtime_dir_path, "sequences", "sequencesrun_modified.pl")) is False:
        RUNJOB_ENVIRON = os.environ.copy()
        RUNJOB_ENVIRON['PWD'] = os.path.join(hume_root_in_docker)
        subprocess.run(shlex.split(
            "/usr/bin/perl sequences/run_modified.pl {} -copy {} {}".format("dummy", runtime_dir_path, filled_config_path)),
            cwd=hume_root_in_docker, env=RUNJOB_ENVIRON)
    # Clear pckpts
    pckpts_paths = set()
    for root, dirs, files in os.walk(runtime_dir_path):
        for file in files:
            if file.endswith(".pckpt") or file.endswith(".Xckpt"):
                pckpts_paths.add(os.path.join(root, file))
    for pckpts_path in pckpts_paths:
        os.unlink(pckpts_path)

    # run perl
    RUNJOB_ENVIRON = os.environ.copy()
    RUNJOB_ENVIRON['PWD'] = runtime_dir_path
    return subprocess.run(shlex.split(
        "/usr/bin/perl sequences/sequencesrun_modified.pl {} -local".format(filled_config_path)),
        cwd=runtime_dir_path, env=RUNJOB_ENVIRON)
