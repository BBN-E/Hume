import codecs
import json
import os,multiprocessing


def get_groundings(extraction):
    ret = list()
    for grounding in sorted(extraction["grounding"],key=lambda x:x['value'],reverse=True):
        concept = grounding["ontologyConcept"]
        ret.append((concept,grounding['value']))
    return ret


def get_text(extraction):
    string_types = ""
    if "mentions" in extraction:
        for m in extraction["mentions"]:
            string_types = string_types + m["text"] + ";"
    else:
        string_types = extraction["text"]
    return string_types


def single_documnet_worker(json_ld_path):
    event_type_to_grounded_top1_cnt = dict()
    event_type_to_grounded_cnt = dict()
    event_type_to_grounded_cnt_causal = dict()
    causal_cnt = dict()
    generic_endpoint = {"/wm/process","/wm/concept"}
    grounded_event_id = set()
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
            if extraction["type"] == "relation" and extraction['subtype'] in {"causation","precondition","catalyst","mitigation","prevention"}:
                if extraction["@id"] in event_event_relation_id_to_event_event_relation:
                    print("DUPLICATE: {}".format(extraction['@id']))
                else:
                    event_event_relation_id_to_event_event_relation[extraction["@id"]] = extraction

        for event_id,event in event_id2event.items():
            groundings = get_groundings(event)
            top_1_type,top1_score = max(groundings,key=lambda x:x[1])
            event_type_to_grounded_top1_cnt[top_1_type] = event_type_to_grounded_top1_cnt.setdefault(top_1_type,0)+1
            only_generic_grounded = True
            for ev_type,score in groundings:
                event_type_to_grounded_cnt[ev_type] = event_type_to_grounded_cnt.setdefault(ev_type,0)+1
                if ev_type not in generic_endpoint:
                    only_generic_grounded = False
            if only_generic_grounded is False:
                grounded_event_id.add(event_id)

        single_end_grounded_eerm = set()
        dual_end_grounded_eerm = set()

        for relation_id, relation in event_event_relation_id_to_event_event_relation.items():
            src_event = None
            dst_event = None
            end_grounded = 0
            for argument in relation['arguments']:
                if argument["type"] == "source":
                    src_event = event_id2event[argument['value']['@id']]
                    if argument['value']['@id'] in grounded_event_id:
                        end_grounded += 1
                if argument['type'] == "destination":
                    dst_event = event_id2event[argument['value']['@id']]
                    if argument['value']['@id'] in grounded_event_id:
                        end_grounded += 1
            if end_grounded == 1:
                single_end_grounded_eerm.add(relation_id)
            elif end_grounded == 2:
                dual_end_grounded_eerm.add(relation_id)
            for ev_type,score in get_groundings(src_event):
                event_type_to_grounded_cnt_causal[ev_type] = event_type_to_grounded_cnt_causal.get(ev_type,0)+1
            for ev_type,score in get_groundings(dst_event):
                event_type_to_grounded_cnt_causal[ev_type] = event_type_to_grounded_cnt_causal.get(ev_type,0)+1
            causal_cnt[relation['subtype']] = causal_cnt.get(relation['subtype'],0) + 1

    return event_type_to_grounded_top1_cnt,event_type_to_grounded_cnt,event_type_to_grounded_cnt_causal,causal_cnt,len(grounded_event_id),len(single_end_grounded_eerm),len(dual_end_grounded_eerm)

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
    serialization_root = "/d4m/ears/expts/48231.072721.v1/expts/hume_test.dart.082720.wm.v1/serialization"
    output_dir = "/d4m/ears/expts/48231.072721.v1/expts/hume_test.dart.082720.wm.v1/compositional_statistics"
    manager = multiprocessing.Manager()
    event_type_to_grounded_top1_cnt_total = dict()
    event_type_to_grounded_cnt_total = dict()
    event_type_to_grounded_cnt_causal_total = dict()
    causal_cnt_total = dict()
    num_grounded_evt_total = 0
    num_single_grounded_eerm_total = 0
    num_dual_grounded_eerm_total = 0
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        for root, dirs, files in os.walk(serialization_root):
            for file in files:
                if file.endswith(".json-ld"):
                    filename = os.path.join(root,file)
                    workers.append(pool.apply_async(single_documnet_worker,args=(filename,)))
                    if len(workers) % 1000 == 0:
                        print("Scheduled {}".format(len(workers)))

        for idx,i in enumerate(workers):
            if idx % 1000 == 0:
                print("Waiting {}/{}".format(idx,len(workers)))
            i.wait()
            event_type_to_grounded_top1_cnt,event_type_to_grounded_cnt,event_type_to_grounded_cnt_causal,causal_cnt,num_grounded_evt,num_single_grounded_eerm,num_dual_grounded_eerm = i.get()
            for event_type, cnt in event_type_to_grounded_top1_cnt.items():
                event_type_to_grounded_top1_cnt_total[event_type] = event_type_to_grounded_top1_cnt_total.get(event_type,0)+cnt
            for event_type,cnt in event_type_to_grounded_cnt.items():
                event_type_to_grounded_cnt_total[event_type] = event_type_to_grounded_cnt_total.get(event_type,0)+cnt
            for event_type,cnt in event_type_to_grounded_cnt_causal.items():
                event_type_to_grounded_cnt_causal_total[event_type] = event_type_to_grounded_cnt_causal_total.get(event_type,0)+cnt
            for cf_type,cnt in causal_cnt.items():
                causal_cnt_total[cf_type] = causal_cnt_total.get(cf_type,0) + cnt
            num_grounded_evt_total += num_grounded_evt
            num_single_grounded_eerm_total += num_single_grounded_eerm
            num_dual_grounded_eerm_total += num_dual_grounded_eerm


    with open(os.path.join(output_dir,"general.cnt"),'w') as wfp:
        for event_type, cnt in event_type_to_grounded_cnt_total.items():
            wfp.write("{}\t{}\n".format(cnt,event_type))
    with open(os.path.join(output_dir,"in_causal.cnt"),'w') as wfp:
        for event_type, cnt in event_type_to_grounded_cnt_causal_total.items():
            wfp.write("{}\t{}\n".format(cnt,event_type))
    with open(os.path.join(output_dir,"general_top1.cnt"),'w') as wfp:
        for event_type, cnt in event_type_to_grounded_top1_cnt_total.items():
            wfp.write("{}\t{}\n".format(cnt,event_type))
    with open(os.path.join(output_dir,'causal.cnt'),'w') as wfp:
        for cf_type,cnt in causal_cnt_total.items():
            wfp.write("{}\t{}\n".format(cnt,cf_type))

    with open(os.path.join(output_dir,'grounded_evt.cnt'),'w') as wfp:
        wfp.write("{}\n".format(num_grounded_evt_total))

    with open(os.path.join(output_dir,'single_end_grounded_eerm.cnt'),'w') as wfp:
        wfp.write("{}\n".format(num_single_grounded_eerm_total))

    with open(os.path.join(output_dir,'dual_end_grounded_eerm.cnt'),'w') as wfp:
        wfp.write("{}\n".format(num_dual_grounded_eerm_total))