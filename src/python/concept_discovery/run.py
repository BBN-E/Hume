import argparse
from collections import defaultdict
import json

import numpy as np

from utils import EventMentionInstanceIdentifierTokenIdxBase, sentence_jsonl_reader, cbc_cluster_reader, \
    read_saliency_list


class Label(object):
    def __init__(self, label, score, correctness=0):
        self.label = label
        self.score = score
        self.correctness = correctness

    def to_json(self):
        d = dict()
        d['label'] = self.label
        d['score'] = self.score
        d['correctness'] = self.correctness
        return d

    @staticmethod
    def from_json(label_dict):
        return Label(label_dict['label'], label_dict['score'], label_dict['correctness'])


class Cluster(object):
    def __init__(self, cluster_id):
        self.id = cluster_id
        self.score = None
        self.coherence_score = None
        self.novelty_score = None
        self.word_counts = defaultdict(int)
        """:type: dict[str]"""
        self.comments = []
        """:type: list[str]"""
        self.similarity_to_ontology_nodes = []
        """:type: list[Label]"""
        self.overlap_ontology_nodes = []    # populated if cluster overlaps with existing node, e.g. /wm/process/communicate
        """:type: list[str]"""
        self.novel_ontology_nodes = []      # populated if cluster is novel. Points to potential parent node, e.g. /wm/process/communicate
        """:type: list[str]"""
        self.exists_in_ontology = False
        """:type: boolean"""

    def add_similarity_to_ontology_node(self, node_path, score):
        self.similarity_to_ontology_nodes.append(Label(node_path, score))

    def add_word(self, word):
        self.word_counts[word.lower()] += 1

    def to_json(self):
        d = dict()
        d['id'] = self.id
        d['score'] = self.score
        # d['coherence_score'] = self.coherence_score
        # d['novelty_score'] = self.novelty_score
        d['words_string'] = ' '.join(w for w, _ in sorted(self.word_counts.items(), key=lambda item: item[1], reverse=True))
        d['cluster_name'] = d['words_string'].split(' ')[0]
        d['comments'] = self.comments
        d['similarity_to_ontology_nodes'] = []
        for label in self.similarity_to_ontology_nodes:
            d['similarity_to_ontology_nodes'].append(label.to_json())
        d['overlap_ontology_nodes'] = self.overlap_ontology_nodes
        d['novel_ontology_nodes'] = self.novel_ontology_nodes
        d['exists_in_ontology'] = int(self.exists_in_ontology is True)
        return d

    @staticmethod
    def from_json(cluster_dict):
        cluster = Cluster(cluster_dict['id'])
        for w in cluster_dict['words_string'].split(' '):
            cluster.add_word(w)
        if 'score' in cluster_dict:
            cluster.score = float(cluster_dict['score'])
        if 'comments' in cluster_dict:
            cluster.comments = cluster_dict['comments']
        if 'similarity_to_ontology_nodes' in cluster_dict:
            for label in cluster_dict['similarity_to_ontology_nodes']:
                cluster.similarity_to_ontology_nodes.append(Label.from_json(label))
        if 'overlap_ontology_nodes' in cluster_dict:
            cluster.overlap_ontology_nodes = cluster_dict['overlap_ontology_nodes']
        if 'novel_overlap_nodes' in cluster_dict:
            cluster.novel_ontology_nodes = cluster_dict['novel_overlap_nodes']
        if 'novelty_score' in cluster_dict:
            cluster.novelty_score = float(cluster_dict['novelty_score'])
        # if there's no coherence_score, assume it's the same as score
        if 'coherence_score' in cluster_dict:
            cluster.coherence_score = float(cluster_dict['coherence_score'])
        else:
            cluster.coherence_score = cluster.score
        if 'exists_in_ontology' in cluster_dict:
            cluster.exists_in_ontology = bool(cluster_dict['exists_in_ontology'])
        return cluster


def read_cluster_annotation(filepath):
    ret = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    i = 0
    while i < len(lines):
        if len(lines[i]) > 0:
            tokens = lines[i].split(' ')
            assert tokens[1].isdigit()  # cluster ID

            cluster = Cluster(tokens[1])
            cluster.score = float(tokens[0])
            # assume coherence_score is the same as score
            cluster.coherence_score = cluster.score
            cluster.words = tokens[2:]

            while (i + 1) < len(lines) and lines[i+1].startswith('#'):
                i = i + 1
                cluster.comments.append(lines[i])
            ret.append(cluster)

        i = i + 1

    return ret


def read_cluster_file(sentence_jsonl_path, cbc_cluster_path):
    doc_id_sent_id_to_sent_en = sentence_jsonl_reader(sentence_jsonl_path)
    ret = []
    with open(cbc_cluster_path) as fp:
        for i in fp:
            i = i.strip()
            cluster_id, score, *rest = i.split(" ")
            cluster = Cluster(cluster_id)
            cluster.score = score
            # assume coherence_score is the same as score
            cluster.coherence_score = score
            for node in rest:
                en = EventMentionInstanceIdentifierTokenIdxBase.from_short_id_str(node)
                sentence_en = doc_id_sent_id_to_sent_en[(en.doc_id, en.sentence_id)]
                token_start_idx = en.trigger_idx_span.start_offset
                token_end_idx = en.trigger_idx_span.end_offset
                word = '_'.join(sentence_en['sentenceInfo']['token'][token_start_idx:token_end_idx+1])
                cluster.add_word(word)

            ret.append(cluster)
    return ret


def read_cluster_json_file(cluster_json_file):
    with open(cluster_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Cluster.from_json(d) for d in data]


def read_cluster_ids_from_file(id_list_path):
    results = set()
    with open(id_list_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            results.add(line.strip())
    return results


def read_static_cluster_file(cbc_cluster_path):
    ret = []
    with open(cbc_cluster_path) as fp:
        for i in fp:
            i = i.strip()
            cluster_id, score, *rest = i.split(" ")
            cluster = Cluster(cluster_id)
            cluster.score = score
            cluster.words = rest
            ret.append(cluster)
    return ret


def read_cluster_to_ontology_similarity(filepath):
    ret = defaultdict(list)
    """:type: dict[str, list[Label]]"""

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            tokens = line.strip().split(',')
            assert len(tokens) == 21
            cluster_id = tokens[0]
            for node, distance in zip(tokens[1:11], tokens[11:]):
                distance = float(distance)
                cos_sim = 1 - distance * distance / 2   # convert angular distance to cosine_similarity, ref: https://github.com/spotify/annoy/issues/112
                ret[cluster_id].append(Label(node, cos_sim))

    return ret


def write_clusters_to_file(clusters, outfile_path):
    cluster_json_list = [c.to_json() for c in sorted(clusters, key=lambda x:float(x.score), reverse=True)]
    with open(outfile_path, 'w', encoding='utf-8') as o:
        o.write(json.dumps(cluster_json_list, indent=4, ensure_ascii=False))


def set_cluster_similarity_scores(clusters, cluster_to_ontology_similarity_dict):
    for c in clusters:
        c.similarity_to_ontology_nodes = cluster_to_ontology_similarity_dict[c.id]
        c.novelty_score = max([label.score for label in c.similarity_to_ontology_nodes])


def compute_rank_scores(clusters):
    clusters_by_id = sorted(clusters, key=lambda x: x.id)

    coherence_scores = np.array([c.coherence_score for c in clusters_by_id]).astype(float)
    novelty_scores = np.array([c.novelty_score for c in clusters_by_id]).astype(float)
    # print(coherence_scores)
    # print(novelty_scores)

    coherence_z_scores = (coherence_scores - np.nanmean(coherence_scores)) / np.nanstd(coherence_scores)
    novelty_z_scores = (novelty_scores - np.nanmean(novelty_scores)) / np.nanstd(novelty_scores)
    # print(coherence_z_scores)
    # print(novelty_z_scores)

    rank_scores = np.nan_to_num(np.add(coherence_z_scores, novelty_z_scores * -1))
    # print(rank_scores)

    for i, cluster in enumerate(clusters_by_id):
        cluster.score = rank_scores[i]


def compute_precision_at_topn(clusters, n):
    rel = 0
    results = sorted(clusters, key=lambda x: float(x.score), reverse=True)
    for c in results[:n]:
        # print('score {} exists {}'.format(c.score, c.exists_in_ontology))
        if not c.exists_in_ontology:
            rel += 1
    print('precision at {}: {:.2f}'.format(n, rel / n))


def prune_cluster_file(cluster_mention_path, sentence_jsonl_path, cluster_annotation_path, output_file):
    cluster_id_to_records = cbc_cluster_reader(cluster_mention_path)
    doc_id_sent_id_to_sent_en = sentence_jsonl_reader(sentence_jsonl_path)

    clusters = read_cluster_annotation(cluster_annotation_path)
    id_to_cluster = dict()
    for cluster in clusters:
        id_to_cluster[cluster.id] = cluster

    outlines = []
    for cluster_id in sorted(cluster_id_to_records):
        selected_ens = []

        if cluster_id in id_to_cluster:     # only interested in certain clusters
            cluster = id_to_cluster[cluster_id]
            target_words = cluster.words[0:10]      # only interested in these words
            print(cluster_id, target_words)

            for en in cluster_id_to_records[cluster_id]:
                """:type: EventMentionInstanceIdentifierTokenIdxBase"""
                doc_id = en.doc_id
                sentence_id = int(en.sentence_id)
                start_token_index = int(en.trigger_idx_span.start_offset)
                end_token_index = int(en.trigger_idx_span.end_offset)
                assert (doc_id, sentence_id) in doc_id_sent_id_to_sent_en
                # if (doc_id, sentence_id) not in doc_id_sent_id_to_sent_en:
                #     print('Cannot find doc_id,sentence_id = {},{} in doc_id_sent_id_to_sent_en'.format(en.doc_id, en.sentence_id))
                #     continue

                d = doc_id_sent_id_to_sent_en[(doc_id, sentence_id)]
                tokens = d['sentenceInfo']['token']
                tokens_string = '_'.join(t for t in tokens[start_token_index:end_token_index+1])
                if tokens_string.lower() in target_words:
                    selected_ens.append(en)
        else:
            selected_ens = cluster_id_to_records[cluster_id]

        out_tokens = []
        for en in selected_ens:
            out_tokens.append('{}|{}|{}|{}'.format(en.doc_id, en.sentence_id,
                                                   en.trigger_idx_span.start_offset,
                                                   en.trigger_idx_span.end_offset))

        outlines.append('{} _ {}'.format(out_tokens[0], ' '.join(t for t in out_tokens[1:])))

    with open(output_file, 'w', encoding='utf-8') as o:
        for line in outlines:
            o.write(line)
            o.write('\n')


def filter_clusters(clusters, list_of_ids_to_filter):
    return [c for c in clusters if c.id not in list_of_ids_to_filter]


def reverse_filter_clusters(clusters, list_of_ids_to_keep):
    return [c for c in clusters if c.id in list_of_ids_to_keep]


def analyze_overlap_with_filtered_clusters(cluster_json_path, filtered_clusters_json):
    clusters = read_cluster_json_file(cluster_json_path)
    bad_clusters = read_cluster_json_file(filtered_clusters_json)

    filtered_terms = set()
    for f in bad_clusters:
        for w in f.word_counts.keys():
            filtered_terms.add(w)

    n_clusters_filtered = 0
    for c in clusters:
        n_total = len(c.word_counts.keys())
        n_filtered = 0
        for w in c.word_counts.keys():
            if w in filtered_terms:
                n_filtered += 1
        filtered_ratio = float(n_filtered / n_total)
        if filtered_ratio > 0.1:
            print("{} {}".format(filtered_ratio, ' '.join(c.word_counts.keys())))
            n_clusters_filtered += 1
    print("Total: {}".format(n_clusters_filtered))


def identify_clusters_to_filter_by_example(clusters, examples_to_filter_json):
    result_ids = []
    bad_clusters = read_cluster_json_file(examples_to_filter_json)

    filtered_terms = set()
    for f in bad_clusters:
        for w in f.word_counts.keys():
            filtered_terms.add(w)

    n_clusters_filtered = 0
    for c in clusters:
        n_total = len(c.word_counts.keys())
        n_filtered = 0
        for w in c.word_counts.keys():
            if w in filtered_terms:
                n_filtered += 1
        filtered_ratio = float(n_filtered / n_total)
        if filtered_ratio > 0.25:
            result_ids.append(c.id)
            # print("{} {}".format(filtered_ratio, ' '.join(c.word_counts.keys())))
            n_clusters_filtered += 1
    print("Total filtered by example: {}".format(n_clusters_filtered))
    return result_ids


def identify_clusters_to_filter_by_heuristic(clusters):
    result_ids = []
    n_clusters_filtered = 0
    for c in clusters:
        n_total = len(c.word_counts.keys())
        n_short_words = 0
        for w in c.word_counts.keys():
            if len(w) <= 3:
                n_short_words += 1
        short_word_ratio = float(n_short_words / n_total)
        if short_word_ratio > 0.75:
            result_ids.append(c.id)
            # print("{} {}".format(short_word_ratio, ' '.join(c.word_counts.keys())))
            n_clusters_filtered += 1
    print("Total filtered by heuristic: {}".format(n_clusters_filtered))
    return result_ids


def compare_clusters_top_3(cluster_json_path_1, cluster_json_path_2):
    clusters_1 = read_cluster_json_file(cluster_json_path_1)
    clusters_2 = read_cluster_json_file(cluster_json_path_2)

    clusters_by_id_1 = sorted(clusters_1, key=lambda x: x.id)
    clusters_by_id_2 = sorted(clusters_2, key=lambda x: x.id)

    assert(len(clusters_by_id_1) == len(clusters_by_id_2))

    print("Total clusters: {}".format(len(clusters_by_id_1)))
    total_changed = 0
    for c1, c2 in zip(clusters_by_id_1, clusters_by_id_2):
        changed = False
        assert(c1.id == c2.id)
        l1 = set()
        l2 = set()
        for i in range(0, 3):
            l1.add(c1.similarity_to_ontology_nodes[i].label)
            l2.add(c2.similarity_to_ontology_nodes[i].label)
            if c1.similarity_to_ontology_nodes[i].label != c2.similarity_to_ontology_nodes[i].label:
                changed = True
        # if changed:
        if len(l1.difference(l2)) != 0:
            # print("{} {}".format(l1, l2))
            total_changed += 1

    print("Total changed: {}".format(total_changed))


def analyze_cluster_to_topn_annotation_file(annotation_path, old_ontology_path):
    correct_scores = []
    correct_ranks = []

    old_path_score_max = []
    old_path_score_all = []

    positive_annotation_count = 0
    number_of_clusters_only_mapped_to_new_nodes = 0

    old_ontology_paths = set()
    with open(old_ontology_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            old_ontology_paths.add(line.strip())

    with open(annotation_path, 'r', encoding='utf-8') as f:
        datas = json.load(f)

    P = 0
    C = 0
    novel_threshold = 0.8
    for d in datas:
        labels = []
        for prediction in d['similarity_to_ontology_nodes']:
            labels.append(Label(prediction['label'], prediction['score'], prediction['correctness']))

        for i, label in enumerate(labels):
            if label.correctness == 1:
                correct_scores.append(label.score)
                correct_ranks.append(i+1)
                positive_annotation_count += 1

        # we now check whether all the correct paths are new paths
        labels_with_old_paths = []
        for label in labels:
            if label.label in old_ontology_paths:
                labels_with_old_paths.append(label)

        has_positive_annotation = False
        for label in labels_with_old_paths:
            if label.correctness == 1:
                has_positive_annotation = True
                break

        if labels_with_old_paths[0].score < novel_threshold:
            P += 1

        if not has_positive_annotation:     # this cluster is only mapped to new nodes (i.e. this is a novel cluster)
            number_of_clusters_only_mapped_to_new_nodes += 1
            old_path_score_max.append(labels_with_old_paths[0].score)
            for label in labels_with_old_paths:
                old_path_score_all.append(label.score)
            if labels_with_old_paths[0].score < novel_threshold:
                C += 1

    print('#clusters in total:', len(datas))
    print('average number of positive annotations per cluster: %.2f' % (float(positive_annotation_count)/len(datas)))

    average_score = np.mean(correct_scores)
    average_rank = np.mean(correct_ranks)
    print('average score: %.2f' % average_score)
    print('average rank: %.1f' % average_rank)

    print('#clusters only mapped to new nodes:', number_of_clusters_only_mapped_to_new_nodes)
    print('old_path_score_max_average: %.2f' % (np.mean(old_path_score_max)))   # and among the above clusters, ...
    print('old_path_score_all_average: %.2f' % (np.mean(old_path_score_all)))   # and among the above clusters, ...

    print('Novel cluster Prec=%d/%d=%.2f Rec=%d/%d=%.2f' % (C, P, float(C)/P, C,
                                                            number_of_clusters_only_mapped_to_new_nodes,
                                                            float(C)/number_of_clusters_only_mapped_to_new_nodes))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True)
    parser.add_argument('--infile')
    parser.add_argument('--outdir')
    parser.add_argument('--cluster-file', required=False)
    parser.add_argument('--sentence-file', required=False)
    parser.add_argument('--outfile', required=False)
    parser.add_argument('--cluster-to-ontology-sim-file', required=False)
    parser.add_argument('--remaining_clusters_file', required=False)
    parser.add_argument('--filter_clusters_by_id', required=False)
    parser.add_argument('--filter_clusters_by_example_file', required=False)
    parser.add_argument('--filter_clusters_by_heuristic', action="store_true")
    parser.add_argument('--annotation-file', required=False)
    parser.add_argument('--cluster-file-1', required=False)
    parser.add_argument('--cluster-file-2', required=False)
    parser.add_argument('--ontology', required=False)
    args = parser.parse_args()

    if args.mode == 'cluster_to_topn_annotation_file':
        all_clusters = read_cluster_file(args.sentence_file, args.cluster_file)
        if args.cluster_to_ontology_sim_file is not None:
            cluster_to_ontology_sim = read_cluster_to_ontology_similarity(args.cluster_to_ontology_sim_file)
        else:
            cluster_to_ontology_sim = dict()
        set_cluster_similarity_scores(all_clusters, cluster_to_ontology_sim)
        compute_rank_scores(all_clusters)
        if args.remaining_clusters_file is not None:
            ids_to_keep = read_cluster_ids_from_file(args.remaining_clusters_file)
            all_clusters = reverse_filter_clusters(all_clusters, ids_to_keep)
        if args.filter_clusters_by_id is not None:
            ids_to_filter = read_cluster_ids_from_file(args.filter_clusters_by_id)
            all_clusters = filter_clusters(all_clusters, ids_to_filter)
        if args.filter_clusters_by_example_file is not None:
            ids_to_filter = identify_clusters_to_filter_by_example(all_clusters, args.filter_clusters_by_example_file)
            all_clusters = filter_clusters(all_clusters, ids_to_filter)
        if args.filter_clusters_by_heuristic:
            ids_to_filter = identify_clusters_to_filter_by_heuristic(all_clusters)
            all_clusters = filter_clusters(all_clusters, ids_to_filter)
        write_clusters_to_file(all_clusters, args.outfile)

    elif args.mode == 'compute_precision_at_topn':
        all_clusters = read_cluster_json_file(args.annotation_file)
        cluster_to_ontology_sim = read_cluster_to_ontology_similarity(args.cluster_to_ontology_sim_file)
        set_cluster_similarity_scores(all_clusters, cluster_to_ontology_sim)
        compute_rank_scores(all_clusters)
        compute_precision_at_topn(all_clusters, 50)
        compute_precision_at_topn(all_clusters, 100)
        compute_precision_at_topn(all_clusters, 150)
        compute_precision_at_topn(all_clusters, 200)
        compute_precision_at_topn(all_clusters, 250)

    elif args.mode == 'analyze_cluster_to_topn_annotation_file':
        analyze_cluster_to_topn_annotation_file(args.annotation_file, args.ontology)

    elif args.mode == 'prune_cluster_file':
        prune_cluster_file(args.cluster_file, args.sentence_file, args.annotation_file, args.outfile)

    elif args.mode == 'filter_cluster_file':
        all_clusters = read_cluster_json_file(args.cluster_file)
        print("Total clusters before filtering: {}".format(len(all_clusters)))
        if args.filter_clusters_by_example_file is not None:
            ids_to_filter_part1 = set(identify_clusters_to_filter_by_example(all_clusters, args.filter_clusters_by_example_file))
            ids_to_filter_part2 = set(identify_clusters_to_filter_by_heuristic(all_clusters))
            ids_to_filter = ids_to_filter_part1.union(ids_to_filter_part2)
            print("Total filtered: {}".format(len(ids_to_filter)))
        else:
            ids_to_filter = read_cluster_ids_from_file(args.filter_clusters_by_id)
        filtered_clusters = filter_clusters(all_clusters, ids_to_filter)
        print("Total remaining: {}".format(len(filtered_clusters)))
        write_clusters_to_file(filtered_clusters, args.outfile)

    elif args.mode == 'analyze_filtered_clusters':
        analyze_overlap_with_filtered_clusters(args.cluster_file_1, args.cluster_file_2)

    elif args.mode == 'compare_clusters_top_3':
        compare_clusters_top_3(args.cluster_file_1, args.cluster_file_2)

