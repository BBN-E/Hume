import sys, os, codecs
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

class EventRemovalResolver(KBResolver):
    def __init__(self):
        self.bad_trigger_words = set()
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        bad_trigger_word_file = os.path.join(script_dir, "..", "data_files", "bad_trigger_words.txt")

        bdw = codecs.open(bad_trigger_word_file, 'r', encoding='utf8')
        for line in bdw:
            line = line.strip()
            self.bad_trigger_words.add(line.lower())
        bdw.close()

    def correct_event_type(self, event):
        event_type = event.event_type_to_confidence.keys()[0]
        if "050" in event_type or "073" in event_type or "070" in event_type or "051" in event_type \
                or "130" in event_type or "111" in event_type or "100" in event_type or "0333" in event_type:
            return None

        ## factor -> Factor
        #if "factor" in event_type or "Factor" in event_type:
        #    event.event_type_to_confidence = {"Factor": 0.5}
        #    return event

        ## /event/Weather -> /event/Factor/Weather
        #if "." not in event_type:
        #    event.event_type_to_confidence = {"Factor/" + event_type: 0.5}
        #    return event

        return event

    def resolve(self, kb):
        print "EventRemovalResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(EventRemovalResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_events_relations_and_groups()

        bad_event_ids = set()
        for evid, event in kb.get_events():
            found_good_event_mention = False
            for event_mention in event.event_mentions:
                if event_mention.trigger is None or event_mention.trigger.lower() not in self.bad_trigger_words:
                    found_good_event_mention = True
                    break
            if found_good_event_mention:
                corrected_event = self.correct_event_type(event)

                if corrected_event is not None:
                    resolved_kb.add_event(event)
            else:
                bad_event_ids.add(evid)
                
        for relid, relation in kb.get_relations():
            if relation.left_argument_id not in bad_event_ids and relation.right_argument_id not in bad_event_ids:
                resolved_kb.add_relation(relation)

        return resolved_kb

    
