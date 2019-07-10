from causeex_object import CauseExObject

class Event(CauseExObject):

    def __init__(self, snippet, event_type, genericity, polarity, tense, modality, anchor_text, docid, anchor_start, anchor_end, sent_no):
        self.snippet = snippet
        self.event_type = event_type
        self.genericity = genericity
        self.polarity = polarity
        self.tense = tense
        self.modality = modality
        self.anchor_text = anchor_text
        self.docid = docid
        self.anchor_start = anchor_start
        self.anchor_end = anchor_end
        self.sent_no = sent_no

        self.arguments = []

    def add_argument(self, event_argument):
        self.arguments.append(event_argument)
