import os,sys,json,shutil,shlex,logging,time,multiprocessing
import requests
from faust import Record

from main_executor import main_executor

logger = logging.getLogger(__name__)
from upstream import upstream_main

class StreamingProcessor(object):
    def __init__(self,max_cdrs_to_trigger,max_waiting_time_to_trigger,buffer_space,config_path):
        self.running_process = None
        self.message_pool = dict()
        self.max_cdrs_to_trigger = max_cdrs_to_trigger
        self.max_waiting_time_to_trigger = max_waiting_time_to_trigger
        self.buffer_space = buffer_space
        shutil.rmtree(self.buffer_space,ignore_errors=True)
        os.makedirs(self.buffer_space,exist_ok=True)
        self.config_path = config_path
        with open(config_path) as fp:
            self.config = json.load(fp)
        self.last_process_time = int(time.time())

    def run_pipeline(self):
        timestamp = str(int(time.time()))
        runtime_tmp = os.path.join(self.buffer_space,timestamp)
        cdr_endpoint = self.config['CDR_retrieval']
        os.makedirs(runtime_tmp,exist_ok=True)
        # Download cdr
        cdr_list = list()
        for msg_id,msg_body in self.message_pool.items():
            msg_body = json.loads(msg_body["cdr-data"])
            uuid = msg_body['document_id']
            if "extracted_text" not in msg_body:
                continue

            uri = "{}/{}".format(cdr_endpoint, uuid)
            try:
                r = requests.get(uri)
                cdr = r.json()
                with open(os.path.join(runtime_tmp, "{}.json".format(msg_id)), 'w') as fp2:
                    json.dump(cdr, fp2, indent=4, sort_keys=True, ensure_ascii=False)
                cdr_list.append(os.path.join(runtime_tmp, "{}.json".format(msg_id)))
                logging.root.info("Saving cdr for message {}".format(msg_id))
            except:
                import traceback
                traceback.print_exc()
        # Generate cdr list
        cdr_list_path = os.path.join(runtime_tmp,'file.list')
        with open(cdr_list_path,'w') as fp:
            for i in cdr_list:
                fp.write("{}\n".format(i))
        # run pipeline
        self.running_process = multiprocessing.Process(target=main_executor,
                                                       args=(self.config_path, cdr_list_path,))
        self.running_process.start()
        self.running_process.join()
        # upload
        if self.running_process.exitcode == 0 and self.running_process.is_alive() == False:
            upstream_main(self.config_path, True)
        else:
            upstream_main(self.config_path, True)
        # cleaning
        shutil.rmtree(runtime_tmp,ignore_errors=True)


    def kafka_message_handler(self,persist_dir, key, value):
        value = value.dumps().decode() if isinstance(value, Record) else json.dumps(value)
        value = json.loads(value)
        self.message_pool[key] = value
        if len(self.message_pool) > 0 and (len(self.message_pool) >= self.max_cdrs_to_trigger or int(time.time()) - self.last_process_time >= self.max_waiting_time_to_trigger):
            try:
                self.run_pipeline()
            except Exception as e:
                import traceback
                traceback.print_exc()
            finally:
                self.last_process_time = int(time.time())
                self.message_pool.clear()

