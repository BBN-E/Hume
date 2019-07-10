from causeex_object import CauseExObject

class Mention(CauseExObject):
    def __init__(self, entity_type, mention_type, mention_text, mention_head_text, docid, start_char, end_char, head_start_char, head_end_char, sent_no):
        self.entity_type = entity_type
        self.mention_type = mention_type
        self.mention_text = mention_text
        self.mention_head_text = mention_head_text
        self.docid = docid
        self.start_char = start_char
        self.end_char = end_char
        self.head_start_char = head_start_char
        self.head_end_char = head_end_char
        self.sent_no = sent_no
        self.actor_match = None
        self.agent_match = None

    def add_actor_match(self, actor_match):
        self.actor_match = actor_match

    def add_agent_match(self, agent_match):
        self.agent_match = agent_match


