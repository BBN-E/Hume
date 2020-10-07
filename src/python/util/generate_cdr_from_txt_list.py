import os,sys,shutil
import json
import hashlib
import datetime

dummy_cdr = {
    "document_id": None,
    "source_uri": "GOOGLE_DOC",
    "extracted_metadata": {
        "CreationDate": datetime.datetime.utcnow().strftime("%Y-%m-%d")
    },
    "extracted_text": None,
    "extracted_ntriples": ""
}

def main(txt_list,output_dir):
    shutil.rmtree(output_dir,ignore_errors=True)
    os.makedirs(output_dir,exist_ok=True)

    for txt in txt_list:
        doc_id = hashlib.sha224(txt.encode('utf-8')).hexdigest()[:32]
        dummy_cdr['document_id'] = doc_id
        dummy_cdr['extracted_text'] = txt
        with open(os.path.join(output_dir,'{}.json'.format(doc_id)),'w') as wfp:
            json.dump(dummy_cdr,wfp,indent=4,sort_keys=True,ensure_ascii=False)


if __name__ == "__main__":
    txt_list = [
        "The increasing trend in cereal prices may provide a source of food insecurity, particularly in the case for poor, urban households who rely on subsidized wheat as their primary sources of carbohydrates. The price of wheat, however, is expected to stabilize owing to anticipated imports in the coming months."
    ]
    output_dir = "/nfs/raid88/u10/users/hqiu/raw_corpus/wm/mitre_072720"
    main(txt_list,output_dir)