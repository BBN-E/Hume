import os,sys,json,logging
import numpy as np
current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir,os.path.pardir))
sys.path.append(project_root)

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.annoy_storage import AnnoyAdapter
from similarity.event_and_arg_emb_pairwise.querier.weighted_querier import build_pairwise_cache
from similarity.event_and_arg_emb_pairwise.config import Config
from similarity.event_and_arg_emb_pairwise.utils.merge_pairwise import merge_pairwise_cache


def main(name,args):
    if name == "BUILD_PAIRWISE_CACHE":
        query_feature_list = args.query_feature_list
        key_getter_mapping = args.key_getter_mapping
        input_cache_list = args.input_cache_list
        threshold = args.threshold
        cutoff = args.cutoff
        output_path = args.output_path


        cache_path_list = list()
        with open(input_cache_list) as fp:
            for i in fp:
                i = i.strip()
                cache_path_list.append(i)

        list_features_all = list()
        with open(query_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                list_features_all.extend(features)
        sim_matrix_all = dict()
        for cache_path in cache_path_list:
            cache_storage = AnnoyAdapter.load_storage(cache_path, {i.index for i in key_getter_mapping})
            sim_matrix = build_pairwise_cache(
                key_getter_mapping,
                cache_storage,
                list_features_all,
                threshold,
                cutoff)
            sim_matrix_all = merge_pairwise_cache([sim_matrix,sim_matrix_all],threshold,cutoff)
        with open(os.path.join(output_path,"sim.npz"), 'wb') as fp:
            np.savez_compressed(fp, sim_matrix=sim_matrix_all)

if __name__ == "__main__":
    json_path = sys.argv[1]
    querier_id = sys.argv[2]
    with open(json_path) as fp:
        j = json.load(fp)
    c = Config()
    c.update_using_dict(j)
    querier_id_to_querier = {i.id:i for i in c.queries}
    querier_config = querier_id_to_querier[querier_id]
    name = querier_config.name
    args = querier_config.args
    main(name,args)