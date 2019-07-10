import unidecode

from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

# Look at constituent entities of each entity group and choose a 
# single entity type for the group. 
# Note: all entities should have been placed in entity groups 
# by the SerifXMLReader. 

class EntityGroupEntityTypeResolver(KBResolver):
    
    def __init__(self):
        pass

    def resolve(self, kb):
        print "EntityGroupEntityTypeResolver RESOLVE"
        
        resolved_kb = KnowledgeBase()
        super(EntityGroupEntityTypeResolver, self).copy_all(resolved_kb, kb)

        # Make sure best entity type across each entity group is consistent
        for entgroupid, entity_group in resolved_kb.get_entity_groups():
            entity_type_to_count = dict() # entity_type => count
            for entity in entity_group.members:
                entity_type = entity.get_best_entity_type()
                if entity_type not in entity_type_to_count:
                    entity_type_to_count[entity_type] = 0
                entity_type_to_count[entity_type] += 1
            
            # Get best entity type from dict
            best_entity_type = None
            highest_count = None
            for et, count in entity_type_to_count.iteritems():
                if best_entity_type is None or count > highest_count:
                    best_entity_type = et
                    highest_count = count
                    continue
                if count < highest_count:
                    continue
                # count and highest count is equal
                best_entity_type = self.get_better_entity_type(best_entity_type, et)
            
            # set entity type for group
            if len(entity_type_to_count) > 1:
                #print "Setting entity type for " + unidecode.unidecode(entity_group.canonical_name) + " " + entity_group.id + " to " + best_entity_type
                #print "Based on: " + str(entity_type_to_count)
                for entity in entity_group.members:
                    entity.add_entity_type(best_entity_type, 0.9)

        return resolved_kb

    def get_better_entity_type(self, et1, et2):
        # Prefer ORGs
        if et1.startswith("ORG") and not et2.startswith("ORG"):
            return et1
        if et2.startswith("ORG") and not et1.startswith("ORG"):
            return et2
        
        # Prefer more general ORG type as we only call this function when confused, so choose the safe type
        if et1.endswith(".General"):
            return et1
        if et2.endswith(".General"):
            return et2

        # Tie breaker
        if et1 < et2:
            return et1

        return et2
