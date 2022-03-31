import json
import numpy as np
import os
import sys

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from similarity.event_and_arg_emb_pairwise.dumper.dump_similarity_to_file import dump_pairwise_to_file
from similarity.event_and_arg_emb_pairwise.dumper.dump_pairwise_similarity_to_learnit_tabular import \
    dump_pairwise_to_learnit_tabular
from similarity.event_and_arg_emb_pairwise.config import Config
from similarity.event_and_arg_emb_pairwise.dumper.dumper_two_column_similarity import dump_pairwise_to_two_column_file
from similarity.event_and_arg_emb_pairwise.dumper.dump_two_column_similarity_typed import \
    dump_pairwise_to_two_column_file_typed
from similarity.event_and_arg_emb_pairwise.dumper.dump_brandeis_interchangeable import \
    dump_pairwise_to_two_column_brandeis
from similarity.event_and_arg_emb_pairwise.dumper.dump_ecb_plus_nlplingo import dump_ecb_plus_nlplingo


def main(name, args):
    if name == "FileDumper":
        query_feature_list = args.query_feature_list
        index_feature_list = args.index_feature_list
        input_sim_matrix_list = args.input_sim_matrix_list
        output_path = args.output_path
        cutoff = args.cutoff
        use_arg_names = False
        if args.use_argument_names and args.use_argument_names.lower() == "true":
            use_arg_names = True

        list_features_all = list()

        with open(query_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)
        with open(index_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)

        sim_matrix_path_list = list()
        with open(input_sim_matrix_list) as fp:
            for i in fp:
                i = i.strip()
                sim_matrix_path_list.append(i)

        with open(os.path.join(output_path, 'dump.log'), 'w') as fp:
            pass
        for sim_matrix_path in sim_matrix_path_list:
            sim_matrix = dict(
                np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
            dump_pairwise_to_file(
                list_features_all,
                sim_matrix,
                os.path.join(output_path, 'dump.log'),
                cutoff,
                use_arg_names)

    elif name == "LearnItTabularDumper":
        input_sim_matrix_list = args.input_sim_matrix_list
        output_path = args.output_path
        cutoff = args.cutoff
        sim_matrix_path_list = list()
        with open(input_sim_matrix_list) as fp:
            for i in fp:
                i = i.strip()
                sim_matrix_path_list.append(i)
        for idx, sim_matrix_path in enumerate(sim_matrix_path_list):
            sim_matrix = dict(
                np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
            dump_pairwise_to_learnit_tabular(sim_matrix, output_path, cutoff)

    elif name == "TwoColumnDumper":
        input_sim_matrix_list = args.input_sim_matrix_list
        output_path = args.output_path
        cutoff = args.cutoff
        sim_matrix_path_list = list()
        with open(input_sim_matrix_list) as fp:
            for i in fp:
                i = i.strip()
                sim_matrix_path_list.append(i)
        for sim_matrix_path in sim_matrix_path_list:
            sim_matrix = dict(
                np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
            dump_pairwise_to_two_column_file(
                sim_matrix,
                os.path.join(output_path),
                cutoff)
    elif name == "TwoColumnTypedDumper":
        query_feature_list = args.query_feature_list
        index_feature_list = args.index_feature_list
        input_sim_matrix_list = args.input_sim_matrix_list
        output_path = args.output_path
        cutoff = args.cutoff
        list_features_all = list()

        with open(query_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)
        with open(index_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)

        sim_matrix_path_list = list()
        with open(input_sim_matrix_list) as fp:
            for i in fp:
                i = i.strip()
                sim_matrix_path_list.append(i)
        for sim_matrix_path in sim_matrix_path_list:
            sim_matrix = dict(
                np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
            dump_pairwise_to_two_column_file_typed(list_features_all,
                                                   sim_matrix,
                                                   output_path,
                                                   cutoff)
    elif name == "TwoColumnTypedDumperBrandeis":
        query_feature_list = args.query_feature_list
        index_feature_list = args.index_feature_list
        input_sim_matrix_list = args.input_sim_matrix_list
        output_path = args.output_path
        cutoff = args.cutoff
        list_features_all = list()

        # with open(query_feature_list) as fp:
        #     for i in fp:
        #         i = i.strip()
        #         features = np.load(i, allow_pickle=True)["features"]
        #         for feature in features:
        #             feature.features = None
        #             list_features_all.append(feature)
        with open(index_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)
        sim_matrix_path_list = list()
        with open(input_sim_matrix_list) as fp:
            for i in fp:
                i = i.strip()
                sim_matrix_path_list.append(i)
        for sim_matrix_path in sim_matrix_path_list:
            sim_matrix = dict(
                np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
            dump_pairwise_to_two_column_brandeis(list_features_all,
                                                 sim_matrix,
                                                 output_path,
                                                 cutoff)
    elif name == "DumpECBPlusNLPLingo":
        query_feature_list = args.query_feature_list
        index_feature_list = args.index_feature_list
        input_sim_matrix_list = args.input_sim_matrix_list
        output_path = args.output_path
        cutoff = args.cutoff
        list_features_all = list()

        # with open(query_feature_list) as fp:
        #     for i in fp:
        #         i = i.strip()
        #         features = np.load(i, allow_pickle=True)["features"]
        #         for feature in features:
        #             feature.features = None
        #             list_features_all.append(feature)
        with open(index_feature_list) as fp:
            for i in fp:
                i = i.strip()
                features = np.load(i, allow_pickle=True)["features"]
                for feature in features:
                    feature.features = None
                    list_features_all.append(feature)
        sim_matrix_path_list = list()
        with open(input_sim_matrix_list) as fp:
            for i in fp:
                i = i.strip()
                sim_matrix_path_list.append(i)
        for sim_matrix_path in sim_matrix_path_list:
            sim_matrix = dict(
                np.load(sim_matrix_path, allow_pickle=True)["sim_matrix"].item())
            dump_ecb_plus_nlplingo(list_features_all,
                                   sim_matrix,
                                   output_path,
                                   cutoff)


if __name__ == "__main__":
    json_path = sys.argv[1]
    dumper_id = sys.argv[2]
    with open(json_path) as fp:
        j = json.load(fp)
    c = Config()
    c.update_using_dict(j)
    dumper_id_to_dumper = {i.id: i for i in c.dumpers}
    dumper_config = dumper_id_to_dumper[dumper_id]
    name = dumper_config.name
    args = dumper_config.args
    main(name, args)
