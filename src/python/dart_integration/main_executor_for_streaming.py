import copy
import json
import logging
import multiprocessing
import os
import shutil
import time
from threading import Timer, RLock

import requests
from faust import Record

from cdr_cache import CDRCache
from main_executor import main_executor
from upstream import upstream_main

logger = logging.getLogger(__name__)


class StreamingProcessor(object):
    def __init__(self, max_cdrs_to_trigger, max_waiting_time_to_trigger, buffer_space, config_path):
        self.running_process = None
        self.queue_message_pool = dict()
        self.max_cdrs_to_trigger = max_cdrs_to_trigger
        self.max_waiting_time_to_trigger = max_waiting_time_to_trigger
        self.buffer_space = buffer_space
        os.makedirs(self.buffer_space, exist_ok=True)
        self.config_path = config_path
        with open(config_path) as fp:
            self.config = json.load(fp)
        self.last_process_time = int(time.time())
        self.timer = None
        self.lock = RLock()
        self.skip_processed = self.config.get("hume.streaming.skip_processed", False)
        self.processed_message_ids = set()
        self.use_packed_ontology = self.config.get("hume.streaming.use_packed_ontology", False)
        if self.skip_processed is True:
            if os.path.isfile(os.path.join(self.config["hume.tmp_dir"], "processed.log")):
                with open(os.path.join(self.config["hume.tmp_dir"], "processed.log")) as fp:
                    for i in fp:
                        i = i.strip()
                        doc_uuid, ontology_id = i.split("\t")
                        self.processed_message_ids.add((doc_uuid, ontology_id))

    def get_ontology_path(self, ontology_id):
        return os.path.join(self.buffer_space, "ontology_{}.yml".format(ontology_id))

    def run_pipeline(self, single_ontology_run_message_pool):
        timestamp = str(int(time.time()))
        runtime_tmp = os.path.join(self.buffer_space, timestamp)
        cdr_endpoint = self.config['CDR_retrieval']
        os.makedirs(runtime_tmp, exist_ok=True)
        cdr_dir = os.path.join(runtime_tmp, "cdrs")
        pipeline_dir = os.path.join(runtime_tmp, "runtimes")
        os.makedirs(cdr_dir, exist_ok=True)
        os.makedirs(pipeline_dir, exist_ok=True)
        processed_doc_uuid_ontology_id = set()

        cdr_cache_dir = self.config.get("hume.cdr_cache_dir", None)
        if cdr_cache_dir is None:
            cdr_cache_dir = cdr_dir
        cdr_cache = CDRCache(cdr_cache_dir, url=self.config["CDR_retrieval"],
                             username=self.config.get("auth", dict()).get("username", None),
                             password=self.config.get("auth", dict()).get("password", dict()))
        # Download cdr
        doc_uuid_list = list()
        ontology_id = None
        for doc_uuid, msg in single_ontology_run_message_pool.items():
            if self.use_packed_ontology is False:
                ontology_id_local = msg["ontologies"][0]["ontology"]
                if ontology_id is None:
                    ontology_id = ontology_id_local
                else:
                    assert ontology_id == ontology_id_local
            doc_uuid_list.append(doc_uuid)
        cdr_list_path = os.path.join(pipeline_dir, "cdrs.list")
        cdr_cache.get_cdr_list_from_uuid_list(doc_uuid_list, cdr_list_path)
        if self.config.get("hume.cdr_cache_dir", None) is not None:
            with open(cdr_list_path) as fp:
                for i in fp:
                    i = i.strip()
                    os.symlink(i, os.path.join(cdr_dir, os.path.basename(i)))

        # hqiu comment out
        # run pipeline
        logger.info("Running pipeline over {} docs using {} ontology".format(len(doc_uuid_list), ontology_id))
        if self.use_packed_ontology is False:
            self.running_process = multiprocessing.Process(target=main_executor,
                                                           args=(self.config_path, cdr_dir, pipeline_dir, ontology_id,
                                                                 self.get_ontology_path(ontology_id)))
        else:
            self.running_process = multiprocessing.Process(target=main_executor,
                                                           args=(self.config_path, cdr_dir, pipeline_dir, None, None))
        self.running_process.start()
        self.running_process.join()
        # upload
        uploaded_doc_uuids = set()
        if self.running_process.exitcode == 0 and self.running_process.is_alive() == False:
            uploaded_doc_uuids = upstream_main(self.config_path, pipeline_dir, True)
        else:
            uploaded_doc_uuids = upstream_main(self.config_path, pipeline_dir, True)
        # hqiu comment out end
        # doc_uuid_to_message_id = {v:k for k,v in message_id_to_doc_uuid.items()}
        for processed_doc_uuid in uploaded_doc_uuids:
            processed_doc_uuid_ontology_id.add((processed_doc_uuid, ontology_id))
        if self.skip_processed is True:
            with open(os.path.join(self.config["hume.tmp_dir"], "processed.log"), 'a') as afp:
                for doc_uuid, ontology_id_l in processed_doc_uuid_ontology_id:
                    afp.write("{}\t{}\n".format(doc_uuid, ontology_id_l))
                afp.flush()
        # cleaning
        if self.config.get("hume.streaming.keep_pipeline_data", False) is False:
            shutil.rmtree(runtime_tmp, ignore_errors=True)

    def main_executer(self):
        with self.lock:
            try:
                run_message_pool = copy.deepcopy(self.queue_message_pool)
                for ontology_id, doc_id_to_msg in run_message_pool.items():
                    logger.info("Processing {} {} start".format(ontology_id, doc_id_to_msg.keys()))
                    self.download_new_ontology(ontology_id)
                    self.run_pipeline(doc_id_to_msg)
                    logger.info("Processing {} {} end".format(ontology_id, doc_id_to_msg.keys()))
            except Exception as e:
                import traceback
                logger.exception(traceback.format_exc())
            finally:
                self.last_process_time = int(time.time())
                self.queue_message_pool.clear()
                self.timer = None

    @property
    def requests_in_queue_message_pool_size(self):
        ret = 0
        for ontology_id, doc_id_to_msg in self.queue_message_pool.items():
            ret += len(doc_id_to_msg.keys())
        return ret

    def pipeline_trigger(self, should_trigger_now):
        if self.requests_in_queue_message_pool_size > 0:
            if self.requests_in_queue_message_pool_size >= self.max_cdrs_to_trigger or should_trigger_now:
                if self.timer is not None:
                    self.timer.cancel()
                self.timer = Timer(0, self.main_executer)
                self.timer.start()
            else:
                if self.timer is None:
                    self.timer = Timer(self.max_waiting_time_to_trigger, self.main_executer)
                    self.timer.start()

    def download_new_ontology(self, ontology_id):
        if os.path.exists(self.get_ontology_path(ontology_id)) is False:
            ontology_retrival_endpoint = self.config['Ontology_retrieval']
            auth_obj = None
            if "auth" in self.config:
                auth_obj = (self.config['auth']['username'], self.config['auth']['password'])
            r = requests.get(ontology_retrival_endpoint, auth=auth_obj, params={"id": ontology_id})
            ontology_str = r.json()["ontology"]
            with open(self.get_ontology_path(ontology_id), 'w') as wfp:
                wfp.write(ontology_str)

    def kafka_message_handler(self, persist_dir, doc_uuid, value):
        value = value.dumps().decode() if isinstance(value, Record) else json.dumps(value)
        value = json.loads(value)
        with self.lock:
            if self.use_packed_ontology:
                value["ontologies"] = [None]
            for ontology_entry in value["ontologies"]:
                current_ontology_version = ontology_entry["ontology"]
                if (doc_uuid, current_ontology_version) not in self.processed_message_ids:
                    self.queue_message_pool.setdefault(current_ontology_version, dict())[doc_uuid] = value
                else:
                    logger.info("Skipping {} due to it's in processed log".format(doc_uuid))
                self.pipeline_trigger(False)
