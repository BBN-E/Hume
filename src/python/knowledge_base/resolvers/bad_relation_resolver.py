import sys, os, codecs
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

# Remove relation when left arg is same entity as right arg
class BadRelationResolver(KBResolver):
    def __init__(self):
        pass

    def resolve(self, kb):
        print "BadRelationResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(BadRelationResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_relations_and_relation_groups()

        for relid, relation in kb.get_relations():
            # Always let event-event relations through
            if relation.argument_pair_type == "event-event":
                resolved_kb.add_relation(relation)
                continue

            # Entity-level arguments are the same, skip
            if relation.left_argument_id == relation.right_argument_id:
                #print "Skipping relation (1): " + relation.id
                continue

            # Cross-document entities will end up the same if the 
            # args have the same cameo_country_code, so skip
            left_entity = kb.entid_to_kb_entity[relation.left_argument_id]
            right_entity = kb.entid_to_kb_entity[relation.right_argument_id]
            if (left_entity.properties.get("cameo_country_code") is not None and
                right_entity.properties.get("cameo_country_code") is not None and
                left_entity.properties.get("cameo_country_code") == right_entity.properties.get("cameo_country_code")):
                #print "Skipping relation (2): " + relation.id
                continue
            
            resolved_kb.add_relation(relation)

        return resolved_kb
