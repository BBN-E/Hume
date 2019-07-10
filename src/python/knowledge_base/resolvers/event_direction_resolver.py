from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from shared_id_manager.shared_id_manager import SharedIDManager
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention

import sys, os, codecs
from string import punctuation

# take direction_of_change property on KBEventMention and 
# create new event for it

class EventDirectionResolver(KBResolver):
    
    event_type_to_grounded_type = \
        { "Increase": "http://ontology.causeex.com/ontology/odps/Event#Increase",
          "Decrease": "http://ontology.causeex.com/ontology/odps/Event#Decrease"
        }

    def __init__(self):
        pass

    def resolve(self, kb):
        print "EventDirectionResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(EventDirectionResolver, self).copy_all(resolved_kb, kb)

        for kb_event in resolved_kb.evid_to_kb_event.values():
            kb_event_mentions = []
            directions = set()
            for kb_event_mention in kb_event.event_mentions:
                # Avoid redundancy
                if kb_event_mention.event_type == "Increase" or kb_event_mention.event_type == "Decrease":
                    continue
                
                if not kb_event_mention.trigger:
                    continue

                if not "direction_of_change" in kb_event_mention.properties:
                    continue
                
                direction = kb_event_mention.properties["direction_of_change"]
                if direction != "Increase" and direction != "Decrease":
                    continue
                directions.add(direction)

                event_mention_id = SharedIDManager.get_in_document_id("EventMention", kb_event_mention.document.id)
                new_kb_event_mention = KBEventMention(
                    event_mention_id,
                    kb_event_mention.document,
                    direction, 
                    kb_event_mention.trigger,
                    kb_event_mention.trigger_start,
                    kb_event_mention.trigger_end,
                    kb_event_mention.snippet,
                    kb_event_mention.sentence,
                    [],
                    kb_event_mention.model,
                    kb_event_mention.confidence)

                new_kb_event_mention.has_topic = kb_event_mention
                kb_event_mentions.append(new_kb_event_mention)
            if len(directions) != 1:
                continue
            event_id = SharedIDManager.get_in_document_id("Event", kb_event_mention.document.id)
            new_kb_event = KBEvent(
                event_id, 
                directions.pop())

            for kb_event_mention in kb_event_mentions:
                new_kb_event.add_event_mention(kb_event_mention)
            resolved_kb.add_event(new_kb_event)

        return resolved_kb
