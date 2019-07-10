from causeex_object import CauseExObject

class RelationMention(CauseExObject):

    def __init__(self, relation_type, tense, modality, left_mention, right_mention, left_eid, right_eid, snippet):
        self.relation_type = relation_type
        self.tense = tense
        self.modality = modality
        self.left_mention = left_mention
        self.left_eid = left_eid
        self.right_mention = right_mention
        self.right_eid = right_eid
        self.time_arg_role = None
        self.time_arg = None
        self.snippet = snippet

    def add_time_arg(self, value_mention, role):
        self.time_arg_role = role
        self.time_value_mention = value_mention
