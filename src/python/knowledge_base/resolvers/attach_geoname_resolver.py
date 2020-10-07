import codecs

from resolvers.kb_resolver import KBResolver
from knowledge_base import KnowledgeBase


class AttachGeoNameResolver(KBResolver):
    def __init__(self):
        super(AttachGeoNameResolver,self).__init__()

    def resolve(self, kb, geoname_with_gdam_woredas_path):
        print("AttachGeoNameResolver RESOLVE")
        resolved_kb = KnowledgeBase()
        super(AttachGeoNameResolver, self).copy_all(resolved_kb, kb)

        geo_mapping_db = dict()
        with codecs.open(geoname_with_gdam_woredas_path, 'r', encoding="utf-8") as fp:
            for i in fp:
                i = i.strip()
                name, geoname_id = i.split("\t")
                geo_mapping_db[name] = geoname_id
        for entid,kb_entity in resolved_kb.entid_to_kb_entity.items():
            for entity_type in kb_entity.entity_type_to_confidence.keys():
                entity_type = str(entity_type.split(".")[0])
                if entity_type in {"GPE", "LOC"}:
                    canonical_name = kb_entity.canonical_name
                    if canonical_name is not None:
                        geonameid_from_geonames_and_woredas = geo_mapping_db.get(canonical_name, None)
                        if geonameid_from_geonames_and_woredas is not None:
                            kb_entity.properties["geonameid"] = geonameid_from_geonames_and_woredas
        return resolved_kb
