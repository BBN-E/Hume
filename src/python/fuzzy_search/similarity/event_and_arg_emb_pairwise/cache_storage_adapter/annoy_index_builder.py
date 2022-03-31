import json
import typing
import logging
import numpy as np
import time

from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.annoy_storage import AnnoyAdapter

logger = logging.getLogger(__name__)


def annoy_index_builder(annoy_metric, n_trees, feature_list_path, output_path):
    annoy_storage = AnnoyAdapter(annoy_metric)
    annoy_storage.init_storage()
    with open(feature_list_path) as fp:
        for idx, i in enumerate(fp):
            i = i.strip()
            logger.info("Reading {}".format(i))
            features = np.load(i, allow_pickle=True)["features"]
            for feature in features:
                annoy_storage.store(feature)
    annoy_storage.finalize_storage(n_trees,output_path)

