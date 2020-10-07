from elements.kb_event_mention import KBEventMention
from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention
from elements.unification.unification_entity import UnificationEntity
from elements.unification.unification_element import UnificationElement
from elements.unification.unification_span import UnificationSpan

class UnificationEventArgument(UnificationElement):
    def __init__(self, role, kb_mention_or_value_mention, kb, confidence):
        self.role = role
        self.confidence = confidence
        if isinstance(kb_mention_or_value_mention, KBMention):
            self.entity = UnificationEntity(kb_mention_or_value_mention, kb)
            self.span = None
        if isinstance(kb_mention_or_value_mention, KBValueMention):
            self.span = UnificationSpan(kb_mention_or_value_mention.document, kb_mention_or_value_mention.head_start_char, kb_mention_or_value_mention.head_end_char, kb_mention_or_value_mention.value_mention_text)
            self.entity = None

    def is_duplicate_of(self, other):
        if self.role != other.role:
            return False
        
        if self.entity is not None and other.entity is not None:
            return self.entity.is_duplicate_of(other.entity)
        
        if self.span is not None and other.span is not None:
            return self.span.is_duplicate_of(other.span)
        
        return True
        
