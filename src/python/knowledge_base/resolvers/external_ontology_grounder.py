import sys, os
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from internal_ontology.internal_ontology import InternalOntology
from internal_ontology.db_interface import EntityDB
from internal_ontology.db_interface import EventDB
from elements.structured.structured_entity import EntityData
from elements.structured.structured_property import Property
from elements.structured.structured_events import Event
import datetime
import threading

class ExternalOntologyGrounder(KBResolver):
    def __init__(self):
        super(ExternalOntologyGrounder, self).__init__()

        self.use_probablist_grounding = False

    def get_event_text(self, kb_event_mention):
        event_text = kb_event_mention.triggering_phrase if kb_event_mention.triggering_phrase is not None else \
            kb_event_mention.trigger if kb_event_mention.trigger is not None else kb_event_mention.snippet[0]
        return event_text

    def resolve(self,
                kb,
                internal_ontology_dir,
                external_ontology_flag,
                n_best_types,
                entity_sqlite,
                clobber_entity_embeddings,
                event_sqlite,
                clobber_event_embeddings,
                n_best_ids):
        """

        :type kb: KnowledgeBase
        :param yaml_ontology_file:
        :param external_ontology_flag:
        :rtype: KnowledgeBase
        """
        print "ExternalOntologyGrounder RESOLVE"
        print(datetime.datetime.time(datetime.datetime.now()))

        n_best_types = int(n_best_types)
        n_best_ids = int(n_best_ids)
        resolved_kb = KnowledgeBase()
        super(ExternalOntologyGrounder, self).copy_all(resolved_kb, kb)

        script_dir = os.path.dirname(os.path.realpath(__file__))
        # internal_ontology_dir = os.path.join(script_dir, "..", "..", "..", "..", "ontology", "internal_ontology")
        event_ontology_file = os.path.join(internal_ontology_dir, "event_ontology.yaml")
        actor_ontology_file = os.path.join(internal_ontology_dir, "actor_ontology.yaml")
        structured_ontology_file = os.path.join(internal_ontology_dir, "structured_ontology.yaml")

        examples_json = os.path.join(internal_ontology_dir, "data_example_events.json")
        embeddings_file = "/nfs/raid87/u14/learnit_similarity_data/glove_6B_50d_embeddings/glove.6B.50d.p"
        lemma_file = os.path.join(internal_ontology_dir, "lemma.nv")
        stopword_file = os.path.join(internal_ontology_dir, "stopwords.list")

        print "ExternalOntologyGrounder LOAD ONTOLOGIES"
        event_ontology = InternalOntology(event_ontology_file,
                                          examples_json,
                                          embeddings_file,
                                          lemma_file,
                                          stopword_file)
        '''
        actor_ontology = InternalOntology(actor_ontology_file,
                                          examples_json,
                                          embeddings_file,
                                          lemma_file,
                                          stopword_file)
        '''

        structured_ontology = InternalOntology(structured_ontology_file,
                                               examples_json,
                                               embeddings_file,
                                               lemma_file,
                                               stopword_file,
                                               apply_transformation_indicator_names=True)

        print "ExternalOntologyGrounder DONE LOAD ONTOLOGIES"
        print(datetime.datetime.time(datetime.datetime.now()))

        #entity_db = EntityDB(
        #    entity_sqlite,
        #    actor_ontology,
        #    clobber=clobber_entity_embeddings=='clobber')
        #event_db = EventDB(event_sqlite, event_ontology, clobber=clobber_event_embeddings=='clobber')

        # TODO unstructured entities

        def ground_some_events(events, flag, chunk_id):
            print "ground some events, size: " + str(len(events))
            count = 0
            for e in events:
                count += 1
                if count % 500 == 0:
                    print count + chunk_id, datetime.datetime.now()
                for m in e.event_mentions:
                    if self.use_probablist_grounding:
                        ##################### grounding to events
                        event_groundings = event_ontology \
                            .ground_event_mention_to_external_ontology(
                                m, flag, 2)
                        m.external_ontology_sources = event_groundings

                        ### ################# grounding to indicators
                        event_text = self.get_event_text(m)
                        min_sim_threshold = 0.9
                        concept = structured_ontology.get_internal_class_from_type("Indicator")
                        sourced = structured_ontology._ground_type_func(concept, "HUME", event_text)
                        indicator_groundings = sorted(sourced.items(), key=lambda x: x[1], reverse=True)[:3]
                        m.external_ontology_sources.extend(indicator_groundings)
                        # print "indicator_groundings: " + str(indicator_groundings)
                        #for g in indicator_groundings:
                        #    type_internal = g[0][0]
                        #    type_external = g[0][1]
                        #    score = g[1]
                        #    if score > min_sim_threshold and type_external != "/indicator":
                        #        groundings_with_scores.append((type_external, score))
                    else:
                        event_groundings = event_ontology \
                            .grounding_event_mention_to_external_ontology_by_type_mapping(m, flag)
                        m.external_ontology_sources = event_groundings

            return None

        # USE THIS LINE TO NOT THREAD
        ground_some_events([evt for (eid, evt) in kb.get_events()],
                           external_ontology_flag,
                           0)


        # USE THIS CHUNK TO THREAD
        """
        all_events = [evt for (eid, evt) in kb.get_events()]
        step_size = len(all_events)/200
        threads = []
        for i in range(0, len(all_events), step_size):
            chunk = all_events[i:i + step_size]
            thread = threading.Thread(target=ground_some_events,
                                      args=(chunk, external_ontology_flag, i))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        """
        '''
        count = 0
        for event_id, event in kb.get_events():
            count += 1
            if count == 1:
                print 'Grounding unstructured events to type:'
            elif count % 500 == 0:
                print count, datetime.datetime.now()

            # TODO merge mentions' external sources for the whole event
            # use a method like self._resolve_type_of_unstructured_event()

            for event_mention in event.event_mentions:
                external_ontology_sources = \
                    event_ontology.ground_event_mention_to_external_ontology(
                        event_mention, external_ontology_flag)
                # TODO make all external_ontology_sources attributes dicts, not just this one
                event_mention.external_ontology_sources = {
                    # TODO when grounding IDs, use IO's source_map, and don't store the OntologyClass here in the first place
                    k: v for (_, k), v in external_ontology_sources
                }


            # TODO change serialization of events to use external sources!
            # in serializer it looks like:
            #     event_type = kb_event.event_type_to_confidence.keys()[0]

            # entities are taken care of
        '''

        '''
        # TODO add these objects in the appropriate places to the KnowledgeBase,
        # such that they are obtained with the calls above
        for structured_document in kb.structured_documents:
            for worksheet in structured_document.sheets:

                # Structured Entities
                for entity in worksheet.entities:
                    self._resolve_type_of_structured_entity(
                        entity, actor_ontology, external_ontology_flag,
                        n_best_types)
                    #self._resolve_entity_individual(
                    #    entity, entity_db, n_best_ids)

                # Structured Events:
                for event in worksheet.events:
                    # Entity
                    entity = event.location  # type: EntityData
                    self._resolve_type_of_structured_entity(
                        entity, actor_ontology, external_ontology_flag,
                        n_best_types)
                    #self._resolve_entity_individual(
                    #    entity, entity_db, n_best_ids)

                    #
                    for role, entity in event.actors.items():
                        pass  # TODO?

                    # Event TODO?
                    pass

                # as of 10/5 with current test set, the only entities are here
                for time_series in worksheet.time_series:

                    # Entities:
                    entity = time_series.location  # type: EntityData
                    self._resolve_type_of_structured_entity(
                        entity, actor_ontology, external_ontology_flag,
                        n_best_types)
                    #self._resolve_entity_individual(
                    #    entity, entity_db, n_best_ids)

                    # Properties:
                    reported_properties = [time_series.time_series_property]
                    reported_properties.extend([value.related_property for value
                                                in time_series.reported_values])
                    reported_properties = filter(lambda x: x is not None,
                                                 reported_properties)
                    for reported_prop in reported_properties:  # type: Property
                        reported_prop.external_ontology_sources = \
                            structured_ontology\
                            .ground_structured_property_to_external_ontology(
                                reported_prop,
                                external_ontology_flag,
                                n_best_types)
                        # TODO decide if we want to do this (1-best)
                        # update internal type for use in individual grounding
                        # prop.internal_ontology_class = prop.external_ontology_sources[0][0][0]

                        # ground indicators
                        indicator_label = \
                            event_ontology.transform_indicator_label(
                                reported_prop.property_label)
                        indicator = Event('dummy', 'Event', indicator_label)
                        indicator.internal_ontology_class = \
                            event_ontology.get_internal_class_of_event(
                                indicator)
                        reported_prop.event_hierarchy_grounding = \
                            event_ontology\
                            .ground_event_mention_to_external_ontology(
                                indicator, external_ontology_flag, n_best_types)

                        # tell us things!
                        self.print_structured_property_info(
                            reported_prop, event_ontology)
        '''

        print(datetime.datetime.time(datetime.datetime.now()))
        return resolved_kb

    @staticmethod
    def print_structured_property_info(prop, ontology):
        print '=== PROPERTY ==='
        print prop.property_id
        print prop.property_label
        for (internal_type, uri), score in prop.external_ontology_sources:
            print score, '\t', uri
        print '----------------'
        print ontology.transform_indicator_label(prop.property_label)
        for (internal_type, uri), score in prop.event_hierarchy_grounding:
            print score, '\t', uri
        print '================'

    @staticmethod
    def _resolve_type_of_structured_entity(
            entity, actor_ontology, external_ontology_flag, n_best):
        #print 'vvvv'
        #print entity.get_uri(), entity.entity_type, \
        #    entity.mar_entity_type
        #print '^^^^'
        entity.external_ontology_sources = actor_ontology \
            .ground_structured_entity_to_external_ontology(
                entity, external_ontology_flag, n_best)

        # TODO decide if we want to do this (1-best)
        # update internal type for use in individual grounding
        # entity.internal_ontology_class = entity.external_ontology_sources[0][0][0]

        print '==='
        print entity, entity.entity_id, entity.entity_type, entity.mar_entity_type
        print entity.label
        print entity.external_ontology_sources
        print '==='

    @staticmethod
    def _resolve_entity_individual(entity, database, n_best):

        entity_is_structured = isinstance(entity, EntityData)

        # TODO decide if we want the sieve approach rather than just grounding.
        # in previous iterations, we first tried to perform exact string match
        # against the database and only grounded upon failure.

        internal_types = [(internal_type, score) for (internal_type, _), score
                          in entity.external_ontology_sources]
        properties = entity.properties
        if entity_is_structured:  # structured
            mentions = [entity.label]
        else:
            mentions = [m.mention_text for m in entity.mentions]
            raise NotImplementedError("KBEntity objects aren't yet getting thei"
                                      "r internal_ontology_class attribute set")

        entity.grounded_individuals = database.ground_entity_to_individual(
            mentions, internal_types, properties, n_best)

        print '==='
        print entity.entity_id, entity.entity_type
        print entity.label
        print entity.grounded_individuals
        print '==='

        # TODO make this whole step optional!
        #
        # TODO add some thresholding so that bad IDs aren't kept here
        # if highest similarity is below some value, just use the internal
        # ontology's ID manager to create (keep?) ID not in DB
        threshold = 0.0  # TODO higher!
        best_type = entity.external_ontology_sources[0][0][0].class_name
        if entity.grounded_individuals[best_type][0][1] < threshold:
            return
        else:

            print 'Replacing id with best grounded ID:',

            if entity_is_structured:

                print entity.entity_id, '-->', entity.grounded_individuals[best_type][0][0]

                entity.entity_id = entity.grounded_individuals[best_type][0][0]
            else:

                print entity.id, '-->', entity.grounded_individuals[best_type][0][0]

                entity.id = entity.grounded_individuals[best_type][0][0]

