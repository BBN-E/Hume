import os,sys,json,subprocess,shutil,shlex,logging

from domain_factory import domain
logger = logging.getLogger(__name__)

def modify_config_file(arg_file_path,num_of_batches,num_of_jobs_for_nn,out_par_file_path,should_output_unification_json):
    output_buf = list()
    with open(arg_file_path) as fp:
        for i in fp:
            i = i.replace("[PENDING_NUM_OF_BATCHES]",str(num_of_batches))
            i = i.replace("[PENDING_NUM_OF_SCHEDULING_JOBS_FOR_NN]",str(num_of_jobs_for_nn))
            i = i.replace("[PENDING_NUM_OF_SCHEDULING_JOBS_FOR_NN]",str(num_of_jobs_for_nn))
            i = i.replace("[SHOULD_OUTPUT_UNIFICATION_JSON]",str(should_output_unification_json))
            output_buf.append(i)
    with open(out_par_file_path,'w') as wfp:
        for i in output_buf:
            wfp.write(i)

def main_executor(config_path,file_list_path):
    with open(config_path) as fp:
        config = json.load(fp)

    hume_root_in_docker = "/wm_rootfs/git/Hume"
    # Clean ckpt etc
    shutil.rmtree(os.path.join(hume_root_in_docker,'ckpts'),ignore_errors=True)
    shutil.rmtree(os.path.join(hume_root_in_docker,'etemplates'),ignore_errors=True)
    shutil.rmtree(os.path.join(hume_root_in_docker,'expts'),ignore_errors=True)
    shutil.rmtree(os.path.join(hume_root_in_docker,'logfiles'),ignore_errors=True)
    # Modify par file
    cdr_list = list()
    with open(file_list_path) as fp:
        for i in fp:
            p = i.strip()
            cdr_list.append([p,os.stat(p).st_size])
    if len(cdr_list) < 1:
        return
    total_file_size = sum((x[1] for x in cdr_list))
    total_file_size_in_mb = total_file_size / 1024 / 1024
    num_of_batches_in_size = int(total_file_size_in_mb * 0.5)
    num_of_jobs_for_nn = config.get('hume.num_of_vcpus',8)
    adjusted_num_of_batches = num_of_jobs_for_nn
    adjusted_num_of_batches = max(num_of_batches_in_size,adjusted_num_of_batches)
    domain_config_name = domain[config['hume.domain']]['config_template_name']
    if config.get("hume.laptop_mode",False) is True:
        laptop_config_name = domain[config['hume.domain']].get("laptop_config_template_name","")
        laptop_config_path = os.path.join(hume_root_in_docker,'lib/runs',laptop_config_name)
        if os.path.exists(laptop_config_path) and os.path.isfile(laptop_config_path):
            domain_config_name = laptop_config_name
    modify_config_file(os.path.join(hume_root_in_docker,'lib/runs',domain_config_name),adjusted_num_of_batches,num_of_jobs_for_nn,os.path.join(hume_root_in_docker,'lib/runs',"{}.par".format(domain_config_name)),domain[config['hume.domain']].get("should_output_unification_json",False))
    os.makedirs("/extra/tmp",exist_ok=True)
    with open("/extra/tmp/ben_sentence.list",'w') as wfp:
        for i in cdr_list:
            wfp.write("{}\n".format(i[0]))
    # run perl
    RUNJOB_ENVIRON = os.environ.copy()
    RUNJOB_ENVIRON['PWD'] = os.path.join(hume_root_in_docker)
    return subprocess.run(shlex.split(
        "/usr/bin/perl sequences/run.pl lib/runs/{} -local".format("{}.par".format(domain_config_name))),
                   cwd=hume_root_in_docker, env=RUNJOB_ENVIRON)
