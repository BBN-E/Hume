import codecs
import json
import os


def get_groundings(extraction):
    string_types = ""
    for grounding in extraction["grounding"]:
        concept = grounding["ontologyConcept"]
        conf = grounding["value"]
        string_types = string_types + concept + ":" + str(conf) + ";"
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

    for root, dirs, files in os.walk("/home/hqiu/ld100/Hume_pipeline/Hume/expts/wm_dart.101419.v1/serialization"):
        for file in files:
            if file.endswith(".json-ld"):
                filename = os.path.join(root,file)

                with codecs.open(filename, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)

                    # cache sentences
                    sent_id2text = dict()
                    for doc in json_data["documents"]:
                        for sent in doc["sentences"]:
                            sent_id2text[sent["@id"]]=sent["text"]

                    # cache entities
                    entity_id2ent = dict()
                    for extraction in json_data["extractions"]:
                        if extraction["subtype"]=="entity":
                            entity_id2ent[extraction["@id"]] = {"text": get_text(extraction), "type": get_groundings(extraction)}

                    # process events
                    for extraction in json_data["extractions"]:
                        if extraction["subtype"]=="event":
                            trigger = extraction["trigger"]["head text"].replace("\n", " ")
                            sid = extraction["trigger"]["provenance"][0]["sentence"]
                            sentence = sent_id2text[sid].replace("\n", " ")
                            types = get_groundings(extraction)

                            print ("--------------------------------------------")
                            print ("sentence: " + sentence)
                            print ("trigger: " + trigger + "\ttypes: " + types)
                            for state in extraction['states']:
                                if state['type'] == "polarity":
                                    print ("Polarity: {}".format(state["text"]))

                            for a in extraction["arguments"]:
                                role = a["type"]
                                entity_id = a["value"]["@id"]

                                entity_text = entity_id2ent[entity_id]["text"].replace("\n", " ")
                                entity_type = entity_id2ent[entity_id]["type"]

                                print (" - " + role + "\t" + entity_text + "\t" + entity_type)

