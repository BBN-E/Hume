import os,sys,json
import numpy as np
current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir,os.path.pardir))
sys.path.append(project_root)

from similarity.event_and_arg_emb_pairwise.config import Config

if __name__ == "__main__":
    json_path = sys.argv[1]
    feature_id = sys.argv[2]
    care_feature_list = sys.argv[3]
    with open(json_path) as fp:
        j = json.load(fp)
    c = Config()
    c.update_using_dict(j)
    feature_id_to_feature = {i.id:i for i in c.feature_extractors}
    dumper_config = feature_id_to_feature[feature_id]
    args = dumper_config.args
    with open(care_feature_list) as fp:
        care_feature_ids = set(json.load(fp))
    from similarity.event_and_arg_emb_pairwise.feature_extractor.utils import merge_features_by_calculating_centroid_sum,merge_feature_by_calculating_centroid_ave
    input_feature_list = args.input_feature_list
    cap = int(args.cap)
    output_path = args.output_path
    resolved_features = dict()

    if len(care_feature_ids) > 0:
        with open(input_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                resolved_features = merge_features_by_calculating_centroid_sum(features, resolved_features, cap,care_feature_ids)
        resolved_features = merge_feature_by_calculating_centroid_ave(resolved_features)

    with open(os.path.join(
            output_path, "features.npz"), 'wb') as fp:
        np.savez_compressed(fp, features=list(resolved_features.values()))