import sys, os, codecs, re
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

class EventTypeChangeResolver(KBResolver):
    whitespace_re = re.compile(r"\s+")

    def __init__(self):
        self.type_change_cache = dict() # type and trigger => new type
        self.type_change_cache_with_orig_types = dict() # (trigger, orig_type,) => new type
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        type_change_file = os.path.join(script_dir, "..", "data_files", "corrective_event_mapping.txt")
        i = codecs.open(type_change_file, 'r', encoding='utf8')
        for line in i:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            pieces = line.rsplit(" ", 1)
            self.type_change_cache[pieces[0].lower()] = pieces[1]
        i.close()

        type_change_by_type_and_headword_file = os.path.join(script_dir, "..", "data_files", "corrective_event_mapping_with_orig_types.txt")
        i = codecs.open(type_change_by_type_and_headword_file, 'r', encoding='utf8')
        for line in i:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            pieces = line.rsplit(" ", 2)
            self.type_change_cache_with_orig_types[(pieces[0].lower(), pieces[1],)] = pieces[2]
        i.close()

    def clean_string(self, s):
        if s is None:
            return None
        
        s = EventTypeChangeResolver.whitespace_re.sub(" ", s)

        return s.lower()

    def resolve(self, kb):
        print "EventTypeChangeResolver RESOLVE"
        
        resolved_kb = KnowledgeBase()
        super(EventTypeChangeResolver, self).copy_all(resolved_kb, kb)
        
        for evid, event in kb.get_events():
            for event_mention in event.event_mentions:

                trigger = self.clean_string(event_mention.trigger)
                triggering_phrase = self.clean_string(event_mention.triggering_phrase)
                
                if (trigger, event_mention.event_type) in self.type_change_cache_with_orig_types:
                    event_mention.event_type = \
                        self.type_change_cache_with_orig_types[(trigger, event_mention.event_type)]
                    #event.event_type_to_confidence[event_mention.event_type] = 0.8

                elif (triggering_phrase, event_mention.event_type) in self.type_change_cache_with_orig_types:
                    event_mention.event_type = \
                        self.type_change_cache_with_orig_types[(triggering_phrase, event_mention.event_type)]
                    #event.event_type_to_confidence[event_mention.event_type] = 0.8

                elif trigger and trigger in self.type_change_cache:
                    event_mention.event_type = self.type_change_cache[trigger]
                    #event.event_type_to_confidence[event_mention.event_type] = 0.8
                  
                elif triggering_phrase and triggering_phrase in self.type_change_cache:
                    event_mention.event_type = self.type_change_cache[triggering_phrase]
                    #event.event_type_to_confidence[event_mention.event_type] = 0.8

        return resolved_kb
