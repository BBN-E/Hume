import os
import logging
logger = logging.getLogger(__name__)

def dump_pairwise_to_two_column_file(sim_matrix,
                  output_dir,
                  cutoff):
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
                    wfp.write("{} {} {:.3f}\n".format(src_feature_id,dst_id,1 - dst_distance * dst_distance / 2))
    with open(os.path.join(output_dir,'vocab'),'w') as vocab_fp:
        for covered_id in covered_ids:
            vocab_fp.write("{}\n".format(covered_id))