import json, os,requests, logging, io,traceback, multiprocessing
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


def mapper_process(job_queue,url,username,password,hume_version,labels,output_queue):
    auth_obj = None
    if username is not None and password is not None:
        auth_obj = (username,password)
    try:
        with requests.Session() as s:
            s.auth = auth_obj
            while True:
                job_en = job_queue.get()
                if job_en is None:
                    break
                with open(job_en) as fp:
                    j = json.load(fp)
                    assert len(j['documents']) == 1
                    doc_uuid = j['documents'][0]['@id']
                    commit_hash = j['ontologyMeta']['commit']
                with open(job_en,'rb') as fp,io.BytesIO() as metadata_io:
                    try:
                        metadata = {"identity": "hume", "version": hume_version, "document_id": doc_uuid,"output_version":commit_hash,"labels":labels}
    
                        metadata_io.write(json.dumps(metadata, ensure_ascii=False).encode("utf-8"))
                        metadata_io.seek(0)
                        fp.seek(0)
                        r = s.post(url, files={
                            "metadata": (None, json.dumps(metadata, ensure_ascii=False)),
                            "file": fp
                        },timeout=180)
                        if r.status_code < 300:
                            logger.info(r.json())
                            output_queue.put(job_en)
                        else:
                            logger.exception(job_en)
                            logger.exception(r.content)
                    except Exception as e:
                        logger.exception(job_en)
                        logger.exception(traceback.format_exc())
    except Exception as e:
        logger.exception(traceback.format_exc())
    finally:
        output_queue.put(None)

def reducer_process(output_queue,n_workers,output_path):
    stop_signals_received = 0
    with open(output_path,'a',encoding="utf-8") as wfp:
        while True:
            elem = output_queue.get()
            if elem is None:
                stop_signals_received += 1
                if stop_signals_received >= n_workers:
                    break
            else:
                wfp.write("{}\n".format(elem))


def main(file_list_path,url,username,password,hume_version,labels,output_path):
    proessed_docpath = set()
    if os.path.exists(output_path):
        with open(output_path) as fp:
            for i in fp:
                i = i.strip()
                proessed_docpath.add(i)
    logger.info("Discovered {} processed json-lds".format(len(proessed_docpath)))
    manager = multiprocessing.Manager()
    job_queue = manager.Queue()
    output_queue = manager.Queue()
    # n_workers = multiprocessing.cpu_count()
    n_workers = 4
    with manager.Pool(n_workers+1) as pool:

        # Step 1 put in jobs
        # for root,dirs,files in os.walk(serialization_path):
        #     for file in files:
        #         if file.endswith(".json-ld"):
        #             full_path = os.path.join(root,file)
        #             if full_path not in proessed_docpath:
        #                 job_queue.put(full_path)
        with open(file_list_path) as fp:
            for i in fp:
                i = i.strip()
                if i not in proessed_docpath:
                    job_queue.put(i)
        workers = list()
        # Step 2 put in end job markings
        for _ in range(n_workers):
            job_queue.put(None)
        # Step 3 spawn mappers
        for _ in range(n_workers):
            proc = pool.apply_async(mapper_process, args=(job_queue,url,username,password,hume_version,labels,output_queue,))
            workers.append(proc)
        # Step 4 spawn writer
        proc = pool.apply_async(reducer_process,args=(output_queue,n_workers,output_path,))
        workers.append(proc)
        for worker in workers:
            worker.wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    url = "Redacted/dart/api/v1/readers/upload"
    username = "Redacted"
    password = "Redacted"
    hume_version = "R2022_02_18"
    output_path = "/home/hqiu/tmp/dart_booking.txt"
    serialization_path = "/d4m/ears/expts/48393.030422.dsmte.v1/expts/dsmte.030322.v1/json-ld.list"
    labels = ["by_hand"]
    main(serialization_path, url, username, password, hume_version, labels,output_path)
