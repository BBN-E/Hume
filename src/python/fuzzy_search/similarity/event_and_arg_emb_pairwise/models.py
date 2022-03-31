
class Feature(object):
    def __init__(self, feature_id, features, aux):
        self.feature_id = feature_id
        self.features = features
        self.aux = aux

    def reprJSON(self):
        return {
            "feature_id": dict(self.feature_id._asdict()),
            "features": self.features,
            "aux": self.aux,
        }

    def reprSimpleJSON(self):
        return {
            "feature_id": dict(self.feature_id._asdict()),
            "features": self.features,
            "aux": dict()
        }

    @staticmethod
    def fromJSON(d):
        return Feature(d['feature_id'], d['features'], d['aux'])

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        return other.feature_id == self.feature_id

    def __hash__(self):
        return (self.feature_id).__hash__()

    def drop_features(self):
        self.features = None


