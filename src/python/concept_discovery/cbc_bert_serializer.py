import argparse
import os
import shutil

from utils import sentence_jsonl_reader


def short_id_string_to_full_id(short_id_str):
    doc_id, sent_id, start_token_idx, end_token_idx = short_id_str.split("|")
    return doc_id, int(sent_id), int(start_token_idx), int(end_token_idx)


def get_linted_sentence(doc_id, sent_id, start_token_idx, end_token_idx, doc_id_sent_id_to_sent_en):
    sentence_en = doc_id_sent_id_to_sent_en[(doc_id, sent_id)]
    ret_arr = list()
    for token_idx, token in enumerate(sentence_en['sentenceInfo']['token']):
        c = ""
        if token_idx == start_token_idx:
            c = "[" + c
        c = c + token
        if token_idx == end_token_idx:
            c = c + "]"
        ret_arr.append(c)
    return " ".join(ret_arr)


def main(sentence_jsonl_path, cbc_cluster_file, output_dir):
    doc_id_sent_id_to_sent_en = sentence_jsonl_reader(sentence_jsonl_path)
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)
    with open(cbc_cluster_file) as fp:
        for idx, i in enumerate(fp):
            i = i.strip()
            cluster_name, score, *rest = i.split(" ")
            score = float(score)
            with open(os.path.join(output_dir, "{}.cluster".format(cluster_name)), 'w') as wfp:
                wfp.write("{}\n".format(score))
                src_doc_id, src_sent_id, src_token_start_idx, src_token_end_idx = short_id_string_to_full_id(rest[0])
                wfp.write("{}\n".format(get_linted_sentence(src_doc_id, src_sent_id,
                                                            src_token_start_idx, src_token_end_idx,
                                                            doc_id_sent_id_to_sent_en)))
                for guest_node in rest:
                    dst_doc_id, dst_sent_id, dst_token_start_idx, dst_token_end_idx = \
                        short_id_string_to_full_id(guest_node)
                    wfp.write("{}\n".format(get_linted_sentence(dst_doc_id, dst_sent_id,
                                                                dst_token_start_idx, dst_token_end_idx,
                                                                doc_id_sent_id_to_sent_en)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sentence-jsonl', required=True)
    parser.add_argument('--cbc-clusters', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()

    main(args.sentence_jsonl, args.cbc_clusters, args.outdir)
