import json, os, codecs, sys

json_file="/nfs/raid87/u10/users/bmin/Runjobs/expts/Hume/causeex_scs.full.nre.v1/event_event_relations/nre_event_event_relations_file.json"
print("Reading " + json_file)
json_objs=json.load(codecs.open(json_file,'r','utf-8'))
for i in range(0,len(json_objs)):
    json_obj = json_objs[i]
    relation_type = json_obj["semantic_class"]

    arg1_text = json_obj["head"]["word"]
    arg2_text = json_obj["tail"]["word"]

    confidence = 0.02
    if "confidence" in json_obj:
        confidence = json_obj["confidence"]

    sentence = json_obj["sentence"]

    print (str(confidence) + "\t" + arg1_text + "\t" + relation_type + "\t" + arg2_text + "\t" + sentence)
