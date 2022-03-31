import os
import shutil
import logging

logger = logging.getLogger(__name__)


def dump_pairwise_to_two_column_file_typed(list_of_features,
                                           sim_matrix,
                                           output_dir,
                                           cutoff):
    feature_id_to_feature = {f.feature_id: f for f in list_of_features}

    type_to_feature_ids = dict()
    feature_id_to_types = dict()
    for feature_id, feature in feature_id_to_feature.items():
        event_type = feature.aux["event_type"]
        type_to_feature_ids.setdefault(event_type, set()).add(feature_id)
        feature_id_to_types.setdefault(feature_id, set()).add(event_type)

    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)
    event_type_to_cover_ids = dict()
    event_type_to_cover_id_pairs = dict()
    for src_feature_id, dst_feature_annoy_idx_to_score in (
            sim_matrix.items()):

        src_event_types = feature_id_to_types.get(src_feature_id, set())
        dst_event_type_to_feature_score = dict()
        for dst_feature_id, score in dst_feature_annoy_idx_to_score.items():
            dst_event_types = feature_id_to_types.get(dst_feature_id, set())
            if len(src_event_types.intersection(dst_event_types)) < 1:
                continue
            for event_type in src_event_types.intersection(dst_event_types):
                dst_event_type_to_feature_score.setdefault(event_type, list()).append([dst_feature_id, score])
        for event_type, dst_feature_id_score_pair in dst_event_type_to_feature_score.items():
            os.makedirs(os.path.join(output_dir, event_type), exist_ok=True)
            with open(os.path.join(output_dir, event_type, "sim"), 'a') as wfp:
                outputted_item_cnt = 0
                for dst_feature_id, score in sorted(dst_feature_id_score_pair, key=lambda x: x[1]):
                    covered_id_pairs = event_type_to_cover_id_pairs.get(event_type, set())
                    if (src_feature_id, dst_feature_id) in covered_id_pairs or (
                    dst_feature_id, src_feature_id) in covered_id_pairs:
                        continue

                    event_type_to_cover_id_pairs.setdefault(event_type, set()).add((src_feature_id, dst_feature_id))
                    event_type_to_cover_ids.setdefault(event_type, set()).add(src_feature_id)
                    event_type_to_cover_ids.setdefault(event_type, set()).add(dst_feature_id)
                    wfp.write("{} {} {:.3f}\n".format(src_feature_id, dst_feature_id, 1 - score * score / 2))
                    outputted_item_cnt += 1
                    if outputted_item_cnt >= cutoff:
                        break
    for event_type, cover_ids in event_type_to_cover_ids.items():
        with open(os.path.join(output_dir, event_type, "vocab"), "w") as vocab_fp:
            for covered_id in cover_ids:
                vocab_fp.write("{}\n".format(covered_id))
