
import os,sys,json,logging
import numpy as np

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir,os.path.pardir))
sys.path.append(project_root)

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.annoy_index_builder import annoy_index_builder
from similarity.event_and_arg_emb_pairwise.config import Config


def main(name,args):
    if name == "Annoy":
        feature_list_path = args.input_feature_list
        annoy_metric = args.annoy_metric
        n_trees = int(args.n_trees)
        output_path = args.output_path
        annoy_index_builder(annoy_metric, n_trees, feature_list_path,output_path)

if __name__ == "__main__":
    json_path = sys.argv[1]
    index_id = sys.argv[2]
    with open(json_path) as fp:
        j = json.load(fp)
    c = Config()
    c.update_using_dict(j)
    index_id_to_index = {i.id:i for i in c.indexing_features}
    index_config = index_id_to_index[index_id]
    name = index_config.name
    args = index_config.args
    main(name,args)