# Sample call:
# python /nfs/raid66/u14/users/azamania/git/Hume/src/python/util/actor_expansion.py /nfs/raid87/u11/users/azamania/actor_aggregation/actor_id_list.txt /nfs/raid87/u11/users/azamania/actor_aggregation/pickled_kbs/ /nfs/raid87/u11/users/azamania/actor_aggregation/awake_db_relations.tsv /nfs/raid87/u11/users/azamania/actor_aggregation/bad_relations.tsv /nfs/raid87/u11/users/azamania/actor_aggregation/combined_relations.tsv

# awake_db_relations.tsv came from running Hume/src/python/misc/get_actor_aggregation_info_awake_db.py

import pickle
import os, sys, codecs, unidecode, operator

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'knowledge_base'))

from knowledge_base import KnowledgeBase

def is_input_actor(entity_id, kb, input_actor_ids):
    kb_entity = kb.entid_to_kb_entity[entity_id]
    if kb_entity.canonical_name is None:
        return False
    actor_id = entity_to_actor_id[kb_entity]
    return actor_id in input_actor_ids
    
def ignore_relation(kb_relation):
    relation_type = kb_relation.relation_type
    return relation_type in ["ART.User-Owner-Inventor-Manufacturer",
                             "ORG-AFF.Investor-Shareholder",
                             "PART-WHOLE.Geographical",
                             "PHYS.Near"]

def load_relations_from_kb_relations(kb, known_relations, new_relations, input_actor_ids, entity_to_actor_id):
    rel_length = len(kb.relid_to_kb_relation)
    count = 0
    for relid, kb_relation in kb.relid_to_kb_relation.iteritems():
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

                lookup_relation = left_external_uri + "\taffiliated_with\t" + right_external_uri
                if lookup_relation in known_relations:
                    continue
                new_relation = left_external_uri + "\taffiliated_with\t" + right_external_uri + "\t0.0\t# " + left_canonical_name + " affiliated_with " + right_canonical_name
                if new_relation not in new_relations:
                    new_relations[new_relation] = 0
                new_relations[new_relation] += 1

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

def calculate_score(count, max_count):
    max_count = float(max_count)
    s = count / max_count
    if s > 1.0:
        s = 1.0

    s = s * 0.95

    if s < 0.5:
        s = 0.5
    
    return s

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print "Usage: input_actor_id_file pickled_kb_dir awake_relations_file bad_relations_file output_file"
        sys.exit(1)
        
    actor_list, pickled_kb_dir, awake_relations, bad_relations, output_file = sys.argv[1:]

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

    actors_already_found = set()

    known_relations = set()

    # Known bad relations
    b = codecs.open(bad_relations, 'r', encoding='utf8')
    for line in b:
        known_relations.add(line.strip())
    b.close()

    # Known relations from AWAKE output
    a = codecs.open(awake_relations, 'r', encoding='utf8')
    for line in a:
        line = line.strip()
        pieces = line.split("\t")
        lookup_relation = pieces[0] + "\t" + pieces[1] + "\t" + pieces[2]
        if lookup_relation in known_relations:
            continue
        o.write(line + "\n")
        actors_already_found.add(pieces[0])
        known_relations.add(lookup_relation)
    a.close()
    
    new_relations = dict() # Tab separated triple => count
    
    filenames = os.listdir(pickled_kb_dir)
    filenames.sort()
    #filenames.reverse()
    count = 1
    for filename in filenames:
        pickled_kb_file = os.path.join(pickled_kb_dir, filename)
        p = open(pickled_kb_file, "rb")
        print(pickled_kb_file + " (" + str(count) + "/" + str(len(filenames)) + ")")
        count += 1
        kb = pickle.load(p)

        entity_to_actor_id = load_entity_to_actor_id(kb)
    
        load_relations_from_kb_relations(kb, known_relations, new_relations, input_actor_ids, entity_to_actor_id)

    sorted_new_relations = sorted(new_relations.items(), key=operator.itemgetter(1))
    sorted_new_relations.reverse()

    for new_relation, count in sorted_new_relations:
        if count == 1:
            continue
        score = calculate_score(count, 10)
        
        str_score = "{0:.2f}".format(score)
        pieces = new_relation.split("\t")
        if pieces[0] in actors_already_found:
            continue
        actors_already_found.add(pieces[0])
        new_relation = pieces[0] + "\t" + pieces[1] + "\t" + pieces[2] + "\t" + str_score + "\t" + pieces[4]
        #new_relation = pieces[0] + "\t" + pieces[1] + "\t" + pieces[2] + "\t" + str(count) + "\t" + pieces[4]
        o.write(new_relation + "\n")

    o.close()
