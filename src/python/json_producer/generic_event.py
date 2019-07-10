from causeex_object import CauseExObject

class GenericEvent(CauseExObject):

    def __init__(self, docid, snippet, event_type, anchor_text, anchor_start, anchor_end, sent_no):
        self.docid = docid
        self.snippet = snippet
        self.event_type = event_type
        self.anchor_text = anchor_text
        self.anchor_start = anchor_start
        self.anchor_end = anchor_end
        self.sent_no = sent_no

        self.arguments = []

    def add_argument(self, event_argument):
        self.arguments.append(event_argument)
