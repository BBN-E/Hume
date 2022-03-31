import os, sys, logging

import numpy as np

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)


from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.annoy_index_builder import annoy_index_builder
from similarity.event_and_arg_emb_pairwise.querier.weighted_querier import build_pairwise_cache
from similarity.event_and_arg_emb_pairwise.dumper.dump_similarity_to_file import dump_pairwise_to_file
from similarity.event_and_arg_emb_pairwise.utils.merge_pairwise import merge_pairwise_cache
from similarity.event_and_arg_emb_pairwise.dumper.dump_pairwise_similarity_to_learnit_tabular import dump_pairwise_to_learnit_tabular
from similarity.event_and_arg_emb_pairwise.cache_storage_adapter.annoy_storage import AnnoyAdapter
from similarity.event_and_arg_emb_pairwise.utils.common import create_file_name_to_path

logger = logging.getLogger(__name__)




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
        from similarity.event_and_arg_emb_pairwise.feature_extractor.serif_nlplingo_feature_extractor import \
            SerifNLPLingoFeatureExtractor
        serif_list = args.input_serif_list
        npz_dir = args.input_serif_npz_dir
        output_path = args.output_path
        output_prefix = args.output_prefix
        key_getter_strs = args.key_getter_str
        input_bert_npz_list = args.input_bert_npz_list

        doc_id_to_bert_npz_path = create_file_name_to_path(input_bert_npz_list,
                                                        ".npz")

        list_features_all = list()
        serif_nlplingo_feature_extractor = SerifNLPLingoFeatureExtractor(
            serif_list, npz_dir, doc_id_to_bert_npz_path, key_getter_strs)
        extracted_features = serif_nlplingo_feature_extractor.extract_features()
        list_features_all.extend(extracted_features)
        with open(os.path.join(
                output_path, output_prefix + "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    elif args.mode == "BUILD_LEARNIT_OBVERSATION_FEATURE":
        from similarity.event_and_arg_emb_pairwise.feature_extractor.learnit_obversation_ave_bert_feature_extractor import \
            LearnItObversationFeatureExtractor
        input_bert_npz_list = args.input_bert_npz_list # This is not from pipeline
        input_learnit_obversation_instance_json_file = args.input_learnit_obversation_instance_json_file
        output_path = args.output_path
        output_prefix = args.output_prefix
        learnit_obversation_feature_extractor = LearnItObversationFeatureExtractor(input_bert_npz_list,input_learnit_obversation_instance_json_file)
        feature_list = learnit_obversation_feature_extractor.extract_features()
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
                        feature.drop_features()
                    list_features_all.append(feature)
        with open(os.path.join(output_path), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    elif args.mode == "BUILD_ANNOY_INDEX":
        feature_list_path = args.input_feature_list
        annoy_metric = args.annoy_metric
        n_trees = args.n_trees
        output_path = args.output_path
        annoy_index_builder(annoy_metric, n_trees, feature_list_path,output_path)


    elif args.mode == "BUILD_PAIRWISE_CACHE":
        feature_list = args.input_feature_list
        chosen_feature_names = args.key_getter_str
        chosen_feature_weights = args.key_getter_weights
        annoy_metric = args.annoy_metric
        input_annoy_cache_path = args.input_annoy_cache_path
        threshold = args.threshold
        cutoff = args.cutoff
        output_path = args.output_path

        assert (chosen_feature_weights is None
                or len(chosen_feature_weights) == len(chosen_feature_names))

        cache_storage = AnnoyAdapter.load_storage(input_annoy_cache_path,annoy_metric,chosen_feature_names)

        list_features_all = list()
        with open(feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                list_features_all.extend(features)
        sim_matrix = build_pairwise_cache(
            chosen_feature_names,
            chosen_feature_weights,
            cache_storage,
            list_features_all,
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
