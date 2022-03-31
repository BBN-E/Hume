import argparse
from collections import defaultdict

import pandas as pd


def get_cosine_similarity(angular_score):
    return 1 - angular_score * angular_score / 2


def get_parent_node(node_name):
    parts = node_name.split("/")
    return "/".join(parts[:-1])


def novelty_judgement_at_threshold(annotation_dict, prediction_dict, threshold):
    novel = list()
    overlapping = list()
    for cluster, ann in annotation_dict.items():
        predictions = prediction_dict[cluster]
        cosine_sim = get_cosine_similarity(float(predictions[0]['score']))
        if cosine_sim < threshold:
            novel.append(cluster)
        else:
            overlapping.append(cluster)
    return novel, overlapping


def prob_correct_node_in_top_n(cluster_ids, n, annotation_dict, prediction_dict):
    n_correct = 0
    for cluster in cluster_ids:
        node_ann = annotation_dict[cluster]['node']
        predictions = prediction_dict[cluster]
        for p in predictions[:n]:
            if p['node'] == node_ann:
                n_correct += 1
                break
    # print("Num clusters: {} Correct: {}".format(len(cluster_ids), n_correct))
    return n_correct / len(cluster_ids)


def prob_parent_node_in_top_n(cluster_ids, n, annotation_dict, prediction_dict):
    n_correct = 0
    for cluster in cluster_ids:
        node_ann = annotation_dict[cluster]['node']
        parent_ann = get_parent_node(node_ann)
        predictions = prediction_dict[cluster]
        for p in predictions[:n]:
            if p['node'] == parent_ann:
                n_correct += 1
                break
    # print("Num clusters: {} Correct: {}".format(len(cluster_ids), n_correct))
    return n_correct / len(cluster_ids)


def novelty_prob_at_threshold(annotation_dict, prediction_dict, threshold):
    predicted_novel = 0
    true_novel = 0
    for cluster, ann in annotation_dict.items():
        predictions = prediction_dict[cluster]
        cosine_sim = get_cosine_similarity(float(predictions[0]['score']))
        if cosine_sim < threshold:
            predicted_novel += 1
            if ann['exists'] == 0:
                true_novel += 1
    # print("Cosine sim: {} Predicted novel: {} True novel: {}".format(cosine_sim, predicted_novel, true_novel))
    return float(true_novel / predicted_novel)


def main(annotation_csv_file, prediction_csv_file):
    annotation_df = pd.read_csv(annotation_csv_file)
    prediction_df = pd.read_csv(prediction_csv_file)

    predictions_by_cluster = defaultdict(list)
    annotation_by_cluster = dict()

    for row in prediction_df.itertuples():
        cluster_id = row[1]
        # print("{}".format(cluster_id))
        for i in range(0, 10):
            predictions_by_cluster[cluster_id].append({
                'node': row[i+2],
                'score': row[i+12]
            })
            # print("\t{} {}".format(row[i+2], row[i+12]))

    for idx, row in annotation_df.iterrows():
        cluster_id = row['Cluster #']
        annotation_by_cluster[cluster_id] = {
            'node': row['Annotation'],
            'exists': row['Exists?']
        }
        # print("{}\t{}\t{}\t{}".format(row['Cluster #'], row['Exists?'], row['Annotation']))

    for threshold in [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
        p = novelty_prob_at_threshold(annotation_by_cluster, predictions_by_cluster, threshold)
        print("Threshold={} P(true=novel|predicted=novel)={}".format(threshold, p))

    threshold = 0.75
    novel, overlapping = novelty_judgement_at_threshold(annotation_by_cluster ,predictions_by_cluster, threshold)
    print("\nWith Threshold={}:".format(threshold))
    print("\t{} novel nodes".format(len(novel)))
    print("\t{} overlapping node".format(len(overlapping)))

    print("\n\tFor all novel nodes:")
    for n in [1, 5, 10]:
        p = prob_parent_node_in_top_n(novel, n, annotation_by_cluster, predictions_by_cluster)
        print("\t\tN={} P(parent_node_in_top_N)={}".format(n, p))

    print("\n\tFor all overlapping nodes:")
    for n in [1, 5, 10]:
        p = prob_correct_node_in_top_n(overlapping, n, annotation_by_cluster, predictions_by_cluster)
        print("\t\tN={} P(correct_node_in_top_N)={}".format(n, p))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--analysis-csv-file', required=True)
    parser.add_argument('--neighbors-csv-file', required=True)
    args = parser.parse_args()

    main(args.analysis_csv_file, args.neighbors_csv_file)
