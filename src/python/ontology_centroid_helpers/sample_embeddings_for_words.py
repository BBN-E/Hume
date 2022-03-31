import argparse
import os
import sys
import logging
import collections
import numpy as np

from src.python.concept_discovery.embedding_caches import BertEmbeddingCache
from src.python.concept_discovery.utils import reading_cbc_s3_trigger_info, trigger_frequency_filter

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
sys.path.append(project_root)


logger = logging.getLogger(__name__)
UnarySpanIdentifier = collections.namedtuple('UnarySpanIdentifier',
                                             ['docId', 'sentenceId', 'triggerSentenceTokenizedPosition',
                                              'triggerSentenceTokenizedEndPosition', 'trigger'])


def main(trigger_jsonl_path, bert_npz_list_path, min_freq_for_index, max_freq_for_bert_cache, output_dir):
    logger.info("Readling trigger jsonl file")
    trigger_info = reading_cbc_s3_trigger_info(trigger_jsonl_path)
    reserved_set = trigger_frequency_filter(trigger_info, min_freq_for_index)
    doc_id_to_records = dict()
    word_to_cnt = dict()
    for j in trigger_info:
        if isinstance(reserved_set,set) and len(reserved_set) > 0:
            if (j['trigger'], j['triggerPosTag']) not in reserved_set:
                continue
        if word_to_cnt.get((j['trigger'], j['triggerPosTag']), 0) >= max_freq_for_bert_cache:
            continue
        en = UnarySpanIdentifier(j['docId'], j['sentenceId'], j['triggerSentenceTokenizedPosition'],
                                 j['triggerSentenceTokenizedEndPosition'], j['trigger'])
        doc_id_to_records.setdefault(en.docId, set()).add(en)
        word_to_cnt[(j['trigger'], j['triggerPosTag'])] = word_to_cnt.get((j['trigger'], j['triggerPosTag']), 0) + 1
    logger.info("Finish reading trigger jsonl file")
    word_to_embs = dict()
    bert_cache = BertEmbeddingCache(bert_npz_list_path)
    for doc_id, recs in doc_id_to_records.items():
        for rec in recs:
            if rec.triggerSentenceTokenizedPosition == rec.triggerSentenceTokenizedEndPosition:
                emb = bert_cache.get_contextual_emb_for_span(doc_id, rec.sentenceId,
                                                             rec.triggerSentenceTokenizedPosition,
                                                             rec.triggerSentenceTokenizedEndPosition)
                if emb is not None:
                    word_to_embs.setdefault(rec.trigger, list()).append(emb)
    word_to_emb_ave = dict()
    for word, embs in word_to_embs.items():
        emb_ave = np.mean(embs, axis=0)
        word_to_emb_ave[word] = emb_ave
    with open(os.path.join(output_dir, 'word_to_ave_emb.npz'), 'wb') as fp:
        np.savez_compressed(fp, word_to_emb_ave=word_to_emb_ave)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--trigger-jsonl', required=True)
    parser.add_argument('--npz-list', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()

    # scratch = '/nfs/raid88/u10/users/hqiu_ad/wm_concept_discovery_wm_p3_bbn/scratch'
    # trigger_jsonl_path = os.path.join(scratch,"trigger.ljson")
    # bert_npz_list_path = "/nfs/raid68/u15/ears/expts/48073.bbn_p3.012521.serif_bert.v1/expts/hume_test.dart.082720.wm.v1/bert/bert_npz.list"
    min_freq_to_be_index = 2
    max_freq_to_be_in_bert_cache = 5
    # output_dir = os.path.join("/nfs/raid88/u10/users/hqiu_ad/wm_concept_discovery_wm_p3_bbn","bert")
    main(args.trigger_jsonl, args.npz_list, min_freq_to_be_index, max_freq_to_be_in_bert_cache, args.outdir)
