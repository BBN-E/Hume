import os
import logging
import annoy
import numpy as np
import json

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.models import CacheStorageAdapter
from similarity.event_and_arg_emb_pairwise.utils.common import create_file_name_to_path


class AnnoyAdapter(CacheStorageAdapter):

    def __init__(self, annoy_metric, **kwargs):
        super().__init__()
        self.feature_name_to_annoy_cache = dict()
        self.feature_id_to_annoy_idx = dict()
        self.feature_name_to_dimension = dict()
        self.current_feature_idx = 0
        self.annoy_metric = annoy_metric
        self.annoy_idx_to_feature_id = dict()

    def store(self, feature):
        for feature_name, value in feature.features.items():
            dimension = len(value)
            self.feature_name_to_dimension[feature_name] = dimension
            annoy_ins = self.feature_name_to_annoy_cache.setdefault(
                feature_name, annoy.AnnoyIndex(dimension, self.annoy_metric))
            annoy_ins.add_item(self.current_feature_idx, value)
        self.feature_id_to_annoy_idx[feature.feature_id] = (
            self.current_feature_idx)
        self.current_feature_idx += 1

    def init_storage(self, **kwargs):
        pass

    def finalize_storage(self, n_trees, output_path, **kwargs):
        for i, (name, annoy_ins) in enumerate(self.feature_name_to_annoy_cache.items()):
            logger.info("Building cache {}/{} for feature name {}".format(
                i + 1, len(self.feature_name_to_annoy_cache), name))
            annoy_ins.build(n_trees)
        os.makedirs(output_path, exist_ok=True)

        with open(os.path.join(
                output_path, "feature_id_to_annoy_idx.npz"), 'wb') as fp:
            np.savez_compressed(
                fp, feature_id_to_annoy_idx=self.feature_id_to_annoy_idx)
        feature_name_to_annoy_path = dict()
        for feature_name, annoy_cache in self.feature_name_to_annoy_cache.items():
            annoy_cache.save(
                os.path.join(output_path, "{}.ann".format(feature_name)))
            feature_name_to_annoy_path[feature_name] = os.path.join(output_path, "{}.ann".format(feature_name))
        with open(os.path.join(output_path, 'cache_config.json'), 'w') as fp:
            features = {
                    feature_name: {"dimension": self.feature_name_to_dimension[feature_name],
                                   "path": feature_name_to_annoy_path[feature_name]} for feature_name in
                self.feature_name_to_dimension.keys()
                }
            config_d = dict()
            config_d["features"] = features
            config_d["annoy_metric"] = self.annoy_metric
            config_d["feature_id_to_annoy_idx"] = os.path.join(
                output_path, "feature_id_to_annoy_idx.npz")
            json.dump(config_d, fp)

    @staticmethod
    def load_storage(input_path, chosen_feature_names=None, **kwargs):


        with open(os.path.join(input_path)) as fp:
            config_j = json.load(fp)
        annoy_metric = config_j["annoy_metric"]
        feature_id_to_annoy_idx = dict(
            np.load(config_j["feature_id_to_annoy_idx"], allow_pickle=True)
            ["feature_id_to_annoy_idx"].item())
        feature_name_to_dimension = dict()
        feature_name_to_annoy_path = dict()
        for feature_name,prop in config_j['features'].items():
            feature_name_to_dimension[feature_name] = prop["dimension"]
            feature_name_to_annoy_path[feature_name] = prop["path"]
        feature_name_to_annoy_cache = dict()
        for feature_name, annoy_path in feature_name_to_annoy_path.items():
            if chosen_feature_names is not None and feature_name not in chosen_feature_names:
                continue
            annoy_ins = annoy.AnnoyIndex(feature_name_to_dimension[feature_name],
                                         annoy_metric)
            annoy_ins.load(annoy_path)
            feature_name_to_annoy_cache[feature_name] = annoy_ins
        annoy_storage = AnnoyAdapter(annoy_metric)
        annoy_storage.feature_name_to_annoy_cache = feature_name_to_annoy_cache
        annoy_storage.feature_id_to_annoy_idx = feature_id_to_annoy_idx
        annoy_storage.feature_name_to_dimension = feature_name_to_dimension
        annoy_storage.current_feature_idx = -100
        return annoy_storage

    def query_by_vector(self, vector, feature_name, topK, **kwargs):
        ret = dict()
        if feature_name not in self.feature_name_to_annoy_cache:
            return ret

        if len(self.annoy_idx_to_feature_id) < 1:
            self.annoy_idx_to_feature_id = {v: k for k, v in self.feature_id_to_annoy_idx.items()}

        multiplier = 1
        if "multiplier" in kwargs:
            multiplier = kwargs['multiplier']
        annoy_cache = self.feature_name_to_annoy_cache[feature_name]

        nearest_neighbor_idxs, nearest_neighbor_distances = (
            annoy_cache.get_nns_by_vector(
                vector,
                topK * multiplier,
                search_k=-1,
                include_distances=True)
        )
        for idx in range(len(nearest_neighbor_idxs)):
            neighbor_annoy_idx = nearest_neighbor_idxs[idx]
            neighbor_distance = nearest_neighbor_distances[idx]
            dst_feature_id = self.annoy_idx_to_feature_id[neighbor_annoy_idx]
            ret[dst_feature_id] = neighbor_distance
        return ret
