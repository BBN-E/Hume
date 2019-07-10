from causeex_object import CauseExObject

class EventArgument(CauseExObject):
    def __init__(self, role, mention, value_mention, global_eid_or_timex):
        self.role = role
        self.mention = mention
        self.value_mention = value_mention

        self.global_eid_or_timex = global_eid_or_timex

        
