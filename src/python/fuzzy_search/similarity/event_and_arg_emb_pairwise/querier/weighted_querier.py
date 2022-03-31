import json
import numpy as np

from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.models import CacheStorageAdapter

def build_pairwise_cache(key_getter_pairs,
                         cache_storage,
                         list_of_features,
                         threshold,
                         cutoff):

    src_annoy_id_to_dst_annoy_id_score = dict()
    feature_ids_without_all_feature_names = set()

    # loop over all features (embedding type)
    for query_feature_pair in key_getter_pairs:

        weight = query_feature_pair.weight

        if weight is None:
            weight = 1.0

        index_feature = query_feature_pair.index
        query_feature = query_feature_pair.query

        # loop over all queries
        for feature_idx, feature in enumerate(list_of_features):
            feature_value = feature.features.get(query_feature, None)

            if feature_value is None:
                feature_ids_without_all_feature_names.add(feature.feature_id)
            elif feature.feature_id in feature_ids_without_all_feature_names:
                continue
            else:
                dst_score = cache_storage.query_by_vector(feature_value,index_feature,cutoff,multiplier=len(key_getter_pairs))

                # loop over all nearest neighbors
                for dst_feature_id,neighbor_distance in dst_score.items():
                    weighted_distance = neighbor_distance * weight
                    if weighted_distance < threshold:
                        src_annoy_id_to_dst_annoy_id_score.setdefault(
                            feature.feature_id, dict()
                        ).setdefault(
                            dst_feature_id, list()
                        ).append(weighted_distance)

    # accumulate scores for all chosen feature names
    queries_to_remove = list()
    results_to_remove = list()
    for src_id, dst_id_to_scores in src_annoy_id_to_dst_annoy_id_score.items():

        # discard any queries that lack all chosen features
        if src_id in feature_ids_without_all_feature_names:
            queries_to_remove.append(src_id)
            continue

        for dst_id, scores in dst_id_to_scores.items():

            # discard any results that are not neighbors for all chosen features
            if len(scores) < len(key_getter_pairs):
                results_to_remove.append((src_id, dst_id))
                continue

            # sum the cosine angles
            single_score = np.sum(scores)
            dst_id_to_scores[dst_id] = single_score

    for src_id in queries_to_remove:
        src_annoy_id_to_dst_annoy_id_score.pop(src_id)
    for src_id, dst_id in results_to_remove:
        src_annoy_id_to_dst_annoy_id_score[src_id].pop(dst_id)

    return src_annoy_id_to_dst_annoy_id_score
