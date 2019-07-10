from causeex_object import CauseExObject

class AgentMatch(CauseExObject):

    def __init__(self, paired_agent_name, paired_actor_name):
        self.paired_agent_name = paired_agent_name
        self.paired_actor_name = paired_actor_name

