import abc
import typing


class Feature(abc.ABC):
    def __init__(self, feature_id, feature, aux):
        self.feature_id = feature_id
        self.feature = feature
        self.aux = aux

    def reprJSON(self):
        return {
            "feature_id": dict(self.feature_id._asdict()),
            "feature": self.feature,
            "aux": self.aux,
        }

    def reprSimpleJSON(self):
        return {
            "feature_id": dict(self.feature_id._asdict()),
            "feature": self.feature,
            "aux": dict()
        }

    @staticmethod
    def fromJSON(d):
        return Feature(d['feature_id'], d['feature'], d['aux'])

    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        return other.feature_id == self.feature_id

    def __hash__(self):
        return (self.feature_id).__hash__()


class FeatureExtractor(abc.ABC):
    """
    Convert to id<->representation
    """

    @abc.abstractmethod
    def extract(self) -> typing.List[Feature]:
        pass
