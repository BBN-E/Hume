import sys, os
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from internal_ontology.internal_ontology import InternalOntology
import datetime
import codecs, json

class EventGrounder(KBResolver):
    def __init__(self):
        super(EventGrounder, self).__init__()


    def resolve(self,
                kb,
                internal_ontology_dir,
                external_ontology_flag,
                n_best_types,
                output_cache_file):
        """

        :type kb: KnowledgeBase
        :param yaml_ontology_file:
        :param external_ontology_flag:
        :rtype: KnowledgeBase
        """
        print "EventGrounder RESOLVE"
        print(datetime.datetime.time(datetime.datetime.now()))

        n_best_types = int(n_best_types)
        resolved_kb = KnowledgeBase()
        super(EventGrounder, self).copy_all(resolved_kb, kb)

        script_dir = os.path.dirname(os.path.realpath(__file__))
        event_ontology_file = os.path.join(internal_ontology_dir, "event_ontology.yaml")

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

        print "EventGrounder DONE LOAD ONTOLOGIES"
        print(datetime.datetime.time(datetime.datetime.now()))

        grounding_cache = dict()
        o = codecs.open(output_cache_file, 'w', encoding='utf8')

        def ground_some_events(events, flag, chunk_id):
            print "ground some events, size: " + str(len(events))
            count = 0
            for e in events:
                count += 1
                if count % 500 == 0:
                    print count + chunk_id, datetime.datetime.now()
                for m in e.event_mentions:

                    event_groundings_det = event_ontology.grounding_event_mention_to_external_ontology_by_deterministic_mapping(m, flag)

                    print("event_groundings_det: " + str(event_groundings_det))

                    event_groundings_soft = event_ontology.ground_event_mention_to_external_ontology_by_similarity(m, flag, n_best_types)

                    print("event_groundings_soft: " + str(event_groundings_soft))

                    cache_key, type_and_confidences = event_groundings_soft
                    values = []
                    for type_and_confidence in type_and_confidences:
                        type = type_and_confidence[0]
                        confidence = type_and_confidence[1]
                        values.append(type_and_confidence)

                        print "grounding: " + str(cache_key) + "\t->\t" + str(confidence) + "\t" + str(type)
                    grounding_cache[cache_key] = values

            return None

        # USE THIS LINE TO NOT THREAD
        ground_some_events([evt for (eid, evt) in kb.get_events()],
                           external_ontology_flag,
                           0)

        o.write(json.dumps(grounding_cache, sort_keys=True, indent=4, ensure_ascii=False))
        o.close()

        print(datetime.datetime.time(datetime.datetime.now()))
        return resolved_kb