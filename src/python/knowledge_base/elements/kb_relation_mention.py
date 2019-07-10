from kb_element import KBElement
from kb_event_mention import KBEventMention

class KBRelationMention(KBElement):

    relation_type_specificity_score = {
        "MitigatingFactor-Effect": 6,
        "Preventative-Effect": 5,
        "Precondition-Effect": 4,
        "Catalyst-Effect": 3,
        "Before-After": 2,
        "Cause-Effect": 1,
    }
    
    def __init__(self, rel_mention_id, left_mention, right_mention, snippet, kb_document):
        self.id = rel_mention_id
        self.left_mention = left_mention
        self.right_mention = right_mention
        self.snippet = snippet
        self.document = kb_document
        self.confidence = 0.5
        self.properties = dict()

    def is_similar_and_better_than(self, other, self_type, other_type):
        # Only implemented for event-event relations
        if not isinstance(self.left_mention, KBEventMention) or not isinstance(self.right_mention, KBEventMention):
            return False
        if not isinstance(other.left_mention, KBEventMention) or not isinstance(other.right_mention, KBEventMention):
            return False

        self_left_em = self.left_mention
        self_right_em = self.right_mention

        other_left_em = other.left_mention
        other_right_em = other.right_mention

        # Must have same sentences
        if self_left_em.sentence != other_left_em.sentence or self_right_em.sentence != other_right_em.sentence:
            return False

        # Must have same trigger words
        if self_left_em.trigger != other_left_em.trigger or self_right_em.trigger != other_right_em.trigger:
            return False

        # Must not have specific (non-"factor", non-"Generic") types that differ
        if (self.types_are_specific_and_differ(self_left_em, other_left_em) or 
            self.types_are_specific_and_differ(self_right_em, other_right_em)):
            return False

        # Before-After relations are different than other types
        if (self_type == "Before-After" and other_type != "Before-After" or
            self_type != "Before-After" and other_type == "Before-After"):
            return False
        
        # These relations are similar, check if self is better than other

        # More arguments are better
        self_argument_count = len(self_left_em.arguments) + len(self_right_em.arguments)
        other_argument_count = len(other_left_em.arguments) + len(other_right_em.arguments)
        if self_argument_count > other_argument_count:
            return True
        if other_argument_count > self_argument_count:
            return False

        # Typed events are better than Factor or factor events
        if self.event_type_score() > other.event_type_score():
            return True
        if other.event_type_score() > self.event_type_score():
            return False

        # More specific relation types are better
        self_specificity_score = KBRelationMention.relation_type_specificity_score.get(self_type)
        if self_specificity_score is None:
            self_specificity_score = 0
        other_specificity_score = KBRelationMention.relation_type_specificity_score.get(other_type)
        if other_specificity_score is None:
            other_specificity_score = 0
        if self_specificity_score > other_specificity_score:
            #print "Throwing out relation due to relation type score: " + str(self_type) + " > " + str(other_type)
            return True
        if other_specificity_score > self_specificity_score:
            return False

        # Tie breaker
        return self.id < other.id
            
    def types_are_specific_and_differ(self, em1, em2):
        if em1.event_type.lower() == "factor" or em2.event_type.lower() == "factor":
            return False
        
        if em1.event_type == "Event" or em2.event_type == "Event":
            return False

        return em1.event_type != em2.event_type
    
    def event_type_score(self):
        score = 0
        if self.left_mention.event_type == "factor":
            score += 0
        elif self.left_mention.event_type == "Factor":
            score += 0.2
        elif self.left_mention.event_type == "Event":
            score += 0.3
        else:
            score += 1

        if self.right_mention.event_type == "factor":
            score += 0
        elif self.right_mention.event_type == "Factor":
            score += 0.2
        elif self.right_mention.event_type == "Event":
            score += 0.3
        else:
            score += 1
            
        return score
        


