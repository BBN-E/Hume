from elements.kb_event_mention import KBEventMention
from unification_event_frame import UnificationEventFrame
from unification_element import UnificationElement

class UnificationRelationArgument(UnificationElement):
    def __init__(self, role, kb_event_mention, kb):
        self.role = role
        self.confidence = kb_event_mention.confidence
        self.frame = UnificationEventFrame(kb_event_mention, kb)
        
    def is_duplicate_of(self, other):
        if self.role != other.role: 
            return False
        
        return self.frame.is_duplicate_of(other.frame)

    def merge_with(self, other):
        self.confidence = max(self.confidence, other.confidence)        
        self.frame.merge_with(other.frame)
