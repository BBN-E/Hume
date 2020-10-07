import os
import sys

import numpy as np
from scipy.spatial import distance
from sklearn.metrics.pairwise import cosine_similarity

current_root = os.path.realpath(os.path.join(__file__,os.pardir))
sys.path.append(os.path.join(current_root,os.pardir,'knowledge_base'))
sys.path.append(os.path.join(current_root, os.pardir))
from internal_ontology import Ontology

from word_embeddings import WordEmbedding

def tree_iterator(root,callback):
    callback(root)
    for child in root.get_children():
        tree_iterator(child,callback)


def read_examplers(internal_ontology_path,exemplars_path,ontology_flag):
    ontology = Ontology()
    ontology.load_from_internal_yaml(internal_ontology_path)
    exemplars = ontology.load_internal_exemplars(exemplars_path)
    ontology.add_internal_exemplars(
        exemplars, None, ontology_flag)
    return ontology


def create_pairwise_base_on_exemplars(ontology):
    def build_word_pairwise_dict(pairwise_dict):
        def single_node_worker(root):
            for src_word in root.get_exemplars_without_descendants():
                for dst_word in root.get_exemplars_without_descendants():
                    for src_token in src_word.split(" "):
                        for dst_token in dst_word.split(" "):
                            pairwise_dict.setdefault(src_token.lower(), dict())[dst_token.lower()] = 1
        return single_node_worker
    pairwise_dict = dict()
    tree_iterator(ontology.get_root(),build_word_pairwise_dict(pairwise_dict))
    return pairwise_dict

def attach_unknown_words(pairwise_dict,list_of_word_list):

    with open(list_of_word_list) as fp:
        for word_list_path in fp:
            word_list_path = word_list_path.strip()
            with open(word_list_path) as fp2:
                for word in fp2:
                    word = word.strip()
                    pairwise_dict.setdefault(word, dict())[word] = 1
    return pairwise_dict


def calculate_event_centroid_using_exampler(ontology, word_embedding):
    type_to_sum = dict()
    type_to_cnt = dict()

    def update_sum_and_cnt_per_type(type_to_sum, type_to_cnt, word_embedding):
        def single_node_worker(root):
            event_type = root.get_name()
            for example_phrase in root.get_exemplars_without_descendants():
                for example_token in example_phrase.split(" "):
                    text, idx, vec = word_embedding.get_vector(example_token.lower())
                    if text is None:
                        continue
                    type_to_sum[event_type] = type_to_sum.get(event_type, np.zeros(400)) + vec
                    type_to_cnt[event_type] = type_to_cnt.get(event_type, 0) + 1

        return single_node_worker

    tree_iterator(ontology.get_root(), update_sum_and_cnt_per_type(type_to_sum, type_to_cnt, word_embedding))
    type_to_centroid = dict()
    for event_type in type_to_sum.keys():
        vec = np.true_divide(type_to_sum[event_type], type_to_cnt[event_type])
        type_to_centroid[event_type] = vec.tolist()
    return type_to_centroid


def calculate_word_to_event_centroids_distance(type_to_centroid, list_to_word_list, word_embedding):
    # Can optimize use matrix
    sorted_type = sorted(type_to_centroid.keys())
    word_to_event_emb = dict()
    with open(list_to_word_list) as fp:
        for word_list_path in fp:
            word_list_path = word_list_path.strip()
            with open(word_list_path) as fp2:
                for word in fp2:
                    word = word.strip()
                    text, idx, vec = word_embedding.get_vector(word.lower())
                    if text is None:
                        continue
                    if word in word_to_event_emb.keys():
                        continue
                    word_event_embeddings = np.zeros(len(sorted_type))
                    for evt_idx, event_type in enumerate(sorted_type):
                        event_centroid = type_to_centroid[event_type]
                        dis = distance.euclidean(vec, event_centroid)
                        word_event_embeddings[evt_idx] = dis
                    word_to_event_emb[word] = word_event_embeddings.tolist()
                    if(len(word_to_event_emb) % 50 == 0):
                        print("Finished {} words".format(len(word_to_event_emb)))
    return word_to_event_emb


def calculate_pairwise(word_to_event_emb):
    idx_to_word = dict()
    idx_to_emb = list()
    for word,vec in word_to_event_emb.items():
        idx_to_word[len(idx_to_emb)] = word
        idx_to_emb.append(vec)
    idx_to_emb = np.array(idx_to_emb)
    pairwise_res = cosine_similarity(idx_to_emb)

    return idx_to_word,pairwise_res


def build_pairwise_matrix_based_on_score(pairwise_dict):
    len_of_words = len(pairwise_dict.keys())
    idx_to_word = dict()
    word_to_idx = dict()
    word_to_similarity = [[0 for _ in range(len_of_words)] for _ in range(len_of_words)]
    sorted_words = sorted(pairwise_dict.keys())
    for idx, word in enumerate(sorted_words):
        idx_to_word[idx] = word
        word_to_idx[word] = idx

    for src_word, dst_words in pairwise_dict.items():
        for dst_word in dst_words.keys():
            word_to_similarity[word_to_idx[src_word]][word_to_idx[dst_word]] = 1

    return idx_to_word, word_to_similarity

def normalize_pairwise_output(idx_to_word,pairwise_res, output_path,threshold=0.1):

    with open(output_path, 'w') as wfp:
        for src_idx,src_word in idx_to_word.items():
            sum_of_similarity_from_src = sum(pairwise_res[src_idx])
            for dst_idx,dst_word in idx_to_word.items():
                score = pairwise_res[src_idx][dst_idx] / sum_of_similarity_from_src
                if score >= threshold:
                    wfp.write("{0}\t{1}\t{2:.4f}\n".format(src_word, dst_word, score))


def pure_0_1_based_pairwise_based_on_exampler():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ontology_root', required=True)
    parser.add_argument('--ontology_flag', required=True)
    parser.add_argument('--additional_word_list', required=True)
    parser.add_argument('--output_path', required=True)
    parser.add_argument('--embedding_npz_path', required=False)
    args = parser.parse_args()
    ontology_root = args.ontology_root
    ontology_flag = args.ontology_flag
    additional_word_list = args.additional_word_list
    output_path = args.output_path

    internal_ontology_path = os.path.join(ontology_root, 'event_ontology.yaml')
    exemplars_path = os.path.join(ontology_root, 'data_example_events.json')
    ontology = read_examplers(internal_ontology_path, exemplars_path, ontology_flag)
    pairwise_dict = create_pairwise_base_on_exemplars(ontology)
    pairwise_dict = attach_unknown_words(pairwise_dict, additional_word_list)
    idx_to_word, pairwise_res = build_pairwise_matrix_based_on_score(pairwise_dict)
    normalize_pairwise_output(idx_to_word, pairwise_res, output_path, 0.0001)


def event_embedding_based_pairwise():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--ontology_root', required=True)
    parser.add_argument('--ontology_flag', required=True)
    parser.add_argument('--additional_word_list', required=True)
    parser.add_argument('--output_path', required=True)
    parser.add_argument('--embedding_npz_path', required=True)
    args = parser.parse_args()
    ontology_root = args.ontology_root
    ontology_flag = args.ontology_flag
    additional_word_list = args.additional_word_list
    output_path = args.output_path
    embedding_npz_path = args.embedding_npz_path
    internal_ontology_path = os.path.join(ontology_root, 'event_ontology.yaml')
    exemplars_path = os.path.join(ontology_root, 'data_example_events.json')
    ontology = read_examplers(internal_ontology_path, exemplars_path, ontology_flag)
    word_embedding = WordEmbedding(embedding_npz_path, 251236, 400, ".", "the")
    type_to_centroid = calculate_event_centroid_using_exampler(ontology, word_embedding)
    word_to_event_emb = calculate_word_to_event_centroids_distance(type_to_centroid, additional_word_list,
                                                                   word_embedding)
    idx_to_word,pairwise_res = calculate_pairwise(word_to_event_emb)
    normalize_pairwise_output(idx_to_word,pairwise_res, output_path,0.1)


if __name__ == "__main__":
    pure_0_1_based_pairwise_based_on_exampler()
