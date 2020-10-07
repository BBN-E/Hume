import os,json

def single_document_handler(cag):
    sent_id_to_sent_txt = dict()
    for doc in cag['documents']:
        for sent in doc['sentences']:
            sent_id_to_sent_txt[sent['@id']] = sent['text']
    for extraction in cag['extractions']:
        if extraction['type'] in {"relation"}:
            continue
        if 'provenance' in extraction:
            provenance = extraction['provenance'][0]
            sent_txt = sent_id_to_sent_txt[provenance['sentence']]
            offs_s,offs_e = provenance['sentenceCharPositions']['start'],provenance['sentenceCharPositions']['end']
            if sent_txt[offs_s:offs_e+1].replace(" ","").replace("\n","") != extraction['text'].replace(" ","").replace("\n",""):
                print("AAA")
                print(sent_txt[offs_s:offs_e+1])
                print(extraction['text'])
            else:
                print("BBB {} {} {} {} {}".format(extraction['@id'],(offs_s,offs_e+1),sent_txt,sent_txt[offs_s:offs_e+1],extraction['text']))



def main():
    input_dir = "/nfs/raid88/u10/users/hqiu/runjob/expts/47943.092420.v1/hume_test.dart.082720.wm.v1/serialization/a81affa173f91cb4d0f2fb302afc65e4"
    for root,dirs,files in os.walk(input_dir):
        for file in files:
            if file.endswith(".json-ld"):
                with open(os.path.join(root,file)) as fp:
                    cag = json.load(fp)
                    single_document_handler(cag)

if __name__ == "__main__":
    main()