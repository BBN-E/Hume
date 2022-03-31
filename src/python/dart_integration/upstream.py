import io
import json
import logging
import os
import shutil
import time
import traceback

import requests

logger = logging.getLogger(__name__)
from domain_factory import domain


def upload_file_to_dart(serialization_dir, config_ins, hume_version, file_suffix):
    upload_uri = config_ins['DART_upload']
    processed_document_uuid = set()
    for root, dirs, files in os.walk(serialization_dir):
        for file in files:
            if file.endswith(file_suffix):
                doc_uuid = file[:-len(file_suffix)]
                logger.info("Handling {}".format(doc_uuid))
                output_version = ""
                if config_ins['hume.domain'] == "WM":
                    with open(os.path.join(root, file)) as fp:
                        j = json.load(fp)
                        commit_hash = j['ontologyMeta']['commit']
                        output_version = commit_hash
                with open(os.path.join(root, file), 'rb') as fp:
                    metadata = {"identity": "hume", "version": hume_version, "document_id": doc_uuid,
                                "output_version": output_version,
                                "labels": config_ins.get("DART_upload_labels", list())}
                    metadata_io = io.BytesIO(json.dumps(metadata, ensure_ascii=False).encode("utf-8"))
                    metadata_io.seek(0)
                    auth_obj = None
                    if "auth" in config_ins:
                        auth_obj = (config_ins['auth']['username'], config_ins['auth']['password'])
                    try:
                        r = requests.post("{}/upload".format(upload_uri), files={
                            "metadata": (None, json.dumps(metadata, ensure_ascii=False)),
                            "file": fp
                        }, auth=auth_obj)
                        logger.info(r.text)
                        processed_document_uuid.add(doc_uuid)
                    except Exception:
                        logger.exception(traceback.format_exc())
    return processed_document_uuid


def upstream_main(config_path, runtime_root, should_upload):
    with open(config_path) as fp:
        config = json.load(fp)
    result_root = os.path.join(config['hume.tmp_dir'], 'results')
    current_result_root = os.path.join(result_root, str(int(time.time())))
    # copy result files
    file_suffix = domain[config['hume.domain']]['suffix']
    domain_expt_name = domain[config['hume.domain']]['job_name']
    serialization_folder = os.path.join(runtime_root, 'expts/{}/serialization'.format(domain_expt_name))
    handled_files = 0

    processed_docuuid = set()
    if os.path.exists(serialization_folder):
        current_result_file_root = os.path.join(current_result_root, 'results')
        os.makedirs(current_result_file_root, exist_ok=True)
        # get current hume version
        hume_version = sorted(os.listdir("/d4m/nlp/releases/Hume/"))[-1]
        for root, dirs, files in os.walk(serialization_folder):
            for file in files:
                if file.endswith(file_suffix):
                    doc_uuid = os.path.basename(root)
                    shutil.copy2(os.path.join(root, file),
                                 os.path.join(current_result_file_root, "{}{}".format(doc_uuid, file_suffix)))
                    handled_files += 1
        if handled_files > 0 and should_upload:
            doc_uuid_set = upload_file_to_dart(current_result_file_root, config, hume_version, file_suffix)
            processed_docuuid.update(doc_uuid_set)
        else:
            if should_upload:
                logger.warning("There's zero result on run {}".format(runtime_root))
            else:
                logger.warning("You can find your results at {}. This is a path accessible from inside docker. ".format(current_result_file_root))
    else:
        logger.warning("There's zero result on run {}".format(runtime_root))

    return processed_docuuid
