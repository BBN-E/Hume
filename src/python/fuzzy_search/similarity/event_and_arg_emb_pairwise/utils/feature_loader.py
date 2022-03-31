
import numpy as np

def load_features(feature_path_list):
    list_features_all = list()
    for feature_path in feature_path_list:
        with open(feature_path) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)
    feature_id_to_feature = {f.feature_id: f for f in list_features_all}
    return feature_id_to_feature

