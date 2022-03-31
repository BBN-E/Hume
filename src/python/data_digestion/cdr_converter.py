import datetime
import io
import json
import os
import random
import shutil
import sys

current_script_path = __file__
sys.path.append(os.path.realpath(os.path.join(current_script_path, os.path.pardir)))

from hume_corpus import make_sgm_file


def get_corpus_from_cdr_list(file_list_path):
    ret = list()
    with open(file_list_path, 'r') as fp:
        for path in fp:
            path = path.strip()
            with io.open(path, encoding='utf-8') as fp:
                ret.append((path, json.load(fp)))
    return ret


def is_news(cdr_doc):
    extracted_text = cdr_doc.get('extracted_text', None)
    if extracted_text is None:
        return False

    if "pdf" in cdr_doc.get("content_type", "").lower():
        return False

    if cdr_doc.get("extracted_metadata", dict()).get("Pages", 1) < 1:
        return True

    # if "Dow Jones" in cdr_doc.get('extracted_metadata',dict()).get("Producer","UNKNOWN"):
    #     return True

    if len(extracted_text) < 50000:
        return True

    return False


def main(input_cdr_list, output_folder, breaking_point=30000):
    shutil.rmtree(output_folder, ignore_errors=True)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(os.path.join(output_folder, 'sgms'), exist_ok=True)
    # os.makedirs(os.path.join(output_folder,'txts'),exist_ok=True)
    # os.makedirs(os.path.join(output_folder,'cdrs'),exist_ok=True)
    booking_arr = list()
    sgm_path_list = list()
    # scanner = get_corpus_from_docker()
    # scanner = get_corpus_from_local("/nfs/raid88/u10/users/hqiu/raw_corpus/cx/cdr-backup-1575698041052.zip")
    scanner = get_corpus_from_cdr_list(input_cdr_list)

    for cdr_path, doc in scanner:
        # with open(os.path.join(output_folder,'cdrs',doc['document_id']+".json"),'w') as fp:
        #     json.dump(doc,fp,ensure_ascii=False,indent=4,sort_keys=True)
        # do something with `doc`
        # for example, print the file_name
        doc_uuid = doc['document_id']
        source_uri = "UNKNOWN"
        if "source_uri" in doc:
            source_uri = doc['source_uri']
        creation_date_str = "UNKNOWN"

        author = doc["extracted_metadata"].get('Author', 'UNKNOWN')
        if author is None:
            author = "UNKNOWN"
        else:
            author = author.replace("\t", " ").replace("\n", " ")
        if doc["extracted_metadata"].get('CreationDate', None) is not None:
            creation_date = datetime.datetime.strptime(doc["extracted_metadata"].get('CreationDate', None), '%Y-%m-%d')
            creation_date_str = creation_date.strftime("%Y%m%d")
        extracted_text = doc.get('extracted_text', None)
        if extracted_text is None:
            print("Skipping: {}".format(doc_uuid))
            continue
        # bs4_text = doc['_source']['extracted_text'].get("bs4","")
        # make_sgm_file(extracted_text,doc_uuid,output_folder,s3_source_uri,source_uri,"news","ENG_NW_CX_SAMS_baltic",creation_date_str,author,booking_arr,sgm_path_list)
        if is_news(doc):
            make_sgm_file(extracted_text, doc_uuid, output_folder, cdr_path, source_uri, "news_{}".format(doc_uuid),
                          "ENG_NW_WM", creation_date_str, author, booking_arr, sgm_path_list, breaking_point)
        else:
            make_sgm_file(extracted_text, doc_uuid, output_folder, cdr_path, source_uri, "analytic_{}".format(doc_uuid),
                          "ENG_NW_WM", creation_date_str, author, booking_arr, sgm_path_list, breaking_point)
        # make_txt_file(extracted_text,doc_uuid,output_folder)
    with open(os.path.join(output_folder, "metadata.txt"), 'w') as wfp:
        for i in booking_arr:
            wfp.write("{}\n".format(i))
    random.shuffle(sgm_path_list)
    with open(os.path.join(output_folder, 'sgms.list'), 'w') as wfp:
        for i in sgm_path_list:
            wfp.write("{}\n".format(i))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--breaking_point', required=False, type=int, default=30000)
    parser.add_argument('--input_cdr_list', required=True)
    parser.add_argument('--output_folder', required=True)
    args = parser.parse_args()
    main(args.input_cdr_list, args.output_folder, args.breaking_point)
