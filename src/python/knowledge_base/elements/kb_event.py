from collections import defaultdict
from kb_element import KBElement

class KBEvent(KBElement):
    
    def __init__(self, id, event_type):
        self.id = id
        self.event_type_to_confidence = { event_type : 0.5 }
        self.event_mentions = []
        self.properties = dict()
        self.arguments = defaultdict(list)
        self.confidence = 0

    def add_event_mention(self, kb_event_mention):
        self.confidence = (self.confidence * len(self.event_mentions) + kb_event_mention.confidence)/(len(self.event_mentions) +1)
        self.event_mentions.append(kb_event_mention)

    def add_argument(self, role, entity_or_valuemention):
        self.arguments[role].append(entity_or_valuemention)

    def get_document(self):
        # in-doc event
        return self.event_mentions[0].document