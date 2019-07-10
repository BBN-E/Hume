from kb_element import KBElement

class KBEntity(KBElement):
        
    def __init__(self, id, canonical_name, entity_type):
        self.id = id
        self.canonical_name = canonical_name
        self.entity_type_to_confidence = { entity_type: 0.8 }
        self.mentions = []
        self.properties = {}
        self.grounded_individuals = []

    def add_entity_type(self, entity_type, confidence):
        self.entity_type_to_confidence[entity_type] = confidence

    def get_best_entity_type(self):
        best = None
        best_score = None
        for entity_type, confidence in self.entity_type_to_confidence.iteritems():
            if best is None or confidence > best_score or (confidence == best_score and entity_type < best):
                best = entity_type
                best_score = confidence
        return best
    
    # add_mention() must be handled by KnowledgeBase
    # because it needs to update the mention to entity id map
    
