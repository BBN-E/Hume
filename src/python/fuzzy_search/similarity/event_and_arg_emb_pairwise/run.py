import os, sys, json, logging, time, multiprocessing

import numpy as np

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)


from similarity.event_and_arg_emb_pairwise.annoy_index_builder import annoy_index_builder
from similarity.event_and_arg_emb_pairwise.build_pairwise_cache import build_pairwise_cache
from similarity.event_and_arg_emb_pairwise.dump_pairwise_similarity_to_file import dump_pairwise_to_file
from similarity.event_and_arg_emb_pairwise.merge_pairwise_cache import merge_pairwise_cache
from similarity.event_and_arg_emb_pairwise.dump_pairwise_similarity_to_learnit_tabular import dump_pairwise_to_learnit_tabular

logger = logging.getLogger(__name__)


def create_doc_id_to_path(file_list, extension):
    docid_to_path = dict()
    with open(file_list) as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i).replace(extension, "")
            docid_to_path[docid] = i
    return docid_to_path


def main():
    logging.basicConfig(
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        level=logging.DEBUG)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True)
    parser.add_argument('--output_path', required=False)
    parser.add_argument("--output_prefix", required=False, type=str)
    parser.add_argument("--should_drop_features_array_when_merging",
                        required=False, type=str)
    parser.add_argument('--input_serif_list', required=False)
    parser.add_argument('--input_bert_npz_list', required=False)
    parser.add_argument('--input_serif_npz_dir', required=False)
    parser.add_argument('--input_learnit_obversation_instance_json_file', required=False)
    parser.add_argument('--key_getter_str', required=False, nargs="+")
    parser.add_argument('--key_getter_weights',
                        required=False, nargs="+", type=float)
    parser.add_argument('--input_feature_list', required=False)
    parser.add_argument('--input_annoy_cache_list', required=False)

    parser.add_argument('--annoy_metric', required=False)
    parser.add_argument('--n_trees', required=False, type=int)
    parser.add_argument('--feature_name_to_dimension_path', required=False)
    parser.add_argument('--feature_id_to_annoy_idx_path', required=False)

    parser.add_argument('--threshold', required=False, type=float)
    parser.add_argument('--cutoff', required=False, type=int)

    parser.add_argument('--sim_matrix_path', required=False)
    parser.add_argument('--sim_matrix_path_list', required=False)
    parser.add_argument("--use_argument_names", required=False, default="false")

    args = parser.parse_args()

    if args.mode == "BUILD_SERIF_DOC_NLPLINGO_FEATURE":
        from similarity.event_and_arg_emb_pairwise.serif_nlplingo_feature_extractor import \
            extract_serif_nlplingo_feature
        serif_list = args.input_serif_list
        npz_dir = args.input_serif_npz_dir
        output_path = args.output_path
        output_prefix = args.output_prefix
        key_getter_strs = args.key_getter_str
        input_bert_npz_list = args.input_bert_npz_list

        doc_id_to_bert_npz_path = create_doc_id_to_path(input_bert_npz_list,
                                                        ".npz")

        list_features_all = list()
        extracted_features = extract_serif_nlplingo_feature(
            serif_list, npz_dir, doc_id_to_bert_npz_path, key_getter_strs)
        list_features_all.extend(extracted_features)
        with open(os.path.join(
                output_path, output_prefix + "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    elif args.mode == "BUILD_LEARNIT_OBVERSATION_FEATURE":
        from similarity.event_and_arg_emb_pairwise.learnit_obversation_ave_bert_feature_extractor import \
            extract_average_bert_emb_for_learnit_obversation
        input_bert_npz_list = args.input_bert_npz_list # This is not from pipeline
        input_learnit_obversation_instance_json_file = args.input_learnit_obversation_instance_json_file
        output_path = args.output_path
        output_prefix = args.output_prefix
        feature_list = extract_average_bert_emb_for_learnit_obversation(input_bert_npz_list,input_learnit_obversation_instance_json_file)
        with open(os.path.join(
                output_path, output_prefix + "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=feature_list)

    elif args.mode == "MERGE_FEATURE_NPZ":
        feature_list = args.input_feature_list
        output_path = args.output_path
        should_drop_features_array_when_merging = True \
            if args.should_drop_features_array_when_merging.lower() == "true" \
            else False
        list_features_all = list()
        with open(feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    if should_drop_features_array_when_merging is True:
                        feature.features = dict()
                    list_features_all.append(feature)
        with open(os.path.join(output_path), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    elif args.mode == "BUILD_ANNOY_INDEX":
        feature_list_path = args.input_feature_list
        annoy_metric = args.annoy_metric
        n_trees = args.n_trees
        output_path = args.output_path
        (feature_name_to_annoy_cache,
         feature_id_to_annoy_idx,
         feature_name_to_dimension
         ) = annoy_index_builder(annoy_metric, n_trees, feature_list_path)
        with open(os.path.join(
                output_path, "feature_id_to_annoy_idx.npz"), 'wb') as fp:
            np.savez_compressed(
                fp, feature_id_to_annoy_idx=feature_id_to_annoy_idx)
        for feature_name, annoy_cache in feature_name_to_annoy_cache.items():
            annoy_cache.save(
                os.path.join(output_path, "{}.ann".format(feature_name)))
        with open(os.path.join(
                output_path, "feature_name_to_dimension.npz"), 'wb') as fp:
            np.savez_compressed(
                fp, feature_name_to_dimension=feature_name_to_dimension)

    elif args.mode == "BUILD_PAIRWISE_CACHE":
        from annoy import AnnoyIndex
        feature_list = args.input_feature_list
        chosen_feature_names = args.key_getter_str
        chosen_feature_weights = args.key_getter_weights
        annoy_metric = args.annoy_metric
        input_annoy_cache_list = args.input_annoy_cache_list
        feature_name_to_dimension_path  = args.feature_name_to_dimension_path
        feature_id_to_annoy_idx_path = args.feature_id_to_annoy_idx_path
        threshold = args.threshold
        cutoff = args.cutoff
        output_path = args.output_path

        assert (chosen_feature_weights is None
                or len(chosen_feature_weights) == len(chosen_feature_names))

        feature_id_to_annoy_idx = dict(
            np.load(feature_id_to_annoy_idx_path, allow_pickle=True)
            ["feature_id_to_annoy_idx"].item())
        feature_name_to_dimension = dict(
            np.load(feature_name_to_dimension_path, allow_pickle=True)
            ["feature_name_to_dimension"].item())
        feature_name_to_annoy_path = create_doc_id_to_path(
            input_annoy_cache_list, ".ann")
        feature_name_to_annoy_cache = dict()
        for feature_name, annoy_path in feature_name_to_annoy_path.items():

            if feature_name not in chosen_feature_names:
                continue

            annoy_ins = AnnoyIndex(feature_name_to_dimension[feature_name],
                                   annoy_metric)
            annoy_ins.load(annoy_path)
            feature_name_to_annoy_cache[feature_name] = annoy_ins
        list_features_all = list()
        with open(feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                list_features_all.extend(features)
        sim_matrix = build_pairwise_cache(
            chosen_feature_names,
            chosen_feature_weights,
            list_features_all,
            feature_name_to_annoy_cache,
            feature_id_to_annoy_idx,
            threshold,
            cutoff)
        with open(os.path.join(output_path), 'wb') as fp:
            np.savez_compressed(fp, sim_matrix=sim_matrix)

    elif args.mode == "MERGE_PAIRWISE_CACHE":
        sim_matrix_path_list = args.sim_matrix_path_list
        threshold = args.threshold
        cutoff = args.cutoff
        output_path = args.output_path
        sim_matrix = merge_pairwise_cache(
            sim_matrix_path_list, threshold, cutoff)
        with open(output_path, 'wb') as fp:
            np.savez_compressed(fp, sim_matrix=sim_matrix)

    elif args.mode == "DUMP_PAIRWISE_CACHE_TO_FILE":
        feature_list = args.input_feature_list
        sim_matrix_path = args.sim_matrix_path
        output_path = args.output_path
        cutoff = args.cutoff
        use_arg_names = False
        if args.use_argument_names.lower() == "true":
            use_arg_names = True

        list_features_all = list()
        with open(feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                list_features_all.extend(features)

        sim_matrix = dict(
            np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
        dump_pairwise_to_file(
            list_features_all,
            sim_matrix,
            output_path,
            cutoff,
            use_arg_names)
    elif args.mode == "DUMP_PAIRWISE_CACHE_TO_LEARNIT_TABULAR":
        sim_matrix_path = args.sim_matrix_path
        output_path = args.output_path
        cutoff = args.cutoff
        sim_matrix = dict(
            np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())

        dump_pairwise_to_learnit_tabular(sim_matrix,output_path,cutoff)
    else:
        raise NotImplemented("Unsupported mode {}".format(args.mode))


if __name__ == "__main__":
    main()
