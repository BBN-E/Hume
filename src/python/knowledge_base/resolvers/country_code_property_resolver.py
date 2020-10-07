import sys, os, re, codecs
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver

class CountryCodePropertyResolver(KBResolver):
    
    reliable_link_confidences = {"AnyName", "AmbiguousName", "TitleDesc", "CopulaDesc", "ApposDesc", "OnlyOneCandidateDesc", "WhqLinkPron", "DoubleSubjectPersonPron", "OnlyOneCandidatePron"}

    def __init__(self):
        # canonical name to country code
        self.country_codes = dict() 
        # country code to ethnicity, we do want the code to 
        # be the key here, because later we calculate the most 
        # common country code, and only want to assign ethnicity
        # if the most common code has a related ethnicity 
        self.ethnicities = dict() 
        # ISO country code (from AWAKE DB) to cameo country code
        self.iso_country_codes = dict()
        
        country_code_and_ethnicity_re = re.compile(r"^(.*?)([A-Z]{3}) (\w+)\s*$")
        country_code_re = re.compile(r"^(.*?)([A-Z]{3})$")

        script_dir = os.path.dirname(os.path.realpath(__file__))
        country_code_file = os.path.join(script_dir, "..", "data_files", "country_codes.txt")
        cc = codecs.open(country_code_file, 'r', encoding='utf8')
        for line in cc:
            line = line.strip()
            m = country_code_and_ethnicity_re.match(line)
            if m is not None:
                self.country_codes[m.group(1).strip()] = m.group(2)
                self.ethnicities[m.group(2).strip()] = m.group(3)
                continue

            m = country_code_re.match(line)
            if m is not None:
                self.country_codes[m.group(1).strip()] = m.group(2)
                continue
        cc.close()
        
        iso_code_to_cameo_file = os.path.join(script_dir, "..", "data_files", "awake_iso_country_code_to_cameo.txt")
        iso = codecs.open(iso_code_to_cameo_file, 'r', encoding='utf8')
        for line in iso:
            line = line.strip()
            pieces = line.split()
            self.iso_country_codes[pieces[0]] = pieces[1]
        iso.close()
        
    def resolve(self, kb):
        print("CountryCodeResolver RESOLVE")
        resolved_kb = KnowledgeBase()

        super(CountryCodePropertyResolver, self).copy_all(resolved_kb, kb)

        for entgroupid, kb_entity_group in resolved_kb.get_entity_groups():
            # Awake ISO code for geoname's country to cameo_code for geoname's country
            # This is for when the KB entity group is a city/geoname
            if ("country_iso_code" in kb_entity_group.properties and 
                kb_entity_group.properties["country_iso_code"] in self.iso_country_codes):
                geonames_country_code = self.iso_country_codes[kb_entity_group.properties["country_iso_code"]]
                kb_entity_group.properties["geonames_country_code"] = geonames_country_code 

        for entid, kb_entity in resolved_kb.entid_to_kb_entity.items():
            # cameo_country_code properties for GPE kb_entity
            # This is for when the KB entity is a country
            cameo_country_code = self.country_codes.get(kb_entity.canonical_name)
            if cameo_country_code is not None:
                kb_entity.properties["cameo_country_code"] = cameo_country_code

        # Reliable (entity, country_code) pairs
        reliable_country_codes = set()

        # citizenship_cameo_country_code property for PER kb_entity
        kb_entity_to_country_code_count = dict()
        for relid, kb_relation in resolved_kb.relid_to_kb_relation.items():
            if kb_relation.relation_type != "GEN-AFF.Citizen-Resident-Religion-Ethnicity":
                continue

            left_id = kb_relation.left_argument_id
            right_id = kb_relation.right_argument_id

            left_entity = resolved_kb.entid_to_kb_entity[left_id]
            right_entity = resolved_kb.entid_to_kb_entity[right_id]
            
            if "PER.Individual" not in left_entity.entity_type_to_confidence and "PER.Group" not in left_entity.entity_type_to_confidence:
                continue
            if "GPE.Nation" not in right_entity.entity_type_to_confidence:
                continue
            
            country_code = self.country_codes.get(right_entity.canonical_name)
            if country_code is None:
                continue

            if left_entity not in kb_entity_to_country_code_count:
                kb_entity_to_country_code_count[left_entity] = dict()
            if country_code not in kb_entity_to_country_code_count[left_entity]:
                kb_entity_to_country_code_count[left_entity][country_code] = 0
            kb_entity_to_country_code_count[left_entity][country_code] += 1

            # Record (entity, country_code) pair if relation is reliable on its own
            for relmention in kb_relation.relation_mentions:
                mention = relmention.left_mention
                if mention.link_confidence in CountryCodePropertyResolver.reliable_link_confidences:
                    reliable_country_codes.add((left_entity, country_code,))
            
        # Take most common country_code in dictionary
        for kb_entity, country_code_count in kb_entity_to_country_code_count.items():
            most_common_country_code = None
            most_common_country_code_count = 0
            for country_code, count in country_code_count.items():
                if count > most_common_country_code_count:
                    most_common_country_code = country_code
                    most_common_country_code_count = count
                elif (count == most_common_country_code_count and 
                      country_code < most_common_country_code):
                    most_common_country_code = country_code
                    most_common_country_code_count = count
            
            # If it's a named entity, require reliable match
            if kb_entity.canonical_name is not None and (kb_entity, most_common_country_code,) not in reliable_country_codes:
                #print "Excluding: " + kb_entity.id + " from having country code: " + most_common_country_code
                continue

            kb_entity.properties["citizenship_cameo_country_code"] = most_common_country_code
            if most_common_country_code in self.ethnicities:
                kb_entity.properties["ethnicity"] = self.ethnicities[most_common_country_code]

        return resolved_kb

    
