import json
import logging
import os
import shutil
import traceback

import requests

logger = logging.getLogger(__name__)


class CDRCache(object):
    def __init__(self, cache_dir, *, prune_cache_dir_per_request=False, url=None, username=None, password=None):
        self.cache_dir = cache_dir
        self.prune_cache_dir_per_request = prune_cache_dir_per_request
        self.url = url
        self.username = username
        self.password = password
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_cdr_list_from_uuid_list(self, uuid_list, output_cdr_list_path):
        if self.prune_cache_dir_per_request:
            pending_remove_set = set()
            for file in os.listdir(self.cache_dir):
                doc_uuid = file[:-len(".json")]
                if doc_uuid not in uuid_list:
                    pending_remove_set.add(os.path.join(self.cache_dir, file))
            for i in pending_remove_set:
                shutil.rmtree(i, ignore_errors=True)
        uuid_to_file_path = dict()
        for file in os.listdir(self.cache_dir):
            doc_uuid = file[:-len(".json")]
            uuid_to_file_path[doc_uuid] = os.path.join(self.cache_dir, file)
        if self.url is not None:
            for idx, doc_uuid in enumerate(uuid_list):
                logger.info("({}/{}):Downloading {}".format(idx + 1, len(uuid_list), doc_uuid))
                if doc_uuid not in uuid_to_file_path:
                    uri = "{}/{}".format(self.url, doc_uuid)
                    try:
                        auth_obj = None
                        if self.username is not None and self.password is not None:
                            auth_obj = (self.username, self.password)
                        r = requests.get(uri, auth=auth_obj)
                        cdr = r.json()
                        with open(os.path.join(self.cache_dir, "{}.json".format(doc_uuid)), 'w') as fp2:
                            json.dump(cdr, fp2, indent=4, sort_keys=True, ensure_ascii=False)
                        uuid_to_file_path[doc_uuid] = os.path.join(self.cache_dir, "{}.json".format(doc_uuid))
                    except:
                        logger.exception(traceback.format_exc())
        with open(output_cdr_list_path, 'w') as wfp:
            for doc_uuid in uuid_list:
                if doc_uuid in uuid_to_file_path:
                    wfp.write("{}\n".format(uuid_to_file_path[doc_uuid]))
                else:
                    logger.critical("Cannot find filesystem entry for {}".format(doc_uuid))
