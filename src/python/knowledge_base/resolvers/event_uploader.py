import sys, os, sqlite3, shutil

from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

# Not really a resolver, but it does need to run during the 
# KBConstructor's resolving stage. 
# 
# Takes the events in a KB and uploads them to a database that
# a grounder can do individual grounding against. 

class EventUploader(KBResolver):
    def __init__(self):
        self.conn = None
        self.cur = None
    
    def resolve(self, kb, empty_database, output_database):
        print "EventUploader UPLOAD"

        shutil.copyfile(empty_database, output_database)
        self.conn = sqlite3.connect(output_database)
        self.cur = self.conn.cursor()

        event_count = 0

        for kb_event_id, kb_event in kb.get_events():
            event_count += 1
            for kb_event_mention in kb_event.event_mentions:
                if self.is_uploadable_event(kb_event_mention):
                    self.upload_event(kb_event_mention)
                if event_count % 250 == 0:
                    self.conn.commit()

        self.conn.commit()
        self.conn.close()

        return kb

    def is_uploadable_event(self, kb_event_mention):
        return True

    def upload_event(self, kb_event_mention):
        label = kb_event_mention.event_type
        if kb_event_mention.triggering_phrase is not None:
            label += " " + kb_event_mention.triggering_phrase
        elif kb_event_mention.trigger is not None:
            label += " " + kb_event_mention.trigger
        event_type = kb_event_mention.event_type
        location = None
        if "Place" in kb_event_mention.arguments:
            location = kb_event_mention.arguments["Place"][0].mention_head_text
        timestamp = None
        if "Time" in kb_event_mention.arguments:
            timestamp = kb_event_mention.arguments["Time"][0].normalized_date
        contexts = []
        if kb_event_mention.triggering_phrase is not None:
            contexts.append(kb_event_mention.triggering_phrase)
        elif kb_event_mention.trigger is not None:
            contexts.append(kb_event_mention.trigger)
        contexts.append(kb_event_mention.sentence.text)

        self.cur.execute("""INSERT INTO Unstructured (Label, Type, Location, Timestamp)
                            VALUES (?, ?, ?, ?)""", (label, event_type, location, timestamp,))
        unstructured_id = self.cur.lastrowid
        for context in contexts:
            self.cur.execute("""INSERT INTO UnstructuredContext (UnstructuredID, Text)
                                VALUES (?, ?)""", (unstructured_id, context,))
        
        
