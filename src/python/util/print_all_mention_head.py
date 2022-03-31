import logging
import serifxml3
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


def single_document_handler(serif_path):
    serif_doc = serifxml3.Document(serif_path)
    unique_mention_head = set()
    for sentence in serif_doc.sentences:
        for mention in sentence.mention_set or ():
            unique_mention_head.add(mention.head)
    return list("{}".format(i.text) for i in unique_mention_head)


def mapper_process(job_queue, output_queue):
    try:
        while True:
            job_en = job_queue.get()
            if job_en is None:
                break
            logger.info("Processing {}".format(job_en))
            for s in single_document_handler(job_en):
                output_queue.put(s)
    except Exception as e:
        logger.exception(traceback.format_exc())
    finally:
        output_queue.put(None)


def reducer(output_queue, n_workers, output_path):
    stop_signals_received = 0
    with open(output_path, 'w', encoding="utf-8") as wfp:
        while True:
            elem = output_queue.get()
            if elem is None:
                stop_signals_received += 1
                if stop_signals_received >= n_workers:
                    break
            else:
                wfp.write("{}\n".format(elem))


def main():
    serif_list = "/d4m/ears/expts/48393.030422.dsmte.v1/expts/dsmte.030322.v1/pyserif_after_pg/pyserif_main/serifxml.list"
    output_path = "/home/hqiu/tmp/all_mentions.dump"
    manager = multiprocessing.Manager()
    job_queue = manager.Queue()
    output_queue = manager.Queue()
    n_workers = multiprocessing.cpu_count() * 2
    with open(serif_list) as fp, manager.Pool(n_workers+1) as pool:
        for i in fp:
            i = i.strip()
            job_queue.put(i)
        workers = list()
        # Step 2 put in end job markings
        for _ in range(n_workers):
            job_queue.put(None)
        # Step 3 spawn mappers
        for _ in range(n_workers):
            proc = pool.apply_async(mapper_process, args=(job_queue, output_queue,))
            workers.append(proc)
        # Step 4 spawn writer
        proc = pool.apply_async(reducer, args=(output_queue, n_workers, output_path,))
        workers.append(proc)
        for worker in workers:
            worker.wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
