import abc
import typing

from similarity.bert_pairwise_entity_filter.feature_extractor import Feature


class Similarity(abc.ABC):

    @abc.abstractmethod
    def get_similarity(self, left_representation: typing.List[Feature], right_representation: typing.List[Feature]) -> \
    typing.Dict[str, typing.Dict[str, float]]:
        pass
