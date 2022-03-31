import os
import sys
import logging

from knowledge_base import KnowledgeBase

from readers.causal_relation_reader import CausalRelationReader
from readers.fact_reader import FactReader
from readers.serifxml_reader import SerifXMLReader
from readers.special_text_reader import SpecialTextReader

from resolvers.additional_entity_type_resolver import AdditionalEntityTypeResolver
from resolvers.attach_geoname_resolver import AttachGeoNameResolver
from resolvers.bad_relation_resolver import BadRelationResolver
from resolvers.confidence_resolver import ConfidenceResolver
from resolvers.country_code_property_resolver import CountryCodePropertyResolver
from resolvers.do_nothing_resolver import DoNothingResolver
from resolvers.entity_add_properties_resolver import EntityAddPropertyResolver
from resolvers.entity_group_entity_type_resolver import EntityGroupEntityTypeResolver
from resolvers.event_direction_resolver import EventDirectionResolver
from resolvers.event_polarity_resolver import EventPolarityResolver
from resolvers.event_removal_resolver import EventRemovalResolver
from resolvers.event_type_change_resolver import EventTypeChangeResolver
from resolvers.external_uri_resolver import ExternalURIResolver
from resolvers.factor_event_generic_genericity_resolver import FactorEventGenericGenericityResolver
from resolvers.kb_unification_resolver import KbUnificationResolver
from resolvers.mention_numeric_resolver import EntityMentionNumericResolver
from resolvers.precision_resolver import PrecisionResolver
from resolvers.premod_precision_resolver import PremodPrecisionResolver
from resolvers.redundant_event_resolver import RedundantEventResolver
from resolvers.redundant_relation_resolver import RedundantRelationResolver
from resolvers.removal_by_type_resolver import RemovalByTypeResolver
from resolvers.relevant_kb_entity_mention_resolver import RelevantKBEntityMentionResolver
from resolvers.add_generic_event_type_if_only_causal_factor_type_available import AddGenericEventTypeIfOnlyCausalFactorTypeAvailableResolver
from resolvers.additional_affiliation_resolver import AdditionalAffiliationResolver
from resolvers.factor_relation_trend_resolver import FactorRelationTrendResolver
from resolvers.drop_negative_polarity_causal_assertion_resolver import DropNegativePolarityCausalAssertionResolver
from resolvers.event_location_resolver import EventLocationResolver
from resolvers.event_event_relation_renaming_resolver import EventEventRelationRenamingResolver
from resolvers.event_location_resolver_no_entity_linking import EventLocationResolverNoEntityLinking

from serializers.event_tsv_serializer import EventTSVSerializer
from serializers.json_serializer import JSONSerializer
from serializers.jsonld_serializer import JSONLDSerializer
from serializers.pickle_serializer import KBPickleSerializer
from serializers.relation_tsv_serializer import RelationTSVSerializer
from serializers.wm_tabular_format_serializer import WMTabularFormatSerializer
from serializers.event_location_time_serializer import EventLocationTimeSerializer
from serializers.unification_serializer import UnificationSerializer
from serializers.visualization_serializer import VisualizationSerializer
from serializers.rdf_serializer import RDFSerializer
from serializers.fillable_tcag_serializer import FillableTCAGSerializer

class KBConstructor:
    
    def __init__(self, config_file):
        # self.paramters maps component(reader, resolver, seralizer)
        # to parameter list for that component
        self.readers, self.resolvers, self.serializers, self.parameters \
            = self.read_config_file(config_file)
        
    def construct(self):
        kb = KnowledgeBase()
        for reader in self.readers:
            if reader not in self.parameters:
                reader.read(kb)
            else:
                reader.read(kb, *(self.parameters[reader]))
        return kb

    def resolve(self, kb):
        new_kb = kb
        for resolver in self.resolvers:
            if resolver not in self.parameters:
                new_kb = resolver.resolve(new_kb)
            else:
                new_kb = resolver.resolve(new_kb, *(self.parameters[resolver]))
        return new_kb
    
    def serialize(self, kb):
        for serializer in self.serializers:
            serializer.serialize(kb, *(self.parameters[serializer]))
        
    def read_config_file(self, config_file):
        readers = []
        resolvers = []
        serializers = []
        
        parameters = dict() # maps component to parameter list
        
        c = open(config_file)
        current_component = None
        for line in c:
            line = line.strip()
            if len(line) == 0 or line.startswith('#'):
                continue

            if line.startswith("READER"):
                try:
                    component_name = line.split()[1]
                    current_component = getattr(sys.modules[__name__], component_name)()
                    readers.append(current_component)
                except AttributeError:
                    print("Unknown READER: " + component_name)
                    sys.exit(1)
                    
            elif line.startswith("RESOLVER"):
                try:
                    component_name = line.split()[1]
                    current_component = getattr(sys.modules[__name__], component_name)()
                    resolvers.append(current_component)
                except AttributeError as e:
                    print("Unknown RESOLVER: " + component_name)
                    sys.exit(1)
                    
            elif line.startswith("SERIALIZER"):
                try:
                    component_name = line.split()[1]
                    current_component = getattr(sys.modules[__name__], component_name)()
                    serializers.append(current_component)
                except AttributeError:
                    print("Unknown SERIALIZER: " + component_name)
                    sys.exit(1)
            
            else:
                # Parameter line
                if current_component not in parameters:
                    parameters[current_component] = []
                parameters[current_component].append(line)

        return readers, resolvers, serializers, parameters

if __name__ == "__main__":
    log_format = '[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s - %(message)s'
    try:
        logging.basicConfig(level=logging.getLevelName(os.environ.get('LOGLEVEL', 'WARNING').upper()),format=log_format)
    except ValueError as e:
        logging.error("Unparseable level {}, will use default {}.".format(os.environ.get('LOGLEVEL', 'WARNING').upper(),
                                                                          logging.root.level))
        logging.basicConfig(format=log_format)
    if len(sys.argv) != 2:
        print("Usage: python " + os.path.basename(sys.argv[0]) + " config_file")
        sys.exit(1)

    config_file = sys.argv[1]

    kbc = KBConstructor(config_file)

    kb = kbc.construct()
    kb = kbc.resolve(kb)
    kbc.serialize(kb)
    


