import json, codecs
from json_encoder import ComplexEncoder

class JSONSerializer:
    def __init__(self):
        pass
        
    def serialize(self, kb, output_json_file):
        print "JSONSerializer SERIALIZE"

        o = codecs.open(output_json_file, 'w', encoding='utf8')
    
        result = dict()
        result["documents"] = kb.docid_to_kb_document.values()
        result["entities"] = kb.entid_to_kb_entity.values()
        result["relations"] = kb.relid_to_kb_relation.values()
        result["events"] = kb.evid_to_kb_event.values()
        result["entity_groups"] = kb.entgroupid_to_kb_entity_group.values()
        result["relation_groups"] = kb.relgroupid_to_kb_relation_group.values()
        result["event_groups"] = kb.evgroupid_to_kb_event_group.values()

        o.write(json.dumps(result, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
        o.close()


