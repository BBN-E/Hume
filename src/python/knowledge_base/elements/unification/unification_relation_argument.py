from elements.unification.unification_element import UnificationElement


class UnificationRelationArgument(UnificationElement):
    def __init__(self, role, event_frame, confidence):
        self.role = role
        self.confidence = confidence
        self.frame = event_frame
        
    def is_duplicate_of(self, other):
        if self.role != other.role: 
            return False
        
        return self.frame.is_duplicate_of(other.frame)

    def merge_with(self, other):
        self.confidence = max(self.confidence, other.confidence)        
        self.frame.merge_with(other.frame)
