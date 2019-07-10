import sys, os, codecs

from knowledge_base import KnowledgeBase

from readers.serifxml_reader import SerifXMLReader
from readers.fact_reader import FactReader
from readers.generic_event_reader import GenericEventReader
from readers.causal_relation_reader import CausalRelationReader
from readers.structured_data_reader import StructuredDataReader

from resolvers.do_nothing_resolver import DoNothingResolver
from resolvers.country_code_property_resolver import CountryCodePropertyResolver
from resolvers.factor_event_generic_genericity_resolver import FactorEventGenericGenericityResolver
from resolvers.entity_add_properties_resolver import EntityAddPropertyResolver
from resolvers.kb_unification_resolver import KbUnificationResolver
from resolvers.redundant_relation_resolver import RedundantRelationResolver
from resolvers.redundant_event_resolver import RedundantEventResolver
from resolvers.event_removal_resolver import EventRemovalResolver
from resolvers.precision_resolver import PrecisionResolver
from resolvers.confidence_resolver import ConfidenceResolver
from resolvers.removal_by_type_resolver import RemovalByTypeResolver
from resolvers.additional_entity_type_resolver import AdditionalEntityTypeResolver
from resolvers.event_direction_resolver import EventDirectionResolver
from resolvers.bad_relation_resolver import BadRelationResolver
from resolvers.extraction_grounder import ExtractionGrounder
from resolvers.external_ontology_grounder import ExternalOntologyGrounder
from resolvers.event_uploader import EventUploader
from resolvers.structured_resolver import StructuredResolver
from resolvers.external_ontology_cache_grounder import ExternalOntologyCacheGrounder
from resolvers.event_type_change_resolver import EventTypeChangeResolver
from resolvers.entity_group_entity_type_resolver import EntityGroupEntityTypeResolver
from resolvers.event_cache_lookup_grounder import EventCacheLookupGrounder
from resolvers.event_grounder import EventGrounder
from resolvers.external_uri_resolver import ExternalURIResolver
from resolvers.external_event_uri_resolver import ExternalEventURIResolver
from resolvers.attach_geoname_resolver import AttachGeoNameResolver
from resolvers.mention_numeric_resolver import EntityMentionNumericResolver

from serializers.json_serializer import JSONSerializer
from serializers.pickle_serializer import KBPickleSerializer
from serializers.jsonld_serializer import JSONLDSerializer
from serializers.visualization_serializer import VisualizationSerializer
from serializers.wm_tabular_format_serializer import WMTabularFormatSerializer
from serializers.relation_tsv_serializer import RelationTSVSerializer
from serializers.event_tsv_serializer import EventTSVSerializer
from serializers.rdf_serializer import RDFSerializer
from serializers.external_ontology_cache_serializer import ExternalOntologyCacheSerializer
from serializers.unification_serializer import UnificationSerializer

class KBConstructor:
    
    def __init__(self, config_file):
        # self.paramters maps component(reader, resolver, seralizer)
        # to parameter list for that component
        self.readers, self.resolvers, self.serializers, self.parameters \
            = self.read_config_file(config_file)
        
    def construct(self):
        kb = KnowledgeBase()
        for reader in self.readers:
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
                    print "Unknown READER: " + component_name
                    sys.exit(1)
                    
            elif line.startswith("RESOLVER"):
                try:
                    component_name = line.split()[1]
                    current_component = getattr(sys.modules[__name__], component_name)()
                    resolvers.append(current_component)
                except AttributeError as e:
                    print "Unknown RESOLVER: " + component_name
                    sys.exit(1)
                    
            elif line.startswith("SERIALIZER"):
                try:
                    component_name = line.split()[1]
                    current_component = getattr(sys.modules[__name__], component_name)()
                    serializers.append(current_component)
                except AttributeError:
                    print "Unknown SERIALIZER: " + component_name
                    sys.exit(1)
            
            else:
                # Parameter line
                if current_component not in parameters:
                    parameters[current_component] = []
                parameters[current_component].append(line)

        return readers, resolvers, serializers, parameters

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: python " + os.path.basename(sys.argv[0]) + " config_file"
        sys.exit(1)

    config_file = sys.argv[1]

    kbc = KBConstructor(config_file)

    kb = kbc.construct()
    kb = kbc.resolve(kb)
    kbc.serialize(kb)
    


