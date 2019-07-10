# Takes cached external grounding information (from
# ExternalOntologyCacheSerializer) and adds it to KB

import sys, os, codecs, json
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from internal_ontology.internal_ontology import InternalOntology
import datetime

class ExternalOntologyCacheGrounder(KBResolver):

    def __init__(self):
        pass

    def resolve(self, kb, internal_ontology_dir, grounding_cache_directory):
        print "ExternalOntologyCacheGrounder RESOLVE"

        script_dir = os.path.dirname(os.path.realpath(__file__))
        # internal_ontology_dir = os.path.join(script_dir, "..", "..", "..", "..", "ontology", "internal_ontology")
        event_ontology_file = os.path.join(internal_ontology_dir, "event_ontology.yaml")
        examples_json = os.path.join(internal_ontology_dir, "data_example_events.json")
        embeddings_file = "/nfs/raid87/u14/learnit_similarity_data/glove_6B_50d_embeddings/glove.6B.50d.p"
        lemma_file = os.path.join(internal_ontology_dir, "lemma.nv")
        stopword_file = os.path.join(internal_ontology_dir, "stopwords.list")

        structured_ontology_file = os.path.join(internal_ontology_dir, "structured_ontology.yaml")

        print "ExternalOntologyCacheGrounder LOAD ONTOLOGY"
        event_ontology = InternalOntology(event_ontology_file,
                                          examples_json,
                                          embeddings_file,
                                          lemma_file,
                                          stopword_file)

        structured_ontology = InternalOntology(structured_ontology_file,
                                               examples_json,
                                               embeddings_file,
                                               lemma_file,
                                               stopword_file,
                                               apply_transformation_indicator_names=True)

        print  "ExternalOntologyCacheGrounder DONE LOAD ONTOLOGY"
        print(datetime.datetime.time(datetime.datetime.now()))

        
        grounding_cache = dict()
        for filename in os.listdir(grounding_cache_directory):
            filepath = os.path.join(grounding_cache_directory, filename)
            i = codecs.open(filepath, 'r', encoding='utf8')
            contents = i.read()
            i.close()

            json_obj = json.loads(contents)
            for key, value in json_obj.iteritems():
                grounding_cache[key] = value

        count = 0
        for event_id, event in kb.get_events():
            
            if count % 10000 == 0:
                print str(count)
            count += 1
            for event_mention in event.event_mentions:
                print "event_mention: " + str(event_mention)
                key = InternalOntology.get_cache_key(event_mention)
                print "event_mention key: " + str(key)
                
                if key not in grounding_cache:
                    print "Warning: couldn't ground event mention id: " + event_mention.id
                    event_mention.external_ontology_sources = [ [ [ "/event", "/event" ], 0.3 ] ]
                    continue

                values = grounding_cache[key]
                for value in values:
                    node_id = value[0]
                    grounded_type = event_ontology.call_uri_ref(value[1])
                    score = value[2]

                    print "event_mention grounding: " + str(node_id) + "\t" + grounded_type + "\t" + str(score)

                    # Is there a better way than this to go from ID to node in the ontology?
                    type_from_id = node_id
                    if type_from_id in event_ontology.type_text_to_class_name:
                        type_from_id = event_ontology.type_text_to_class_name[type_from_id]
                        #if type_from_id.endswith("_001"):
                        #    type_from_id = type_from_id[0:-4]
                        internal_ontology_class = event_ontology.get_internal_class_from_type(type_from_id)
                    elif type_from_id in structured_ontology.type_text_to_class_name:
                        type_from_id = structured_ontology.type_text_to_class_name[type_from_id]
                        #if type_from_id.endswith("_001"):
                        #    type_from_id = type_from_id[0:-4]
                        internal_ontology_class = structured_ontology.get_internal_class_from_type(type_from_id)
                
                event_mention.external_ontology_sources = [ [ [ internal_ontology_class, grounded_type ], score ] ]
                
        return kb
