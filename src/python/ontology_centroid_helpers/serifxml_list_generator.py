import os

def get_doc_id_to_doc_path(list_path,suffix=".xml"):
    ret = dict()
    with open(list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id.replace(".sgm.xml","").replace(".serifxml","").replace(".xml","")
            ret[doc_id] = i
    return ret

def main():
    care_doc_id_list = "/home/hqiu/tmp/mentioned_docids"
    care_serif_lists = {
        "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/legacy_cx.list",
        "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/legacy_wm.list",
        "/nfs/ld100/u10/hqiu/Hume_pipeline_int/Hume/expts/wm_382.generic.093020/learnit_decoder/learnit/learnit_decoder.list",
        "/nfs/raid88/u10/data/annotation/causal_relations/wm_dart.100219.v1.generic_events/serifxml.list",
        "/nfs/raid88/u10/users/hqiu_ad/lists/serifxmls/WM/wm_factiva.120919.list"
    }
    doc_id_to_serif_path = dict()
    for care_serif_list in care_serif_lists:
        doc_id_to_serif_path.update(get_doc_id_to_doc_path(care_serif_list))
    with open("/nfs/raid88/u10/users/hqiu_ad/lists/serifxmls/WM/all_annotated_030821.list",'w') as wfp:
        with open(care_doc_id_list) as fp:
            for i in fp:
                i = i.strip()
                if not i in doc_id_to_serif_path:
                    print(i)
                wfp.write("{}\n".format(doc_id_to_serif_path[i]))

if __name__ == "__main__":
    main()