# sample call: python3 /nfs/raid66/u14/users/azamania/git/Hume/src/python/actor_aggregation/output_relation_counts_from_kb.py /nfs/raid87/u11/users/azamania/actor_aggregation/actor_id_list.txt /nfs/raid87/u11/users/azamania/runjobs/expts/Hume/causeex_collab2_0916c_m24_shaved_dataset_serialization/serialization/COLLAB2_0/causeex_collab2_0916c_m24_shaved_dataset_serialization.p /nfs/raid87/u11/users/azamania/actor_aggregation_dec/kb_relations.tsv

import pickle
import os, sys, codecs, operator

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'knowledge_base'))

from knowledge_base import KnowledgeBase


def is_input_actor(entity_id, kb, input_actor_ids):
    kb_entity = kb.entid_to_kb_entity[entity_id]
    if kb_entity.canonical_name is None:
        return False
    actor_id = entity_to_actor_id[kb_entity]
    return actor_id in input_actor_ids

def get_canonical_name_and_external_uri(kb, entity_id):
    canonical_name = None
    external_uri = None

    if entity_id in kb.entid_to_kb_entity:
        kb_entity = kb.entid_to_kb_entity[entity_id]
        canonical_name = kb_entity.canonical_name

        if "external_uri" in kb_entity.properties:
            external_uri = kb_entity.properties["external_uri"]
        elif "geonameid" in kb_entity.properties:
            external_uri = "http://www.geonames.org/" + kb_entity.properties["geonameid"]

        return canonical_name, external_uri

def load_entity_to_actor_id(kb):
    results = dict()
    for entgroupid, entgroup in kb.get_entity_groups():
        for entity in entgroup.members:
            results[entity] = entgroup.actor_id
    return results

def ignore_relation(kb_relation):
    relation_type = kb_relation.relation_type
    return relation_type in ["ART.User-Owner-Inventor-Manufacturer",
                             "ORG-AFF.Investor-Shareholder",
                             "PART-WHOLE.Geographical",
                             "PHYS.Near"]

def load_relations_from_kb_relations(kb, relations, input_actor_ids, entity_to_actor_id):
    rel_length = len(kb.relid_to_kb_relation)
    count = 0
    for relid, kb_relation in kb.relid_to_kb_relation.items():
        count += 1
        if ignore_relation(kb_relation):
            continue
        if kb_relation.argument_pair_type == "entity-entity":
            left_entity_id = kb_relation.left_argument_id
            right_entity_id = kb_relation.right_argument_id
            
            if not is_input_actor(right_entity_id, kb, input_actor_ids):
                continue

            left_canonical_name, left_external_uri = get_canonical_name_and_external_uri(kb, left_entity_id)
            right_canonical_name, right_external_uri = get_canonical_name_and_external_uri(kb, right_entity_id)

            if left_canonical_name is not None and \
                left_external_uri is not None and \
                right_canonical_name is not None and \
                right_external_uri is not None:

                relation = (left_external_uri, right_external_uri,)
                if relation not in relations:
                    relations[relation] = 0
                relations[relation] += 1

if __name__ == "__main__":
    if len(sys.argv) <= 3:
        print("Usage: " + sys.argv[0] + "input_actor_id_file output_file pickled_kb_file_1 [picked_kb_file_2]...")
        sys.exit(1)

    actor_list = sys.argv[1]
    output_file = sys.argv[2]
    pickled_kb_files = sys.argv[3:]

    input_actor_ids = set()
    i = open(actor_list)
    for line in i: 
        line = line.strip()
        if line.startswith("#"):
            continue
        pieces = line.split(" ", 1)
        input_actor_ids.add(int(pieces[0]))
    i.close()
    
    o = codecs.open(output_file, 'w', encoding='utf8')

    relations = dict() # (actor1, actor2) => count

    for pickled_kb_file in pickled_kb_files:

        kb = None
        try:
            p = open(pickled_kb_file, "rb")
            kb = pickle.load(p)
            p.close()
        except UnicodeDecodeError:
            print("Couldn't load KB")
            sys.exit(1)

        entity_to_actor_id = load_entity_to_actor_id(kb)
        
        load_relations_from_kb_relations(kb, relations, input_actor_ids, entity_to_actor_id)
    
    sorted_relations = sorted(relations.items(), key=operator.itemgetter(1))
    sorted_relations.reverse()

for relation, count in sorted_relations:
    o.write(relation[0] + "\t" + relation[1] + "\t" + str(count) + "\n")

o.close()
