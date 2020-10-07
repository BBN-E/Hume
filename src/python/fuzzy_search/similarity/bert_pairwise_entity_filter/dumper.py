import json
import pickle

from similarity.bert_pairwise_entity_filter.query_bert_feature_extractor import MyQueryFeature, QueryId
from similarity.bert_pairwise_entity_filter.serif_bert_feature_extractor import MyEventMentionFeature, InstanceId


class ReportDumper(object):
    def __init__(self, metric,n_trees,query_result_file, query_feature_file_list, document_feature_file_list):
        self.query_result_file = query_result_file
        self.query_feature_file_list = query_feature_file_list
        self.document_feature_file_list = document_feature_file_list
        self.metric = metric
        self.n_trees = n_trees

    def dump(self):

        should_reverse = {
            'angular':False,
            'euclidean':False,
            'dot':True,
            'sklearn.cosine_similarity':True
        }

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

        output_entries = list()

        for query_id_str, doc_feature_score_dict in query_result.items():
            query_id = QueryId(**json.loads(query_id_str))
            for doc_feature_id_str in sorted(doc_feature_score_dict.keys(), key=lambda x: doc_feature_score_dict[x],reverse=should_reverse[self.metric])[:20]:
                score = doc_feature_score_dict[doc_feature_id_str]
                doc_feature_id = InstanceId(**json.loads(doc_feature_id_str))
                doc_feature = doc_feature_id_to_feature[doc_feature_id]
                output_entries.append({
                    "query": dict(query_id._asdict()),
                    "event_mention": doc_feature.aux['anchor_str'],
                    "event_sentence": doc_feature.aux['sentence_str'],
                    'event_type': doc_feature.aux['event_type'],
                    'score': score,
                    'canonical_names': list(doc_feature.canonical_names)
                })
        return output_entries
