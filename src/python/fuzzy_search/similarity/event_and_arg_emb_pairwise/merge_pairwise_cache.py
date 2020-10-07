import queue
import numpy as np


class MyPriorityQueue(queue.PriorityQueue):
    def __init__(self, size):
        super().__init__(size)

    def put_nowait(self, item):
        while True:
            try:
                super().put_nowait(item)
                return
            except queue.Full as e:
                super().get_nowait()


def merge_pairwise_cache(sim_matrix_list_path, threshold, cutoff):
    src_feature_id_to_dst_pq = dict()
    with open(sim_matrix_list_path) as fp:
        for i in fp:
            i = i.strip()
            sim_matrix = dict(
                np.load(i, allow_pickle=True)["sim_matrix"].item())
            for src_feature_id, dst_feature_id_score_pair in sim_matrix.items():
                q = src_feature_id_to_dst_pq.setdefault(src_feature_id,
                                                        MyPriorityQueue(cutoff))
                for dst_feature_id, score in dst_feature_id_score_pair.items():
                    if score < threshold:
                        q.put_nowait((-score, dst_feature_id))
    ret = dict()
    for src_feature_id, dst_score_to_feature_id in (
            src_feature_id_to_dst_pq.items()):
        d = ret.setdefault(src_feature_id, dict())
        while dst_score_to_feature_id.empty() is False:
            score_prime, dst_feature_id = dst_score_to_feature_id.get_nowait()
            d[dst_feature_id] = -score_prime
    return ret
