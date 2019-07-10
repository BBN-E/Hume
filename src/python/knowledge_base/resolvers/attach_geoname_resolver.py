from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
import io


class AttachGeoNameResolver(KBResolver):
    def __init__(self):
        super(AttachGeoNameResolver,self).__init__()
    def resolve(self, kb, ua_south_sudan_geoid_txt_path):
        print "AttachGeoNameResolver RESOLVE"
        resolved_kb = KnowledgeBase()
        super(AttachGeoNameResolver, self).copy_all(resolved_kb, kb)

        geo_mapping_db = dict()
        with io.open(ua_south_sudan_geoid_txt_path, 'r', encoding="utf-8") as fp:
            for i in fp:
                i = i.strip()
                unpacked = i.split(" ")
                geoname = unpacked[0]
                geoid = unpacked[1]
                geo_mapping_db[geoname] = geoid
        for entid,kb_entity in resolved_kb.entid_to_kb_entity.items():
            for entity_type in kb_entity.entity_type_to_confidence.keys():
                entity_type = str(entity_type.split(".")[0])
                if (any({'GPE','LOC'}) in {entity_type}) is True:
                    canonical_name = kb_entity.canonical_name
                    if canonical_name is not None:
                        geonameid_from_ua = geo_mapping_db.get(canonical_name.strip().lower().replace(" ","_"),None)
                        if geonameid_from_ua is not None:
                            kb_entity.properties["geonameid"] = geonameid_from_ua
        return resolved_kb
