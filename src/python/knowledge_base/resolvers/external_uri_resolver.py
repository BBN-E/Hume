
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver
from resolvers.utilities.awake_db import AwakeDB

class ExternalURIResolver(KBResolver):
    
    def __init__(Self):
        pass

    def resolve(self, kb, awake_db):
        print("ExternalURIResolver RESOLVE")
        resolved_kb = KnowledgeBase()
        
        super(ExternalURIResolver, self).copy_all(resolved_kb, kb)
        if awake_db == "NA":
            return resolved_kb
        
        kb_entity_to_entity_group = dict()
        for entgroupid, kb_entity_group in resolved_kb.get_entity_groups():
            for kb_entity in kb_entity_group.members:
                kb_entity_to_entity_group[kb_entity] = kb_entity_group
        
        AwakeDB.initialize_awake_db(awake_db)
        for entid, kb_entity in resolved_kb.entid_to_kb_entity.items():
            kb_entity_group = kb_entity_to_entity_group[kb_entity]
            source_string = AwakeDB.get_source_string(kb_entity_group.actor_id)
            if source_string is not None and source_string.find("dbpedia.org") != -1:
                formatted_string = source_string.strip()
                if source_string.startswith("<"):
                    source_string = source_string[1:]
                if source_string.endswith(">"):
                    source_string = source_string[0:-1]
                source_string = source_string.replace("dbpedia.org/resource", "en.wikipedia.org/wiki", 1)
                kb_entity.properties["external_uri"] = source_string
            # For countries, add geoname_id to properties
            if (kb_entity_group.actor_id is not None 
                and "external_uri" not in kb_entity.properties 
                and "geonameid" not in kb_entity.properties):
                geonameid = AwakeDB.get_geonameid_from_actorid(kb_entity_group.actor_id)
                if geonameid is not None and len(str(geonameid).strip()) != 0:
                    kb_entity.properties["geonameid"] = str(geonameid)
                
        return resolved_kb
