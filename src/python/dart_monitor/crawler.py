import os,sys,json
import requests

def download_cdrs_by_list(msg_list,cdr_dir,seen_text_hash):
    newly_seen_text_hash = set()
    with requests.Session() as s:
        s.auth = ('Redacted', 'Redacted')
        for idx,msg in enumerate(msg_list):
            uuid = msg['document_id']
            uri = "Redacted/dart/api/v1/cdrs/{}".format(uuid)
            print("Handling {}/{}".format(idx,len(msg_list)))
            r = s.get(uri)
            cdr = r.json()
            with open(os.path.join(cdr_dir,"{}.json".format(uuid)),'w') as fp:
                json.dump(cdr,fp,indent=4,sort_keys=True,ensure_ascii=False)

    return newly_seen_text_hash


def test_main():
    persist = "/home/hqiu/tmp/dart.030422/798361a2-05da-4b12-a2af-c314bcd578c4"
    cdr_dir = "/nfs/raid88/u10/users/hqiu_ad/raw_corpus/wm/22apr_stability"
    os.makedirs(cdr_dir,exist_ok=True)
    msg_list = list()
    for root,dirs,files in os.walk(persist):
        for file in files:
            if file.endswith(".txt"):
                doc_uuid = os.path.basename(file)[:-len(".txt")]
                with open(os.path.join(root,file)) as fp:
                    msg = json.load(fp)
                    msg["document_id"] = doc_uuid
                    msg_list.append(msg)
    seen_text_hash = set()
    newly_seen_text_hash = download_cdrs_by_list(msg_list,cdr_dir,seen_text_hash)
    seen_text_hash.update(newly_seen_text_hash)
    if len(newly_seen_text_hash) > 0:
        print("There are {} new documents. Please run the pipeline".format(len(newly_seen_text_hash)))
    else:
        print("Nothing new.")


if __name__ == "__main__":
    test_main()