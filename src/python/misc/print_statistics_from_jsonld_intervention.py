import codecs
import json
import os,multiprocessing


def get_groundings(extraction):
    for grounding in sorted(extraction["grounding"],key=lambda x:x['value'],reverse=True):
        concept = grounding["ontologyConcept"]
        if concept.startswith("/wm/concept/causal_factor/interventions"):
            return concept
        return False
    return False


def get_text(extraction):
    string_types = ""
    if "mentions" in extraction:
        for m in extraction["mentions"]:
            string_types = string_types + m["text"] + ";"
    else:
        string_types = extraction["text"]
    return string_types


def single_documnet_worker(json_ld_path):
    event_type_to_grounded_cnt = dict()
    event_type_to_grounded_cnt_causal = dict()
    with codecs.open(json_ld_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

        # cache sentences
        sent_id2text = dict()
        for doc in json_data["documents"]:
            for sent in doc["sentences"]:
                sent_id2text[sent["@id"]] = sent["text"]

        # cache entities
        entity_id2ent = dict()
        for extraction in json_data["extractions"]:
            if extraction["subtype"] == "entity":
                entity_id2ent[extraction["@id"]] = extraction

        # process events
        event_id2event = dict()
        event_event_relation_id_to_event_event_relation = dict()
        for extraction in json_data["extractions"]:
            if extraction["subtype"] == "event":
                if extraction['@id'] not in event_id2event:
                    event_id2event[extraction['@id']] = extraction
                else:
                    print("DUPLICATE: {}".format(extraction['@id']))
            if extraction["type"] == "relation" and extraction['subtype'] in {"causation"}:
                if extraction["@id"] in event_event_relation_id_to_event_event_relation:
                    print("DUPLICATE: {}".format(extraction['@id']))
                else:
                    event_event_relation_id_to_event_event_relation[extraction["@id"]] = extraction

        for event_id,event in event_id2event.items():
            if get_groundings(event) is not False:
                event_type_to_grounded_cnt[get_groundings(event)] = event_type_to_grounded_cnt.setdefault(get_groundings(event),0)+1

        for relation_id, relation in event_event_relation_id_to_event_event_relation.items():
            src_event = None
            dst_event = None
            for argument in relation['arguments']:
                if argument["type"] == "source":
                    src_event = event_id2event[argument['value']['@id']]
                if argument['type'] == "destination":
                    dst_event = event_id2event[argument['value']['@id']]
            if get_groundings(src_event) is not False:
                event_type_to_grounded_cnt_causal[get_groundings(src_event)] = event_type_to_grounded_cnt_causal.get(get_groundings(src_event),0)+1
            if get_groundings(dst_event) is not False:
                event_type_to_grounded_cnt_causal[get_groundings(dst_event)] = event_type_to_grounded_cnt_causal.get(get_groundings(dst_event),0)+1

    return event_type_to_grounded_cnt,event_type_to_grounded_cnt_causal

if __name__ == "__main__":
    # filename = "/home/hqiu/ld100/hume_pipeline_read_only/Hume/expts/wm_dart.082919/serialization/analytic/wm_dart.082919.json-ld"
    # filename="/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_hume_indra_unittest.082619.v3/serialization/analytic/wm_hume_indra_unittest.082619.v3.json-ld"
    # filename = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_dart.092719/serialization/analytic/wm_dart.092719.json-ld"
    # import argparse
    # parser= argparse.ArgumentParser()
    # parser.add_argument("--serialization_root",required=True)
    # args = parser.parse_args()
    # serialization_root = args.serialization_root
    # serialization_root = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_dart.101119.v1/serialization"
    serialization_root = "/home/hqiu/ld100/Hume_pipeline_int/Hume/expts/wm_thanksgiving.030820.v1/serialization"
    output_dir = "/home/hqiu/Public/wm_intervention_statistics.030920"
    manager = multiprocessing.Manager()
    event_type_to_grounded_cnt_total = dict()
    event_type_to_grounded_cnt_causal_total = dict()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        for root, dirs, files in os.walk(serialization_root):
            for file in files:
                if file.endswith(".json-ld"):
                    filename = os.path.join(root,file)
                    workers.append(pool.apply_async(single_documnet_worker,args=(filename,)))
        for idx,i in enumerate(workers):
            i.wait()
            event_type_to_grounded_cnt, event_type_to_grounded_cnt_causal = i.get()
            for event_type,cnt in event_type_to_grounded_cnt.items():
                event_type_to_grounded_cnt_total[event_type] = event_type_to_grounded_cnt_total.get(event_type,0)+cnt
            for event_type,cnt in event_type_to_grounded_cnt_causal.items():
                event_type_to_grounded_cnt_causal_total[event_type] = event_type_to_grounded_cnt_causal_total.get(event_type,0)+cnt

    with open(os.path.join(output_dir,"general.cnt"),'w') as wfp:
        for event_type, cnt in event_type_to_grounded_cnt_total.items():
            wfp.write("{}\t{}\n".format(cnt,event_type))
    with open(os.path.join(output_dir,"in_causal.cnt"),'w') as wfp:
        for event_type, cnt in event_type_to_grounded_cnt_causal_total.items():
            wfp.write("{}\t{}\n".format(cnt,event_type))


