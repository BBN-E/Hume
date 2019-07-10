# Takes cached external grounding information (from
# ExternalOntologyCacheSerializer) and adds it to KB

import sys, os, codecs, json
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from internal_ontology.internal_ontology import InternalOntology
from rdflib import Graph, URIRef, RDFS, Literal
import datetime


class EventCacheLookupGrounder(KBResolver):
    def __init__(self):
        pass

    def resolve(self, kb, grounding_cache_directory):
        print "EventCacheLookupGrounder RESOLVE"

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
                grounding_candidate = InternalOntology.get_grounding_candidate(event_mention)
                key = InternalOntology.get_cache_key(grounding_candidate)
                print "event_mention key: " + str(key)

                if key not in grounding_cache:
                    print "Warning: couldn't ground event mention id: " + event_mention.id
                    continue

                event_mention.external_ontology_sources = []

                values = grounding_cache[key]
                for value in values:
                    grounded_type = value[0]
                    score = value[1]

                    print "event_mention grounding: " + grounded_type + "\t" + str(score)

                    event_mention.external_ontology_sources.append([URIRef(grounded_type), score])

        return kb
