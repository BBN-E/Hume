from collections import defaultdict

from elements.kb_element import KBElement


class KBEvent(KBElement):
    
    def __init__(self, id, event_type):
        self.id = id
        # self.event_type_to_confidence = { event_type : 0.5 }
        self.event_mentions = []
        self.properties = dict()
        self.arguments = dict()


        # self.confidence = 0

    def add_event_mention(self, kb_event_mention):
        # self.confidence = (self.confidence * len(self.event_mentions) + kb_event_mention.confidence)/(len(self.event_mentions) +1)
        self.event_mentions.append(kb_event_mention)

    def add_argument(self, role, entity_or_valuemention):
        self.arguments.setdefault(role,list()).append(entity_or_valuemention)

    def get_document(self):
        # in-doc event
        return self.event_mentions[0].document

    @property
    def confidence(self):
        return list(self.event_type_to_confidence.values())[0]

    @property
    def event_type_to_confidence(self):
        ret = dict()
        if len(self.event_mentions[0].external_ontology_sources) > 0:
            ret[self.event_mentions[0].external_ontology_sources[0][0]] = self.event_mentions[0].external_ontology_sources[0][1]
        else:
            ret[self.event_mentions[0].causal_factors[0].factor_class] = self.event_mentions[0].causal_factors[0].relevance
        return ret