import os,sys,json
import numpy as np

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir,os.path.pardir))
sys.path.append(project_root)

def main(feature_list_path,output_path):
    list_features_all = list()
    with open(feature_list_path) as fp:
        for i in fp:
            i = i.strip()
            features = np.load(i, allow_pickle=True)["features"]
            for feature in features:
                feature.features = None
                list_features_all.append(feature)
    with open(os.path.join(
            output_path, "features.npz"), 'wb') as fp:
        np.savez_compressed(fp, features=list_features_all)

if __name__ == "__main__":
    feature_list_path = sys.argv[1]
    output_path = sys.argv[2]
    main(feature_list_path, output_path)