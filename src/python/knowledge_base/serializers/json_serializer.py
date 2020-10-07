import codecs
import json
import logging
import os
import sys

from json_encoder import ComplexEncoder

logger = logging.getLogger(__name__)
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
class JSONSerializer:
    def __init__(self):
        pass
        
    def serialize(self, kb, output_json_file):
        print("JSONSerializer SERIALIZE")

        o = codecs.open(output_json_file, 'w', encoding='utf8')
    
        result = dict()
        result["documents"] = list(kb.docid_to_kb_document.values())
        result["entities"] = list(kb.entid_to_kb_entity.values())
        result["relations"] = list(kb.relid_to_kb_relation.values())
        result["events"] = list(kb.evid_to_kb_event.values())
        result["entity_groups"] = list(kb.entgroupid_to_kb_entity_group.values())
        result["relation_groups"] = list(kb.relgroupid_to_kb_relation_group.values())
        result["event_groups"] = list(kb.evgroupid_to_kb_event_group.values())

        o.write(json.dumps(result, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
        o.close()


if __name__ == "__main__":
    import pickle

    if len(sys.argv) != 3:
        print("Usage: " + sys.argv[0] + " pickled_kb_file output_json_file")
        sys.exit(1)
    json_serializer = JSONSerializer()
    with open(sys.argv[1], "rb") as pickle_stream:
        logger.info("Loading pickle file...")
        kb = pickle.load(pickle_stream)
        logger.info("Done loading. Serializing...")
        json_serializer.serialize(kb, sys.argv[2])
