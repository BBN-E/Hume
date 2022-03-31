import json
import logging
import traceback
import multiprocessing
import multiprocessing.managers

logger = logging.getLogger(__name__)


# https://stackoverflow.com/a/50878600/6254393
# Backup original AutoProxy function
backup_autoproxy = multiprocessing.managers.AutoProxy

# Defining a new AutoProxy that handles unwanted key argument 'manager_owned'
def redefined_autoproxy(token, serializer, manager=None, authkey=None,
          exposed=None, incref=True, manager_owned=True):
    # Calling original AutoProxy without the unwanted key argument
    return backup_autoproxy(token, serializer, manager, authkey,
                     exposed, incref)

# Updating AutoProxy definition in multiprocessing.managers package
multiprocessing.managers.AutoProxy = redefined_autoproxy

def reducer_process(output_queue,n_workers,output_path):
    stop_signals_received = 0
    doc_uuid_to_cdr_paths = dict()
    while True:
        elem = output_queue.get()
        if elem is None:
            stop_signals_received += 1
            if stop_signals_received >= n_workers:
                break
        else:
            cdr_path,cdr_uuid = elem
            doc_uuid_to_cdr_paths.setdefault(cdr_uuid,set()).add(cdr_path)
    logger.info("Writing {}".format(len(doc_uuid_to_cdr_paths)))
    with open(output_path,'w') as wfp:
        for doc_uuid,cdr_paths in doc_uuid_to_cdr_paths.items():
            wfp.write("{}\n".format(list(cdr_paths)[0]))


def mapper_process(job_queue,output_queue):
    try:
        while True:
            job_en = job_queue.get()
            if job_en is None:
                break
            with open(job_en) as fp:
                cdr = json.load(fp)
                doc_uuid = cdr['document_id']
                output_queue.put((job_en,doc_uuid))

    except Exception as e:
        logger.exception(traceback.format_exc())
    finally:
        output_queue.put(None)

def main(input_cdr_list_path,output_cdr_list_path):
    manager = multiprocessing.Manager()
    job_queue = manager.Queue()
    output_queue = manager.Queue()
    n_workers = multiprocessing.cpu_count()
    with open(input_cdr_list_path) as fp, manager.Pool(n_workers+1) as pool:
        # Step 1 put in jobs
        for idx,line in enumerate(fp):
            line = line.strip()
            job_queue.put(line)
        workers = list()
        # Step 2 put in end job markings
        for _ in range(n_workers):
            job_queue.put(None)
        # Step 3 spawn mappers
        for _ in range(n_workers):
            proc = pool.apply_async(mapper_process, args=(job_queue,output_queue,))
            workers.append(proc)
        # Step 4 spawn writer
        proc = pool.apply_async(reducer_process,args=(output_queue,n_workers,output_cdr_list_path,))
        workers.append(proc)
        for worker in workers:
            worker.wait()


if __name__ == "__main__":
    input_cdr_list_path = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/wm/OIAD_processing.list"
    output_cdr_list_path = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/wm/OIAD_processing_deduplicated.list"
    main(input_cdr_list_path, output_cdr_list_path)