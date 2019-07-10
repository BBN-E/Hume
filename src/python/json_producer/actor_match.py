from causeex_object import CauseExObject

class ActorMatch(CauseExObject):

    def __init__(self, actor_name, latitude, longitude):
        self.actor_name = actor_name
        self.latitude = latitude
        self.longitude = longitude


