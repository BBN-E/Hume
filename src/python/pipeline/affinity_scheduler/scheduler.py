import os,sys,psutil,io,glob
import shlex
from multiprocessing import Semaphore, Process, Manager
from subprocess import PIPE
def list_spliter_by_num_of_batches(my_list, num_of_batches):
    k, m = divmod(len(my_list), num_of_batches)
    return list(my_list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(num_of_batches))

def worker(command_line,sema, concurrent_dict,concurrent_dict_lock,assigned_core_num,batch_id):
    try:
        sub_process = psutil.Popen(shlex.split("taskset -c {} {}".format(assigned_core_num,command_line)))
        print("[Scheduler]Scheduling {} on coreid {} pid {} with {}".format(batch_id, assigned_core_num,sub_process.pid,command_line))
        # os.system("taskset -p -c %d %d &> /dev/null" % (assigned_core_num, sub_process.pid))
        sub_process.wait()
    finally:
        with concurrent_dict_lock:
            concurrent_dict[assigned_core_num] = 1 # release the assigned core
        sema.release()
        print("[Scheduler] {} on coreid {} pid {} completed".format(batch_id,assigned_core_num,sub_process.pid))


def manager(input_list_path,number_of_jobs_from_user,batch_id,number_of_batches,command_prefix,batch_arg_name,scratch_space,pass_in_batch_id_field):
    # CORE_NUM = min(psutil.cpu_count(logical=False), 64) - 1  # max number of cores is 64
    # CORE_NUM = psutil.cpu_count(logical=False) - 1  # Use as many cores as possible
    # LOGICAL_TO_PHYSICAL_MULTIPLER = psutil.cpu_count(logical=True) / psutil.cpu_count(logical=False)

    NUM_USER_SAY = None
    try:
        NUM_USER_SAY = int(number_of_jobs_from_user)
    except ValueError as e:
        NUM_USER_SAY = None
    if NUM_USER_SAY is None:
        NUM_USER_SAY = psutil.cpu_count(logical=False)
    elif NUM_USER_SAY < 2:
        NUM_USER_SAY = psutil.cpu_count(logical=False)
    elif NUM_USER_SAY > psutil.cpu_count(logical=True):
        NUM_USER_SAY = psutil.cpu_count(logical=False)

    CONCURRENT_JOB_NUM = NUM_USER_SAY - 1  # Use as many cores as possible
    LOGICAL_TO_PHYSICAL_MULTIPLER = int(psutil.cpu_count(logical=True) / NUM_USER_SAY)


    all_jobs = list()
    with open(input_list_path) as fp:
        for i in fp:
            i = i.strip()
            all_jobs.append(i)


    all_jobs_in_batch = list_spliter_by_num_of_batches(all_jobs,number_of_batches)

    batch_file_dir = os.path.join(scratch_space,'batch_file')
    os.makedirs(batch_file_dir,exist_ok=True)
    batch_files_list = list()

    for idx,job_batch in enumerate(all_jobs_in_batch):
        batch_file = os.path.join(batch_file_dir,str(idx))
        with open(batch_file,'w') as wfp:
            for job in job_batch:
                wfp.write("{}\n".format(job))
        batch_files_list.append(batch_file)

    with Manager() as manager:
        concurrent_dict = manager.dict()
        sema = manager.Semaphore(CONCURRENT_JOB_NUM)

        concurrent_dict_lock = manager.Lock()

        all_processes = list()
        # fill the concurrent_dict with all possible cores
        for core_num in range(CONCURRENT_JOB_NUM):
            concurrent_dict[int(LOGICAL_TO_PHYSICAL_MULTIPLER * (core_num + 1)) % psutil.cpu_count(logical=True)] = 1
        for idx,file_list_path in enumerate(batch_files_list):
            # once `chunk_sizes` processes are running,
            # the following code will block main process
            sema.acquire()
            assigned_core_num = None
            with concurrent_dict_lock:
                for core_num in concurrent_dict:
                    assigned_core_num = core_num
                    break
                assert (assigned_core_num is not None)
                del concurrent_dict[assigned_core_num]  # occupy the assigned core

            command = command_prefix.replace(batch_arg_name,file_list_path)
            if pass_in_batch_id_field is not None:
                command = command.replace(pass_in_batch_id_field,"{}_{}".format(batch_id,idx))
            p = Process(target=worker, args=(command,sema, concurrent_dict,concurrent_dict_lock,assigned_core_num,idx))
            all_processes.append(p)
            p.start()
        for p in all_processes:
            p.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_list_path",type=str,required=True)
    parser.add_argument("--number_of_jobs_from_user",type=str)
    parser.add_argument("--batch_id",type=str,required=True)
    parser.add_argument("--number_of_batches",type=int,required=True)
    parser.add_argument("--command_prefix",type=str,required=True)
    parser.add_argument("--batch_arg_name",type=str,required=True)
    parser.add_argument("--scratch_space",type=str,required=True)
    parser.add_argument("--pass_in_batch_id_field",type=str,required=False)
    args, unknown = parser.parse_known_args()
    manager(args.input_list_path,args.number_of_jobs_from_user,args.batch_id, args.number_of_batches, args.command_prefix, args.batch_arg_name,args.scratch_space,args.pass_in_batch_id_field)