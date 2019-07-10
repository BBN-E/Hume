# This is to create dummy objects that can 
# take the place of Serif ActorEntity and ActorMention
# objects to short-circuit the actor matches in one place

class SerifActorEntity:
    def __init__(self, name, actor_uid):
        self.actor_name = name
        self.actor_mentions = []
        self.actor_uid = actor_uid

class SerifActorMention:
    def __init__(self, name):
        self.actor_name = name
        self.actor_uid = None
        self.paired_agent_name = None
        self.paired_actor_name = None
