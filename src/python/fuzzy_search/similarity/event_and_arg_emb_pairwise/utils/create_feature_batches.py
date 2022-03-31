import os,sys,json,logging

import numpy as np

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir,os.path.pardir))
sys.path.append(project_root)

from similarity.event_and_arg_emb_pairwise.config import Config
from similarity.event_and_arg_emb_pairwise.models import Feature

logger = logging.getLogger(__name__)

def list_spliter_by_num_of_batches(my_list, num_of_batches):
    k, m = divmod(len(my_list), num_of_batches)
    return list(my_list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(num_of_batches))



if __name__ =="__main__":
    json_path = sys.argv[1]
    feature_id = sys.argv[2]

    with open(json_path) as fp:
        j = json.load(fp)
    c = Config()
    c.update_using_dict(j)
    feature_id_to_feature = {i.id:i for i in c.feature_extractors}
    feature_extractor_config = feature_id_to_feature[feature_id]
    args = feature_extractor_config.args
    output_path = args.output_path

    number_of_batches = int(feature_extractor_config.number_of_batches)
    input_feature_list = args.input_feature_list
    feature_ids = set()
    with open(input_feature_list) as fp:
        for i in fp:
            i = i.strip()
            features = np.load(i, allow_pickle=True)["features"]
            for feature in features:
                feature_ids.add(feature.feature_id)
    batches = list_spliter_by_num_of_batches(list(feature_ids),number_of_batches)

    for batch_id,batch in enumerate(batches):
        with open(os.path.join(output_path,"{}.list".format(batch_id)),'w') as wfp:
            json.dump(batch,wfp)
