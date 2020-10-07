import os,sys,io,glob
import shlex
import psutil
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
        out,err = sub_process.communicate()
        if sub_process.returncode is not None and sub_process.returncode != 0:
            raise RuntimeError
    finally:
        with concurrent_dict_lock:
            concurrent_dict[assigned_core_num] = 1 # release the assigned core
        sema.release()
        print("[Scheduler] {} on coreid {} pid {} completed".format(batch_id,assigned_core_num,sub_process.pid))


def manager():
    # CORE_NUM = min(psutil.cpu_count(logical=False), 64) - 1  # max number of cores is 64
    CORE_NUM = 8
    number_of_batches=100
    LOGICAL_TO_PHYSICAL_MULTIPLER = 1

    all_jobs = list()



    all_jobs_in_batch = list_spliter_by_num_of_batches(all_jobs,number_of_batches)
    batch_files_list = all_jobs_in_batch

    with Manager() as manager:
        concurrent_dict = manager.dict()
        sema = manager.Semaphore(CORE_NUM)

        concurrent_dict_lock = manager.Lock()

        all_processes = list()
        # fill the concurrent_dict with all possible cores
        for core_num in range(CORE_NUM):
            concurrent_dict[int(LOGICAL_TO_PHYSICAL_MULTIPLER * (core_num + 1))] = 1
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

            command = "cat /nonexists"
            p = Process(target=worker, args=(command,sema, concurrent_dict,concurrent_dict_lock,assigned_core_num,idx))
            all_processes.append(p)
            p.start()
        for p in all_processes:
            p.join()

if __name__ == "__main__":
    manager()