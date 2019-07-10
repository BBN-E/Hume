# Takes a KB with event mentions that have been grounded to 
# an external ontology and outputs a mapping from 
# (event_type, trigger) to external ontology URL. 
# The mapping can be read in by the 
# ExternalOntologyCacheGrounder to quickly attach that 
# grounding information to an event mention in another
# KB (probably made from the same documents as this runs on). 
# 
# The point is that this serializer can be run in parallel, 
# while the ExternalOntologyGrounderByCache can be quickly
# run not in parallel.

from knowledge_base import KnowledgeBase
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from internal_ontology.internal_ontology import InternalOntology
import codecs, json


class ExternalOntologyCacheSerializer:

    def __init__(self):
        pass

    def serialize(self, kb, output_cache_file):
        print "ExternalOntologyCacheSerializer SERIALIZE"
        o = codecs.open(output_cache_file, 'w', encoding='utf8')

        grounding_cache = dict()

        for event_id, event in kb.get_events():
            for event_mention in event.event_mentions:
                # Create cache key
                key = InternalOntology.get_cache_key(event_mention)

                eos = event_mention.external_ontology_sources
                if eos is None or len(eos) == 0:
                    continue

                values = []
                for eos_entry in eos:
                    node_id = eos_entry[0][0].id  # best_match[0][0] is an OntologyClass object
                    grounded_type = eos_entry[0][1]
                    score = eos_entry[1]

                    print "grounding: " + str(key) + "\t->\t" + str(score) + "\t" + str(node_id) + "\t" + str(grounded_type)

                    # best_match = eos[0]
                
                    # create cache value
                    # node_id = eos_entry[0][0].id # best_match[0][0] is an OntologyClass object
                    # grounded_type = eos_entry[0][1]
                    # score = eos_entry[1]
                    value = (node_id, grounded_type, score,)
                    values.append(value)
                
                grounding_cache[key] = values
                
        o.write(json.dumps(grounding_cache, sort_keys=True, indent=4, ensure_ascii=False))

        o.close()

