import copy
import json
import logging
import os
import zlib

import numpy as np

logger = logging.getLogger(__name__)


def parse_label_mappings(mappings_path):
    resolved_positive_event_mentions = list()
    with open(mappings_path, 'rb') as fp:
        z = json.loads(zlib.decompress(fp.read()).decode('utf-8'))
        mappings = z[1]
        label_mappings = mappings['patternInstanceMap'][1]['data'][1]
        key_id_to_key = dict()
        val_id_to_val = dict()
        for idx, k in enumerate(label_mappings['keyList'][1]):
            key_id_to_key[idx] = k
        for idx, v in enumerate(label_mappings['valList'][1]):
            val_id_to_val[idx] = v
        k_vals_map = dict()
        for idx, en in enumerate(label_mappings['entries'][1]):
            key = en[1]['key']
            vals = [v for v in en[1]['values'][1]]
            k_vals_map[key] = vals
        for k, vals in k_vals_map.items():
            learnit_instance_identifier = key_id_to_key[k]
            instance_identifier = {
                'docid': learnit_instance_identifier['docid'],
                'sent_idx': learnit_instance_identifier['sentid'],
                'trig_idx_start': learnit_instance_identifier['slot0Start'],
                'trig_idx_end': learnit_instance_identifier['slot0End']
            }
            for v in vals:
                label_pattern = val_id_to_val[v][1]
                event_type = label_pattern['relationType']['string']
                frozen_state = label_pattern['frozenState']
                if frozen_state == "FROZEN_GOOD":
                    en = copy.deepcopy(instance_identifier)
                    en['event_type'] = event_type
                    resolved_positive_event_mentions.append(en)
    return resolved_positive_event_mentions


def calculate_centriod(resolved_positive_event_mentions, npz_list, output_centroid_json_path):
    doc_id_to_mentions = dict()
    for item in resolved_positive_event_mentions:
        doc_id_to_mentions.setdefault(item['docid'], list()).append(item)

    type_to_sum = dict()
    type_to_cnt = dict()
    doc_id_in_npz_list = set()

    with open(npz_list, 'r') as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i).replace(".npz", "")
            doc_id_in_npz_list.add(doc_id)
            if doc_id in doc_id_to_mentions.keys():
                with np.load(i, allow_pickle=True) as fp2:
                    embeddings = fp2['embeddings']
                    tokens = fp2['tokens']
                    token_map = fp2['token_map']
                    for mention in doc_id_to_mentions[doc_id]:
                        sent_idx = mention['sent_idx']
                        head_token_idx_in_serif = mention['trig_idx_end']
                        event_type = mention['event_type']
                        if len(token_map[sent_idx]) < 1:
                            logger.warning(
                                "We cannot find embedding for docid:{}, sent:{}, head_token_idx:{}.".format(doc_id,
                                                                                                            sent_idx,
                                                                                                            head_token_idx_in_serif))
                            continue
                        head_token_idx_in_bert = token_map[sent_idx][head_token_idx_in_serif]
                        current_vec = embeddings[sent_idx][head_token_idx_in_bert]
                        current_sum = type_to_sum.get(event_type, np.zeros(current_vec.shape[0]))
                        current_sum += current_vec
                        type_to_sum[event_type] = current_sum
                        type_to_cnt[event_type] = type_to_cnt.get(event_type, 0) + 1
    logger.warning("We have {} docs that don't have npz from bert.".format(
        len(set(doc_id_to_mentions.keys()).difference(doc_id_in_npz_list))))
    final_type_to_vec = dict()
    for event_type in type_to_sum.keys():
        vec = np.true_divide(type_to_sum[event_type], type_to_cnt[event_type])
        # final_type_to_vec[event_type] = vec.tolist()
        final_type_to_vec[event_type] = {
            "sum":type_to_sum[event_type].tolist(),
            "cnt": type_to_cnt[event_type],
            "avg":vec.tolist()
        }
    with open(output_centroid_json_path, 'w') as fp:
        json.dump(final_type_to_vec, fp, indent=4, sort_keys=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--labeled_mappings_path", required=True)
    parser.add_argument("--npz_list_path", required=True)
    parser.add_argument("--output_json_path", required=True)

    args = parser.parse_args()
    resolved_positive_event_mentions = parse_label_mappings(args.labeled_mappings_path)
    calculate_centriod(resolved_positive_event_mentions, args.npz_list_path, args.output_json_path)
