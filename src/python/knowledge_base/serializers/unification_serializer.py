import codecs, os, json, tarfile, io, time
from json_encoder import ComplexEncoder
from elements.kb_event_mention import KBEventMention
from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from elements.unification.unification_relation_frame import UnificationRelationFrame
from elements.unification.unification_event_frame import UnificationEventFrame


def string_to_tarfile(name, string):
    encoded = string.encode('utf-8')
    s = io.BytesIO(encoded)

    tar_info = tarfile.TarInfo(name=name)
    tar_info.mtime = time.time()
    tar_info.size = len(encoded)

    return s, tar_info


class UnificationSerializer:
    def __init__(self):
        pass

    def serialize(self, kb, output_json_directory):
        print("UnificationSerializer SERIALIZE")

        causal_relation_count = 0
        merged_relation_count = 0
        merged_event_count = 0

        os.makedirs(output_json_directory, exist_ok=True)
        os.makedirs(os.path.join(output_json_directory,"unification_json/relation"), exist_ok=True)
        os.makedirs(os.path.join(output_json_directory,"unification_json/event"), exist_ok=True)

        # Relation json
        results = dict()  # Docid => [ UnificationFrame, UnificationFrame, ] ...
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
                # merged = False
                # for existing_relation_frame in results[docid]:
                #     if existing_relation_frame.is_duplicate_of(new_relation_frame):
                #         #print "Merging with " + existing_relation_frame.id + " " + kb_relation_mention.document.properties["uuid"]
                #         existing_relation_frame.merge_with(new_relation_frame)
                #         #new_relation_frame.status = "MERGED WITH: " + existing_relation_frame.id 
                #         merged = True
                #         merged_relation_count += 1
                #         break

                # if not merged:
                # new_relation_frame.id = str(causal_relation_count)
                if True:
                    results[docid].append(new_relation_frame)

                # DEBUG REMOVE!!
                # if merged:
                #    results[docid].append(new_relation_frame)
        for docid, frame_list in results.items():
            with open(os.path.join(output_json_directory,"unification_json/relation/{}.json".format(docid)),'w') as wfp:
                json.dump(frame_list,wfp,sort_keys=True,indent=4,cls=ComplexEncoder,ensure_ascii=False)

        for docid, kb_document in kb.docid_to_kb_document.items():
            uuid = kb_document.properties["uuid"]
            if uuid not in results:
                with open(os.path.join(output_json_directory, "unification_json/relation/{}.json".format(docid)), 'w') as wfp:
                    json.dump([], wfp, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False)

        # Event json
        results = dict()  # Docid => [ UnificationEventFrame, UnificationEventFrame, ] ...
        for ev_id, kb_event in kb.get_events():
            for kb_event_mention in kb_event.event_mentions:
                docid = kb_event_mention.document.properties["uuid"]
                if docid not in results:
                    results[docid] = []

                new_event_frame = UnificationEventFrame(kb_event_mention, kb)

                # Check for duplicates
                # merged = False
                # for existing_event_frame in results[docid]:
                #     if existing_event_frame.is_duplicate_of(new_event_frame):
                #         #print "Merging with " + existing_event_frame.id + " " + kb_event_mention.document.properties["uuid"]
                #         existing_event_frame.merge_with(new_event_frame)
                #         #new_event_frame.status = "MERGED WITH: " + existing_event_frame.id
                #         merged = True
                #         merged_event_count += 1
                #         break

                # if not merged:
                # new_event_frame.id = str(causal_event_count)
                if True:
                    results[docid].append(new_event_frame)

        for docid, frame_list in results.items():
            with open(os.path.join(output_json_directory,"unification_json/event/{}.json".format(docid)),'w') as wfp:
                json.dump(frame_list,wfp,sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False)

        for docid, kb_document in kb.docid_to_kb_document.items():
            uuid = kb_document.properties["uuid"]
            if uuid not in results:
                with open(os.path.join(output_json_directory, "unification_json/event/{}.json".format(docid)),
                          'w') as wfp:
                    json.dump([], wfp, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False)

        print("Total causal relations: " + str(causal_relation_count))
        print("Merged relations: " + str(merged_relation_count))
