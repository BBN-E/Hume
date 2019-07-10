from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention
from unification_provenance import UnificationProvenance
from unification_element import UnificationElement
from unification_span import UnificationSpan

class UnificationEntity(UnificationElement):
    entity_type_map = { "PER": "http://ontology.causeex.com/ontology/odps/Actor#Person",
                        "ORG": "http://ontology.causeex.com/ontology/odps/Actor#Organization",
                        "LOC": "http://ontology.causeex.com/ontology/odps/GeneralConcepts#PhysicalLocation",
                        "FAC": "http://www.ontologyrepository.com/CommonCoreOntologies/Facility",
                        "GPE": "http://ontology.causeex.com/ontology/odps/Actor#GeopoliticalEntity",
                        "VEH": "http://ontology.causeex.com/ontology/odps/GeneralConcepts#Vehicle",
                        "WEA": "http://ontology.causeex.com/ontology/odps/CommonCoreOntologies#Weapon",
                        "ART": "http://ontology.causeex.com/ontology/odps/CommonCoreOntologies#Artifact" }
    
    def __init__(self, kb_mention, kb):
        # Currently, only KBMention is passed in and this code assumes 
        # we don't have a KBValueMention here
        
        kb_entity_id = kb.kb_mention_to_entid[kb_mention]
        kb_entity = kb.entid_to_kb_entity[kb_entity_id]
        
        if kb_entity.canonical_name:
            self.canonical_label = kb_entity.canonical_name

        self.entity_types = self.get_entity_types(kb_mention, kb)
        
        # default is NOM
        self.mention_type = "http://ontology.causeex.com/ontology/odps/DataProvenance#NOM"
        if isinstance(kb_mention, KBMention):
            if kb_mention.mention_type == "name":
                self.mention_type = "http://ontology.causeex.com/ontology/odps/DataProvenance#NAM"
            if kb_mention.mention_type == "pron":
                self.mention_type = "http://ontology.causeex.com/ontology/odps/DataProvenance#PRO"
        
        self.evidence = dict()
        self.evidence["span"] = UnificationSpan(kb_mention.document, kb_mention.start_char, kb_mention.end_char, kb_mention.mention_text)
        self.evidence["head_span"] = UnificationSpan(kb_mention.document, kb_mention.head_start_char, kb_mention.head_end_char, kb_mention.mention_head_text)

        self.properties = dict() 
        if "geonameid" in kb_entity.properties:
            self.properties["geonames_id"] = int(kb_entity.properties["geonameid"])
        if "latitude" in kb_entity.properties:
            self.properties["latitude"] = float(kb_entity.properties["latitude"])
        if "longitude" in kb_entity.properties:
            self.properties["longitude"] = float(kb_entity.properties["longitude"])
        if "cameo_country_code" in kb_entity.properties:
            self.properties["cameo_country_code"] = kb_entity.properties["cameo_country_code"]
        if "external_uri" in kb_entity.properties:
            self.properties["external_uri"] = kb_entity.properties["external_uri"]

        self.provenance = UnificationProvenance()
        
    def is_duplicate_of(self, other):
        for entity_type in other.entity_types.keys():
            if entity_type not in self.entity_types:
                return False

        spans_match = self.evidence["span"].is_duplicate_of(other.evidence["span"]) and self.evidence["head_span"].is_duplicate_of(other.evidence["head_span"]) 

        return spans_match
    
    # TODO something smarter here -- can we store the entity type grounding on 
    # the KBEntity or KBMention/KBValueMention?
    def get_entity_types(self, kb_mention_or_value_mention, kb):
        if isinstance(kb_mention_or_value_mention, KBMention):
            return self.get_entity_types_for_mention(kb_mention_or_value_mention, kb)
        if isinstance(kb_mention_or_value_mention, KBValueMention):
            return self.get_entity_types_for_value_mention(kb_mention_or_value_mention)
       
        return None

    def get_entity_types_for_mention(self, kb_mention, kb):
        results = dict()
        kb_entity_id = kb.kb_mention_to_entid[kb_mention]
        kb_entity = kb.entid_to_kb_entity[kb_entity_id]
        bbn_entity_type = kb_entity.get_best_entity_type()
        ace_type = bbn_entity_type[0:bbn_entity_type.find(".")]
        causeex_type = UnificationEntity.entity_type_map[ace_type]
        results[causeex_type] = 1.0
        return results

    def get_entity_types_for_value_mention(self, kb_value_mention, kb):
        return results

    
