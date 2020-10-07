import json
import pickle
import typing

from similarity.bert_pairwise_entity_filter.query_bert_feature_extractor import MyQueryFeature, QueryId
from similarity.bert_pairwise_entity_filter.serif_bert_feature_extractor import MyEventMentionFeature, InstanceId
from similarity.bert_pairwise_entity_filter.filter import Filter


class EntityConstraintFilter(Filter):

    def __init__(self, query_result_file, query_feature_file_list, document_feature_file_list):
        self.query_result_file = query_result_file
        self.query_feature_file_list = query_feature_file_list
        self.document_feature_file_list = document_feature_file_list

    def filter(self) -> typing.Dict[str, typing.Dict[str, float]]:
        query_id_to_query_feature = dict()
        with open(self.query_feature_file_list) as fp:
            for i in fp:
                i = i.strip()
                with open(i) as fp2:
                    j = json.load(fp2)
                    for k in j:
                        query_feature = MyQueryFeature.fromJSON(k)
                        query_id_to_query_feature[query_feature.feature_id] = query_feature
        doc_feature_id_to_feature = dict()
        with open(self.document_feature_file_list) as fp:
            for i in fp:
                i = i.strip()
                with open(i) as fp2:
                    j = json.load(fp2)
                    for k in j:
                        doc_feature = MyEventMentionFeature.fromJSON(k)
                        doc_feature_id_to_feature[doc_feature.feature_id] = doc_feature

        with open(self.query_result_file, 'rb') as fp:
            query_result = pickle.load(fp)
        filtered_query_result = dict()
        for query_id_str, doc_feature_score_dict in query_result.items():
            query_id = QueryId(**json.loads(query_id_str))
            allowed_entities = query_id_to_query_feature[query_id].canonical_names
            for doc_feature_id_str, score in doc_feature_score_dict.items():
                doc_feature_id = InstanceId(**json.loads(doc_feature_id_str))
                existed_entities = doc_feature_id_to_feature[doc_feature_id].canonical_names
                if allowed_entities.issubset(existed_entities):
                    filtered_query_result.setdefault(query_id_str, dict())[doc_feature_id_str] = score
        return filtered_query_result
