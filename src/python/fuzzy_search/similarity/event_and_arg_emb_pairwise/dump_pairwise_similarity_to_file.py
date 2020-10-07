import logging
import numpy as np
logger = logging.getLogger(__name__)


def get_name_match_score(query_names, result_names):
    """
    keys in the two input dicts are names of argument similarity modes belonging
    to the Feature.  Values are lists of actor names associated with that mode.
    e.g. {
        "arguments.bert": ["Vladimir Putin", "Russian Federation"],
        "arguments.Active_Actor_Argument_model": ["Vladimir Putin"],
        "arguments.Location_Argument_model": ["Russian Federation"]
        }
    """
    match_score = 0  # measure of similarity between query and result names
    all_result_names = set()
    for names in result_names.values():
        all_result_names.update(names)

    for mode, names in query_names.items():
        for name in set(names):
            # match score increased if query name present anywhere in result
            if name in all_result_names:
                match_score += 1
            # bonus for query name with same mode
            if name in result_names.get(mode, []):
                match_score += 1
    return match_score


def build_results_buffer_from_dict(match_count_to_buffer):
    ret = []
    for match_count, buf in sorted(
            match_count_to_buffer.items(), key=lambda x: x[0], reverse=True):
        ret.extend(sorted(buf, key=lambda x: x[1]))
    return ret


def dump_pairwise_to_file(list_of_features,
                          sim_matrix,
                          output_file,
                          cutoff,
                          using_argument_names):
    feature_id_to_feature = {f.feature_id: f for f in list_of_features}

    with open(output_file, 'w') as wfp:
        for src_feature_id, dst_feature_annoy_idx_to_score in (
                sim_matrix.items()):

            observed_neighbor_texts = set()

            wfp.write("###\tOriginal: {}\n".format(
                feature_id_to_feature[src_feature_id]
                .aux['originalText']
                .replace("\t", " ")
                .replace("\n", " ")))

            # ignores the features actually chosen to build similarity matrix,
            # instead using the full set of all argument feature names and the
            # actor names associated with them.
            if using_argument_names:
                src_names = (feature_id_to_feature[src_feature_id]
                             .aux['argument_names'])
                dst_sent_score_bufs = {}
                for dst_feature_id, score in dst_feature_annoy_idx_to_score.items():

                    text = (feature_id_to_feature[dst_feature_id]
                            .aux['originalText'])
                    if text in observed_neighbor_texts:
                        continue

                    dst_names = (feature_id_to_feature[dst_feature_id]
                                 .aux['argument_names'])
                    match_score = get_name_match_score(src_names, dst_names)
                    dst_text = ("ArgNameScore: {}\t{}".format(
                        match_score, text))
                    dst_sent_score_bufs.setdefault(match_score, list()).append(
                        (dst_text, score))
                    observed_neighbor_texts.add(text)

                dst_sent_score_buf = build_results_buffer_from_dict(
                    dst_sent_score_bufs)

            else:
                dst_sent_score_buf = list()
                for dst_feature_id, score in dst_feature_annoy_idx_to_score.items():

                    text = (feature_id_to_feature[dst_feature_id]
                            .aux['originalText'])
                    if text in observed_neighbor_texts:
                        continue

                    dst_sent_score_buf.append((text, score))
                    observed_neighbor_texts.add(text)

                dst_sent_score_buf = sorted(dst_sent_score_buf, key=lambda x: x[1])

            for dst_sent, score in dst_sent_score_buf[:cutoff]:
                wfp.write("!!!\tDest: Score:{:.4f} {}\n".format(
                    score, dst_sent.replace("\t", " ").replace("\n", " ")))
