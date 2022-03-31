
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver
from resolvers.utilities.awake_db import AwakeDB

import codecs, os, re

class AdditionalAffiliationResolver(KBResolver):
    cameo_code_re = re.compile(r"\w\w\w")

    def __init__(Self):
        pass

    def resolve(self, kb):
        print("AdditionalAffiliationResolver RESOLVE")
        resolved_kb = KnowledgeBase()

        super(AdditionalAffiliationResolver, self).copy_all(resolved_kb, kb)
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        
        actor_affiliation = dict() # actor_id => affiliated_actor_id e.g. "Vladimir Putin" -> "Russia"
        actor_component_of = dict() # actor_id => actor_id e.g. "Estonia" -> ["Baltic States", "NATO"]

        # Load actor_id -> actor_id/CAMEO code has affiliation
        affiliation_file = os.path.join(script_dir, "..", "data_files", "actor_affiliation_info.txt")
        a = codecs.open(affiliation_file, 'r', encoding='utf8')
        for line in a:
            line = line.strip()
            if line.startswith("#"):
                continue
            pieces = line.split(" " , 2)
            actor_id = int(pieces[0])
            affiliated_actor_id_or_cameo_code = pieces[1]
            description = pieces[2]
            actor_affiliation[actor_id] = affiliated_actor_id_or_cameo_code # assumes one affiliation per actor id
        a.close()

        # Load actor_id -> actor_id component info
        component_file = os.path.join(script_dir, "..", "data_files", "actor_component_info.txt")
        c = codecs.open(component_file, 'r', encoding='utf8')
        for line in c:
            line = line.strip()
            if line.startswith("#"):
                continue
            pieces = line.split(" " , 2)
            actor_id = int(pieces[0])
            containing_actor_id = int(pieces[1])
            description = pieces[2]
            if actor_id not in actor_component_of:
                actor_component_of[actor_id] = []
            actor_component_of[actor_id].append(containing_actor_id)
        c.close()

        # Set properties on entity groups
        for (entgroupid, entity_group) in resolved_kb.get_entity_groups():
            actor_id = entity_group.actor_id

            if actor_id is None:
                continue
            if actor_id in actor_affiliation:
                affiliated_actor_id_or_cameo_code = actor_affiliation[actor_id]
                if AdditionalAffiliationResolver.cameo_code_re.match(affiliated_actor_id_or_cameo_code):
                    entity_group.properties["awake_affiliated_cameo_code"] = affiliated_actor_id_or_cameo_code
                else:
                    entity_group.properties["awake_affiliated_actor_id"] = int(affiliated_actor_id_or_cameo_code)
            if actor_id in actor_component_of:
                if "component_of_actor_ids" not in entity_group.properties:
                    entity_group.properties["component_of_actor_ids"] = []
                entity_group.properties["component_of_actor_ids"].extend(actor_component_of[actor_id])
                
        return resolved_kb
