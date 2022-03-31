import os
import json
import logging
import requests
import traceback

logger = logging.getLogger(__name__)

def download_cdrs(config,doc_uuids,output_folder):
    cdr_endpoint = config['CDR_retrieval']
    cdr_list = list()
    os.makedirs(output_folder,exist_ok=True)
    for idx, doc_uuid in enumerate(doc_uuids):
        logger.info("({}/{}):Downloading {}".format(idx+1, len(doc_uuids), doc_uuid))
        uri = "{}/{}".format(cdr_endpoint, doc_uuid)
        try:
            auth_obj = None
            if "auth" in config:
                auth_obj = (config['auth']['username'], config['auth']['password'])
            r = requests.get(uri, auth=auth_obj)
            cdr = r.json()
            with open(os.path.join(output_folder, "{}.json".format(doc_uuid)), 'w') as fp2:
                json.dump(cdr, fp2, indent=4, sort_keys=True, ensure_ascii=False)
            cdr_list.append(os.path.join(output_folder, "{}.json".format(doc_uuid)))
            logger.info("Saving cdr for message {}".format(doc_uuid))
        except:
            logger.exception(traceback.format_exc())
    return cdr_list

def main():
    config = {
        'CDR_retrieval': "Redacted/dart/api/v1/cdrs",
        'auth': {
            'username': 'Redacted',
            'password': 'Redacted'
        }
    }
    request_json_path = "/home/hqiu/Downloads/stability-discovery-results.json"
    output_job_control_dir = "/nfs/raid88/u10/users/hqiu_ad/data/wm/apr_embed_2/preprocess/"
    with open(request_json_path) as fp:
        request_json = json.load(fp)
    with open(os.path.join(output_job_control_dir,"salient_words.tsv"),'w') as wfp:
        for word in request_json["allowed_words"]:
            wfp.write("{}\t{}\n".format(word.replace("\t", " ").replace("\n", " ").replace("\r", " "), 0))
    with open(os.path.join(output_job_control_dir,'ontology_metadata.yml'),'w') as wfp:
        wfp.write(request_json["ontology_metadata"])
    cdr_outout_dir = os.path.join(output_job_control_dir,'cdrs')
    os.makedirs(cdr_outout_dir,exist_ok=True)
    cdr_paths = download_cdrs(config, request_json["relevant_doc_uuids"], cdr_outout_dir)
    with open(os.path.join(output_job_control_dir,'cdrs.list'),'w') as wfp:
        for cdr_path in cdr_paths:
            wfp.write("{}\n".format(cdr_path))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()