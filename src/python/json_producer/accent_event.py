from causeex_object import CauseExObject

class AccentEvent(CauseExObject):
    def __init__(self, snippet, event_code, event_tense, event_name, participants, source_eid, target_eid, time_value_mention, docid, sent_no):
        self.snippet = snippet
        self.event_code = event_code
        self.event_tense = event_tense
        self.event_name = event_name
        self.participants = participants
        
        self.source_eid = source_eid
        self.target_eid = target_eid

        self.time_value_mention = time_value_mention

        self.docid = docid
        self.sent_no = sent_no
