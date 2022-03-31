import warcio, sys, json, os,requests, logging, io,traceback, multiprocessing
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

def html_page_extractor(warc_path,cared_doc_ens,response,output_queue):
    with io.BytesIO(response.content) as warc_fh:
        for care_record in cared_doc_ens:
            care_offset = care_record["offset"]
            try:
                warc_fh.seek(int(care_offset))
                it = iter(warcio.ArchiveIterator(warc_fh))
                record = next(it)
                original_html = record.content_stream().read().decode(care_record['encoding'])
                care_record["BBN_docid"] = encode_doc_id(os.path.basename(warc_path), care_offset)
                care_record["original_html"] = original_html
            except Exception as e:
                logger.exception(traceback.format_exc())
            finally:
                if care_record.get("original_html",None) is not None:
                    output_queue.put(care_record)


def encode_doc_id(warc_file_name,offset):
    return "{}_{}".format(warc_file_name,offset)

def mapper_process(job_queue,output_queue):
    try:
        while True:
            job_en = job_queue.get()
            if job_en is None:
                break
            warc_path,cared_doc_ens = job_en
            logger.info("Working on {}".format(warc_path))
            try:
                response = requests.get("https://commoncrawl.s3.amazonaws.com/{}".format(warc_path), stream=True, timeout=3)
                if response.status_code >= 400:
                    logger.exception("Error handling {} with status code {}".format(os.path.basename(warc_path),response.status_code))
                else:
                    html_page_extractor(warc_path, cared_doc_ens, response, output_queue)
            except Exception as e:
                logger.exception("Error handling {}".format(os.path.basename(warc_path)))
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
                wfp.write("{}\n".format(json.dumps(elem,ensure_ascii=False)))


def main(crawler_metadata_path,output_path):
    proessed_docid = set()
    if os.path.exists(output_path):
        with open(output_path) as fp:
            for i in fp:
                i = i.strip()
                line = json.loads(i)
                if line.get("original_html",None) is not None and line.get("BBN_docid",None) is not None:
                    proessed_docid.add(line['BBN_docid'])
    logger.info("Discovered {} processed htmls".format(len(proessed_docid)))
    manager = multiprocessing.Manager()
    job_queue = manager.Queue()
    output_queue = manager.Queue()
    n_workers = multiprocessing.cpu_count() * 2
    with open(crawler_metadata_path) as fp, manager.Pool(n_workers+1) as pool:
        crawler_metadata = json.load(fp)
        logger.info("In total {} warc files to process.".format(len(crawler_metadata)))
        # Step 1 put in jobs
        for idx,(warc_path,metadata_records) in enumerate(crawler_metadata.items()):
            cared_doc_en = list()
            for metadata_record in metadata_records:
                offset = int(metadata_record["offset"])
                doc_id = encode_doc_id(os.path.basename(warc_path),offset)
                if doc_id not in proessed_docid:
                    cared_doc_en.append(metadata_record)
            if len(cared_doc_en) > 0:
                job_queue.put((warc_path,cared_doc_en))
        workers = list()
        # Step 2 put in end job markings
        for _ in range(n_workers):
            job_queue.put(None)
        # Step 3 spawn mappers
        for _ in range(n_workers):
            proc = pool.apply_async(mapper_process, args=(job_queue,output_queue,))
            workers.append(proc)
        # Step 4 spawn writer
        proc = pool.apply_async(reducer_process,args=(output_queue,n_workers,output_path,))
        workers.append(proc)
        for worker in workers:
            worker.wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    crawler_metadata_path = "/home/ubuntu/wait_for_crawling_7.json"
    output_path = "/home/ubuntu/commoncrawl_dump_7"
    main(crawler_metadata_path, output_path)