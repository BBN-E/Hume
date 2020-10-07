from elements.unification.unification_element import UnificationElement

class UnificationCausalFactor(UnificationElement):
    def __init__(self, kb_causal_factor):
        self.factor_class = kb_causal_factor.factor_class # ICM factor type (URL)
        self.trend = kb_causal_factor.trend # DECREASING, NEUTRAL, INCREASING
        self.magnitude = kb_causal_factor.magnitude # -1.0 to 1.0
        self.relevance = kb_causal_factor.relevance # 0.0 to 1.0
