# A class for quickly viewing event mentions sorted by document

import codecs
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention

class EventTSVSerializer:
    def __init__(self):
        pass
    
    def serialize(self, kb, output_tsv_file):
        print "EventTSVSerializer SERIALIZE"

        o = codecs.open(output_tsv_file, 'w', encoding='utf8')

        all_event_mentions = []
        for evid, event in kb.get_events():
            for event_mention in event.event_mentions:
                all_event_mentions.append(event_mention)
        all_event_mentions.sort(key=lambda x: (x.document.id, x.event_type))
    
        for event_mention in all_event_mentions:
            trigger = "None"
            if event_mention.trigger is not None:
                trigger = event_mention.trigger
            if event_mention.triggering_phrase is not None:
                trigger = event_mention.triggering_phrase
            o.write(
                event_mention.document.id + "\t" +
                event_mention.event_type + "\t" +
                event_mention.model + "\t" +
                trigger + "\t" +
                event_mention.sentence.text + "\n"
                )
        o.close()

        
