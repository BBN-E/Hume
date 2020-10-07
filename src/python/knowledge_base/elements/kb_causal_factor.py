from elements.kb_element import KBElement

class KBCausalFactor(KBElement):
    
    def __init__(self, id, factor_class, trend, relevance, magnitude):
        self.id = id
        self.factor_class = factor_class # ICM factor type (URL)
        self.trend = trend # DECREASING, NEUTRAL, INCREASING
        self.magnitude = magnitude # -1.0 to 1.0
        self.relevance = relevance # 0.0 to 1.0
