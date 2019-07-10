import codecs, os, json
from json_encoder import ComplexEncoder
from elements.kb_event_mention import KBEventMention
from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from elements.unification.unification_relation_frame import UnificationRelationFrame

class UnificationSerializer:
    def __init__(self):
        pass

    def serialize(self, kb, output_json_directory):
        print "UnificationSerializer SERIALIZE"

        causal_relation_count = 0
        merged_relation_count = 0
        
        if not os.path.isdir(output_json_directory):
            os.makedirs(output_json_directory)

        results = dict() # Docid => [ UnificationFrame, UnificationFrame, ] ...

        for rel_id, kb_relation in kb.get_relations():
            if kb_relation.argument_pair_type != "event-event" or kb_relation.relation_type == "Before-After":
                continue
            
            for kb_relation_mention in kb_relation.relation_mentions:
                causal_relation_count += 1
                docid = kb_relation_mention.document.properties["uuid"]
                if docid not in results:
                    results[docid] = []
                
                new_relation_frame = UnificationRelationFrame(kb_relation, kb_relation_mention, kb)
                
                # Check for duplicates
                merged = False
                for existing_relation_frame in results[docid]:
                    if existing_relation_frame.is_duplicate_of(new_relation_frame):
                        #print "Merging with " + existing_relation_frame.id + " " + kb_relation_mention.document.properties["uuid"]
                        existing_relation_frame.merge_with(new_relation_frame)
                        #new_relation_frame.status = "MERGED WITH: " + existing_relation_frame.id 
                        merged = True
                        merged_relation_count += 1
                        break

                if not merged:
                    #new_relation_frame.id = str(causal_relation_count)
                    results[docid].append(new_relation_frame)

                # DEBUG REMOVE!!
                #if merged:
                #    results[docid].append(new_relation_frame)
            
        for docid, frame_list in results.iteritems():
            output_json_file = os.path.join(output_json_directory, docid + ".json")
            o = codecs.open(output_json_file, 'w', encoding='utf8')
            o.write(json.dumps(frame_list, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
            o.close()

        for docid, kb_document in kb.docid_to_kb_document.iteritems():
            uuid = kb_document.properties["uuid"]
            if uuid not in results:
                output_json_file = os.path.join(output_json_directory, uuid + ".json")
                o = codecs.open(output_json_file, 'w', encoding='utf8')
                o.write("[]\n")
                o.close()

        print "Total causal relations: " + str(causal_relation_count)
        print "Merged relations: " + str(merged_relation_count)
