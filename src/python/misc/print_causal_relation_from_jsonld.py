import codecs
import json
import os


def get_groundings(extraction):
    string_types = ""
    for grounding in sorted(extraction["grounding"],key=lambda x:x['value'],reverse=True):
        concept = grounding["ontologyConcept"]
        conf = grounding["value"]
        string_types = string_types + concept + ":" + str(conf) + ";\n"
    return string_types


def get_text(extraction):
    string_types = ""
    if "mentions" in extraction:
        for m in extraction["mentions"]:
            string_types = string_types + m["text"] + ";"
    else:
        string_types = extraction["text"]
    return string_types


if __name__ == "__main__":
    # filename = "/home/hqiu/ld100/hume_pipeline_read_only/Hume/expts/wm_dart.082919/serialization/analytic/wm_dart.082919.json-ld"
    # filename="/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_hume_indra_unittest.082619.v3/serialization/analytic/wm_hume_indra_unittest.082619.v3.json-ld"
    # filename = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_dart.092719/serialization/analytic/wm_dart.092719.json-ld"
    import argparse
    parser= argparse.ArgumentParser()
    parser.add_argument("--serialization_root",required=True)
    args = parser.parse_args()
    serialization_root = args.serialization_root
    # serialization_root = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_dart.101119.v1/serialization"
    rel_cnt = 0
    for root, dirs, files in os.walk(serialization_root):
        for file in files:
            if file.endswith(".json-ld"):
                filename = os.path.join(root,file)
                with codecs.open(filename, 'r', encoding='utf-8') as f:
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
                        if extraction["type"] == "relation" and extraction['subtype'] in {"causation", "precondition", "prevention",
                                                                                          "catalyst", "migration",
                                                                                          "temporallyPrecedes"}:
                            if extraction["@id"] in event_event_relation_id_to_event_event_relation:
                                print("DUPLICATE: {}".format(extraction['@id']))
                            else:
                                event_event_relation_id_to_event_event_relation[extraction["@id"]] = extraction

                    for relation_id, relation in event_event_relation_id_to_event_event_relation.items():
                        src_event = None
                        dst_event = None
                        for argument in relation['arguments']:
                            if argument["type"] == "source":
                                src_event = event_id2event[argument['value']['@id']]
                            if argument['type'] == "destination":
                                dst_event = event_id2event[argument['value']['@id']]
                        print("{} Sentence: {}".format(rel_cnt,sent_id2text[relation['provenance'][0]["sentence"]]))
                        rel_cnt += 1
                        print("\n{}\n{}\n{}\n\n{}\n{}".format(src_event['trigger']['text'].replace("\n", " "),
                                                              get_groundings(src_event), relation['subtype'],
                                                              dst_event['trigger']['text'].replace("\n", " "), get_groundings(dst_event)))
                        print("----")
