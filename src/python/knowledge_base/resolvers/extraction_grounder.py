import sys, os
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from internal_ontology.internal_ontology import InternalOntology
from elements.structured.structured_entity import EntityData
from elements.structured.structured_events import Event
from elements.structured.structured_time_series import TimeSeries
from elements.structured.structured_reported_value import ReportedValue
from elements.structured.structured_property import Property
import datetime

class ExtractionGrounder(KBResolver):
    
    def __init__(self):
        pass
    
    def resolve(self, kb, internal_ontology_dir):
        print "ExtractionGrounder RESOLVE"
                
        resolved_kb = KnowledgeBase()
        super(ExtractionGrounder, self).copy_all(resolved_kb, kb)
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        # internal_ontology_dir = os.path.join(script_dir, "..", "..", "..", "..", "ontology", "internal_ontology")
        event_ontology_file = os.path.join(internal_ontology_dir, "event_ontology.yaml")
        actor_ontology_file = os.path.join(internal_ontology_dir, "actor_ontology.yaml")
        structured_ontology_file = os.path.join(internal_ontology_dir, "structured_ontology.yaml")

        examples_json = os.path.join(internal_ontology_dir, "data_example_events.json")
        embeddings_file = "/nfs/raid87/u14/learnit_similarity_data/glove_6B_50d_embeddings/glove.6B.50d.p"
        lemma_file = os.path.join(internal_ontology_dir, "lemma.nv")
        stopword_file = os.path.join(internal_ontology_dir, "stopwords.list")
        print "ExtractionGrounder LOAD ONTOLOGIES"
        event_ontology = InternalOntology(event_ontology_file,
                                          examples_json,
                                          embeddings_file,
                                          lemma_file,
                                          stopword_file)
#        actor_ontology = InternalOntology(actor_ontology_file,
#                                          examples_json,
#                                          embeddings_file,
#                                          lemma_file,
#                                          stopword_file)

        print "ExtractionGrounder DONE LOAD ONTOLOGIES"
        print(datetime.datetime.time(datetime.datetime.now()))

        # set internal ontology type for each unstructured event mention
        count = 0
        for event_id, event in kb.get_events():
            count += 1
            if count == 1:
                print 'Setting internal ontology types for unstructured events'
            if count % 500 == 0:
                print count, '...\n',
            for event_mention in event.event_mentions:
                event_mention.internal_ontology_class = \
                    event_ontology.get_internal_class_of_event(event_mention)
        print

        # TODO add these objects in the appropriate places to the KnowledgeBase
        # such that they are obtained with the calls above

        '''
        for structured_document in kb.structured_documents:
            for worksheet in structured_document.sheets:

                # structured entities:

                # none in M12 as of 10/11 TODO check after 10/12 release
                for entity in worksheet.entities:
                    pass  # TODO

                # none in M12 as of 10/11 TODO check after 10/12 release
                for event in worksheet.events:
                    for role, entity in event.actors.items():
                        pass  # TODO
                    
                    location = event.event_location
                    location.internal_ontology_class = actor_ontology \
                        .get_internal_class_of_structured_entity(location)

                for time_series in worksheet.time_series:  # type: TimeSeries

                    # Entities:
                    location = time_series.location  # type: EntityData
                    location.internal_ontology_class = actor_ontology \
                        .get_internal_class_of_structured_entity(location)

                    # Properties:
                    reported_properties = [time_series.time_series_property]
                    reported_properties.extend([value.related_property for value
                                                in time_series.reported_values])
                    reported_properties = filter(lambda x: x is not None,
                                                 reported_properties)
                    for property in reported_properties:  # type: Property
                        # assume provided class is useful
                        property.internal_ontology_class = structured_ontology \
                            .get_internal_class_of_property(property.property_type)

        # structured factors in causal assertions:
        # TODO no processing needs to occur here for TYPE grounding properties
        # TODO factors' types are uniformly CE:MeasurementFactor, which is fine
        for structured_relationship in kb.structured_relationships:
            pass  # TODO?
        '''

        return resolved_kb
