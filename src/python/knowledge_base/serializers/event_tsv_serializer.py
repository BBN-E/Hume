# A class for quickly viewing event mentions sorted by document

import codecs

class EventTSVSerializer:
    def __init__(self):
        pass
    
    def serialize(self, kb, output_tsv_file):
        print("EventTSVSerializer SERIALIZE")

        o = codecs.open(output_tsv_file, 'w', encoding='utf8')

        all_event_mentions = []
        for evid, event in kb.get_events():
            o.write("---------------------------------------------\n")
            for event_mention in event.event_mentions:
                
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

        
