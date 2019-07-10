import argparse
from collections import defaultdict

from Cluster import *

class ClusterLabeler(object):
    def __init__(self):
        (self.clusters, self.member_to_clusters) = self.read_cluster_file(
            '/nfs/ld100/u10/bmin/repositories/CauseEx/util/python/causality/events/cbc.finalClustering')

    def cluster_line_to_cluster(self, line):
        tokens = line.strip().split()
        centriod = tokens[0]
        score = float(tokens[1])
        return Cluster(centriod, score, tokens[2:])


    def read_cluster_file(self, filepath):
        clusters = []
        member_to_clusters = defaultdict(set)

        with open(filepath, 'r') as f:
            for line in f:
                cluster = self.cluster_line_to_cluster(line)
                clusters.append(cluster)
                for m in cluster.members:
                    member_to_clusters[m].add(cluster)
        return (clusters, member_to_clusters)

    def get_highest_scoring_cluster(self, clusters):
        max_score = 0
        max_cluster = None

        for c in clusters:
            if c.score > max_score:
                max_score = c.score
                max_cluster = c
        return max_cluster

    def get_label(self, w):
        if w in self.member_to_clusters.keys():
            max_cluster = self.get_highest_scoring_cluster(self.member_to_clusters[w])
            print(max_cluster.to_string())
            return max_cluster.centriod
        else:
            print('%s is not a cluster member' % (w))
            return "NA"


if __name__ == "__main__":
    # example usage: python find_cluster_label.py --cluster_file cbc.finalClustering --word fund

    parser = argparse.ArgumentParser()
    parser.add_argument('--word')
    args = parser.parse_args()
    w = args.word

    clusterLabeler = ClusterLabeler()
    print("word=" + w + " , label=" + clusterLabeler.get_label(w))


