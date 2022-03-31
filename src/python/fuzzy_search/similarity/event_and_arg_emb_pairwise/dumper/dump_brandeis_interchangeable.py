import os
import logging
logger = logging.getLogger(__name__)

def dump_pairwise_to_two_column_brandeis(list_of_features,sim_matrix,
                  output_dir,
                  cutoff):

    feature_id_to_feature = {f.feature_id: f for f in list_of_features}
    covered_ids = set()
    with open(os.path.join(output_dir,"sim"),'w') as wfp:
        for src_feature_id, dst_feature_annoy_idx_to_score in (
                sim_matrix.items()):
            dst_sent_score_buf = list()
            for dst_feature_id, score in dst_feature_annoy_idx_to_score.items():
                dst_sent_score_buf.append([dst_feature_id,
                                           score])
            dst_sent_score_buf = sorted(dst_sent_score_buf, key=lambda x: x[1])[:cutoff]
            if len(dst_sent_score_buf) > 0:
                covered_ids.add(src_feature_id)
                for dst_id,dst_distance in dst_sent_score_buf:
                    covered_ids.add(dst_id)
                    src_docid = feature_id_to_feature[src_feature_id].aux["docid"]
                    src_emid = "{}_{}_{}".format(feature_id_to_feature[src_feature_id].aux["sent_id"],feature_id_to_feature[src_feature_id].aux["start_token_idx"],feature_id_to_feature[src_feature_id].aux["end_token_idx"])
                    tgt_docid = feature_id_to_feature[dst_id].aux["docid"]
                    tgt_emid = "{}_{}_{}".format(feature_id_to_feature[dst_id].aux["sent_id"],feature_id_to_feature[dst_id].aux["start_token_idx"],feature_id_to_feature[dst_id].aux["end_token_idx"])
                    wfp.write("{}\t{}\t{}\t{}\t{:.3f}\n".format(src_docid,src_emid,tgt_docid,tgt_emid,1 - dst_distance * dst_distance / 2))
    with open(os.path.join(output_dir,'vocab'),'w') as vocab_fp:
        for covered_id in covered_ids:
            vocab_fp.write("{}\n".format(covered_id))