import json

from similarity.bert_pairwise_entity_filter.feature_extractor import FeatureExtractor
from similarity.bert_pairwise_entity_filter.query_bert_feature_extractor import QueryId,MyQueryFeature

class CentroidFeatureExtractor(FeatureExtractor):
    def __init__(self,centroid_path):
        self.centroid_path = centroid_path

    def extract(self):
        with open(self.centroid_path) as fp:
            type_to_centroid = json.load(fp)

        res = list()
        for event_type,centroid in type_to_centroid.items():
            res.append(MyQueryFeature(QueryId(event_type,event_type),centroid,set(),{}))
        return res