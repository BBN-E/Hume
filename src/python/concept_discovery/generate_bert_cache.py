import argparse
import os
import sys
import logging
import numpy as np

from embedding_caches import BertEmbeddingCache
from utils import reading_cbc_s3_trigger_info, trigger_frequency_filter, EventMentionInstanceIdentifierTokenIdxBase,\
    AnnoyCacheAdapter, StaticWordEmbCache

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
sys.path.append(project_root)

logger = logging.getLogger(__name__)


def group_trigger_jsonl_by_docid(trigger_jsonl_path, min_freq_to_be_index, max_freq_to_be_in_bert_cache):
    logger.info("Readling trigger jsonl file")
    trigger_info = reading_cbc_s3_trigger_info(trigger_jsonl_path)
    reserved_set = trigger_frequency_filter(trigger_info, min_freq_to_be_index)
    doc_id_to_records = dict()
    word_to_cnt = dict()
    for j in trigger_info:
        if isinstance(reserved_set, set) and len(reserved_set) > 0:
            if (j['trigger'], j['triggerPosTag']) not in reserved_set:
                continue
        if word_to_cnt.get((j['trigger'], j['triggerPosTag']), 0) >= max_freq_to_be_in_bert_cache:
            continue
        en = EventMentionInstanceIdentifierTokenIdxBase.fromJSON(j)
        doc_id_to_records.setdefault(en.doc_id, set()).add(en)
        word_to_cnt[(j['trigger'], j['triggerPosTag'])] = word_to_cnt.get((j['trigger'], j['triggerPosTag']), 0) + 1
    logger.info("Finish reading trigger jsonl file")
    return doc_id_to_records


def main(trigger_jsonl_path, bert_npz_list_path, min_freq_to_be_index, max_freq_to_be_in_bert_cache, output_dir):
    doc_id_to_records = group_trigger_jsonl_by_docid(trigger_jsonl_path, min_freq_to_be_index, max_freq_to_be_in_bert_cache)
    bert_cache = BertEmbeddingCache(bert_npz_list_path)
    AnnoyCacheAdapter.build_annoy_index(doc_id_to_records, bert_cache, None, output_dir)


def static_main(trigger_jsonl_path, statics_word_emb_path, min_freq_to_be_index, _, output_dir):
    doc_id_to_records = group_trigger_jsonl_by_docid(trigger_jsonl_path, min_freq_to_be_index,
                                                     max_freq_to_be_in_bert_cache)
    npz_file = statics_word_emb_path + '.npz'
    words = list()
    word_vecs = list()
    if os.path.exists(npz_file):
        data = np.load(npz_file)
        words, word_vecs = data['words'], data['word_vec']
    word_to_word_vec = dict()
    for idx in range(len(words)):
        word = words[idx]
        word_vec = word_vecs[idx]
        word_to_word_vec[word] = word_vec
    static_cache = StaticWordEmbCache(word_to_word_vec, None)
    AnnoyCacheAdapter.build_annoy_index(doc_id_to_records, None, static_cache, output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--trigger-jsonl', required=True)
    parser.add_argument('--npz-list', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()

    min_freq_to_be_index = 2
    max_freq_to_be_in_bert_cache = 4

    main(args.trigger_jsonl, args.npz_list, min_freq_to_be_index, max_freq_to_be_in_bert_cache, args.outdir)
    # static_main(args.trigger_jsonl, statics_word_emb_path, min_freq_to_be_index, None, args.outdir)
