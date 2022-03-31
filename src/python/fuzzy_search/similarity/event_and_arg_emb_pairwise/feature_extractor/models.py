import abc
import typing
from similarity.event_and_arg_emb_pairwise.models import Feature

class FeatureExtractor(abc.ABC):

    @abc.abstractmethod
    def extract_features(self) -> typing.Collection[Feature]:
        pass