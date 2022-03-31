import os
import logging
logger = logging.getLogger(__name__)

def dump_ecb_plus_nlplingo(list_of_features,sim_matrix,
                  output_dir,
                  cutoff):

    feature_id_to_feature = {f.feature_id: f for f in list_of_features}
    with open(os.path.join(output_dir, "sim"), 'w') as wfp:
        for src_feature_id, dst_feature_annoy_idx_to_score in (
                sim_matrix.items()):
            src_feature = feature_id_to_feature[src_feature_id]
            dst_sent_score_buf = list()
            for dst_feature_id, score in dst_feature_annoy_idx_to_score.items():
                dst_sent_score_buf.append([dst_feature_id,
                                           score])
            dst_sent_score_buf = sorted(dst_sent_score_buf, key=lambda x: x[1])[:cutoff]
            for idx, (dst_feature_id, score) in enumerate(dst_sent_score_buf):
                dst_feature = feature_id_to_feature[dst_feature_id]
                wfp.write("{}\t{}\t{}\t{}\n".format("{}#{}#{}".format(src_feature.aux["docid"],",".join(src_feature.aux["event_ids"]),src_feature.aux["em_id"]),"{}#{}#{}".format(dst_feature.aux["docid"],",".join(dst_feature.aux["event_ids"]),dst_feature.aux["em_id"]),1 - score * score / 2,idx))