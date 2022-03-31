import os,sys,json,io
import requests



def main():
    json_ld_dir = "/nfs/mercury-07/u26/hqiu_ad/delivered/wm/053121.new_ontology"
    uri = "Redacted/dart/api/v1/readers/upload"
    with requests.Session() as s:
        s.auth = ('Redacted', 'Redacted')
        for root,dirs,files in os.walk(json_ld_dir):
            for file in files:
                if file.endswith(".json-ld"):
                    with open(os.path.join(root, file), encoding='utf-8') as fp:
                        j = json.load(fp)
                        assert len(j['documents']) == 1
                        doc_uuid = j['documents'][0]['@id']
                    with open(os.path.join(root, file),'rb') as fp:
                        metadata = {"identity":"hume","version":"R2021_05_20_1.after","document_id":doc_uuid}
                        metadata_io = io.BytesIO(json.dumps(metadata,ensure_ascii=False).encode("utf-8"))
                        metadata_io.seek(0)
                        r = s.post(uri,files={
                            "metadata":(None,json.dumps(metadata,ensure_ascii=False)),
                            "file":fp
                        })
                        print(r.json())



if __name__ == "__main__":
    main()