import json
import numpy as np


def build_pairwise_cache(chosen_feature_names,
                         weights,
                         list_of_features,
                         feature_name_to_annoy_cache,
                         feature_id_to_annoy_idx,
                         threshold,
                         cutoff):

    if weights is None:
        weights = [1.0] * len(chosen_feature_names)
    assert len(weights) == len(chosen_feature_names)

    annoy_idx_to_feature_id = {v: k for k, v in feature_id_to_annoy_idx.items()}
    src_annoy_id_to_dst_annoy_id_score = dict()
    feature_ids_without_all_feature_names = set()

    # loop over all features (embedding type)
    for i, chosen_feature_name in enumerate(chosen_feature_names):

        if chosen_feature_name not in feature_name_to_annoy_cache.keys():
            continue
        annoy_cache = feature_name_to_annoy_cache[chosen_feature_name]
        w = weights[i]

        # loop over all queries
        for feature_idx, feature in enumerate(list_of_features):
            feature_value = feature.features.get(chosen_feature_name, None)

            if feature_value is None:
                feature_ids_without_all_feature_names.add(feature.feature_id)
            elif feature.feature_id in feature_ids_without_all_feature_names:
                continue
            else:
                nearest_neighbor_idxs, nearest_neighbor_distances = (
                    annoy_cache.get_nns_by_vector(
                        feature_value,
                        cutoff * len(chosen_feature_names),
                        search_k=-1,
                        include_distances=True))

                # loop over all nearest neighbors
                for idx in range(len(nearest_neighbor_idxs)):
                    neighbor_annoy_idx = nearest_neighbor_idxs[idx]
                    neighbor_distance = nearest_neighbor_distances[idx]
                    weighted_distance = neighbor_distance * w
                    if weighted_distance < threshold:
                        src_annoy_id_to_dst_annoy_id_score.setdefault(
                            feature.feature_id, dict()
                        ).setdefault(
                            annoy_idx_to_feature_id[neighbor_annoy_idx], list()
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
            if len(scores) < len(chosen_feature_names):
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
