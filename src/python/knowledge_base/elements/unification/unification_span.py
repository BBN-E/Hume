from elements.kb_sentence import KBSentence
from elements.unification.unification_element import UnificationElement

class UnificationSpan(UnificationElement):
    def __init__(self, kb_document, start, end, text):
        offset = kb_document.properties["offset"]
        self.docid = kb_document.properties["uuid"]
        self.start = start + offset
        self.length = end - start + 1
        self.text = text

    @classmethod
    def create_from_sentence(cls, kb_sentence, kb_document):
        return UnificationSpan(kb_document, kb_sentence.start_offset, kb_sentence.end_offset, kb_sentence.text)
    
    @classmethod 
    def create_from_event_mention(cls, kb_event_mention):
        kb_document = kb_event_mention.document
        if kb_event_mention.trigger:
            return UnificationSpan(
                kb_document, kb_event_mention.trigger_start, 
                kb_event_mention.trigger_end, kb_event_mention.trigger)
        if kb_event_mention.proposition_infos and len(kb_event_mention.proposition_infos) > 0:
            prop_info = kb_event_mention.proposition_infos[0]
            return UnificationSpan(
                kb_document, prop_info[1],
                prop_info[2], prop_info[0])
        return None
    
    @classmethod 
    def create_from_event_mention_anchor(cls, kb_event_mention):
        kb_document = kb_event_mention.document
        if kb_event_mention.anchor_info:
            return UnificationSpan(
                kb_document, kb_event_mention.anchor_info[1],
                kb_event_mention.anchor_info[2], kb_event_mention.anchor_info[0])
        return None
    
    def is_duplicate_of(self, other):
        return self.start == other.start and self.length == other.length

