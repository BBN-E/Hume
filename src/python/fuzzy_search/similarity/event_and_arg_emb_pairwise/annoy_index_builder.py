import json
import typing
import logging
import numpy as np
import time

from annoy import AnnoyIndex

logger = logging.getLogger(__name__)


def annoy_index_builder(annoy_metric, n_trees, feature_list_path):
    feature_name_to_annoy_cache = dict()
    feature_id_to_annoy_idx = dict()
    feature_name_to_dimension = dict()
    current_feature_idx = 0
    with open(feature_list_path) as fp:
        for idx, i in enumerate(fp):
            i = i.strip()
            logger.info("Reading {}".format(i))
            features = np.load(i, allow_pickle=True)["features"]
            for feature in features:
                for feature_name, value in feature.features.items():
                    dimension = len(value)
                    feature_name_to_dimension[feature_name] = dimension
                    annoy_ins = feature_name_to_annoy_cache.setdefault(
                        feature_name, AnnoyIndex(dimension, annoy_metric))
                    annoy_ins.add_item(current_feature_idx, value)
                feature_id_to_annoy_idx[feature.feature_id] = (
                    current_feature_idx)
                current_feature_idx += 1

    for i, (name, annoy_ins) in enumerate(feature_name_to_annoy_cache.items()):
        logger.info("Building cache {}/{} for feature name {}".format(
            i+1, len(feature_name_to_annoy_cache), name))
        annoy_ins.build(n_trees)

    return (feature_name_to_annoy_cache,
            feature_id_to_annoy_idx,
            feature_name_to_dimension)
