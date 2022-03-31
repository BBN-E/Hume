import logging,gzip
logger = logging.getLogger(__name__)

def dump_pairwise_to_learnit_tabular(sim_matrix,
                  output_file,
                  cutoff):
    with gzip.open(output_file,'wb') as wfp:
        for src_feature_id, dst_feature_annoy_idx_to_score in (
                sim_matrix.items()):
            dst_sent_score_buf = list()
            for dst_feature_id, score in dst_feature_annoy_idx_to_score.items():
                dst_sent_score_buf.append([dst_feature_id,
                                           score])
            dst_sent_score_buf = sorted(dst_sent_score_buf, key=lambda x: x[1])[:cutoff]
            if len(dst_sent_score_buf) > 0:
                wfp.write("{}\t{}\n".format(src_feature_id,"\t".join("{}\t{:.4f}".format(i[0],-i[1]) for i in dst_sent_score_buf)).encode("utf-8"))