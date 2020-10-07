import json
import typing

from annoy import AnnoyIndex

from similarity.bert_pairwise_entity_filter.feature_extractor import Feature
from similarity.bert_pairwise_entity_filter.similarity_module import Similarity


class CosineSimilarityModule(Similarity):
    def get_similarity(self,metric,n_trees, query_representation: typing.List[Feature],
                       document_representation: typing.List[Feature]) -> typing.Dict[str, typing.Dict[str, float]]:
        right_list = [[json.dumps(dict(i.feature_id._asdict())), i.feature] for i in document_representation]
        right_numpy_list = list(i[1] for i in right_list)
        if len(right_numpy_list) < 1:
            return dict()
        f = len(right_numpy_list[0])
        t = AnnoyIndex(f, metric)
        for i, v in enumerate(right_numpy_list):
            t.add_item(i, v)
        t.build(n_trees)
        query_to_similar_mention_id_to_dis = dict()
        for query_feature in query_representation:
            nns_ids, nns_diss = t.get_nns_by_vector(query_feature.feature, len(right_list), search_k=-1,
                                                    include_distances=True)
            for idx in range(len(nns_ids)):
                nns_id = nns_ids[idx]
                nns_dis = nns_diss[idx]
                query_to_similar_mention_id_to_dis.setdefault(json.dumps(dict(query_feature.feature_id._asdict())),
                                                              dict())[right_list[nns_id][0]] = nns_dis
        return query_to_similar_mention_id_to_dis

# class CosineSimilarityModule(Similarity):
#     def get_similarity(self,metric,n_trees, query_representation: typing.List[Feature],
#                        document_representation: typing.List[Feature]) -> typing.Dict[str, typing.Dict[str, float]]:
#         right_list = [[json.dumps(dict(i.feature_id._asdict())), i.feature] for i in document_representation]
#         right_numpy_list = list(i[1] for i in right_list)
#         if len(right_numpy_list) < 1:
#             return dict()
#         f = len(right_numpy_list[0])
#
#         query_to_similar_mention_id_to_dis = dict()
#         for query_feature in query_representation:
#             nns_ids = cosine_similarity(right_numpy_list,[query_feature.feature])
#
#             for idx in range(len(nns_ids)):
#                 nns_id = idx
#                 nns_dis = nns_ids[idx][0]
#                 query_to_similar_mention_id_to_dis.setdefault(json.dumps(dict(query_feature.feature_id._asdict())),
#                                                               dict())[right_list[nns_id][0]] = nns_dis.item()
#         return query_to_similar_mention_id_to_dis