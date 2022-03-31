import argparse
import os
import sys
import shutil

from annoy_caches import AnnoyCorpusCache
from utils import EventMentionInstanceIdentifierTokenIdxBase

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
sys.path.append(project_root)


def main(corpus_cache_path, bert_npz_path, output_path):
    bert_cache = AnnoyCorpusCache(corpus_cache_path, bert_npz_path)
    shutil.rmtree(output_path, ignore_errors=True)
    os.makedirs(output_path, exist_ok=True)
    vocab_path = os.path.join(output_path, 'vocab')
    sim_path = os.path.join(output_path, 'sim')

    vocab_set = set()
    with open(sim_path, 'w') as wfp:
        for en_counter, en_short_id in enumerate(bert_cache.en_to_annoy_idx.keys()):
            en = EventMentionInstanceIdentifierTokenIdxBase.from_short_id_str(en_short_id)
            dsts = bert_cache.find_nn(en)
            if len(dsts) > 0:
                vocab_set.add(en_short_id)
                for dst_en in dsts:
                    dst_short_id = dst_en['dst'].to_short_id_str()
                    vocab_set.add(dst_short_id)
                    angular_score = dst_en['score']
                    cosine_similarity = 1 - angular_score * angular_score / 2
                    wfp.write("{} {} {:.3f}\n".format(en_short_id, dst_short_id, cosine_similarity))
            if (en_counter % 500)==0:
                print('Processed {}/{}'.format(str(en_counter), len(bert_cache.en_to_annoy_idx.keys())))

    with open(vocab_path, 'w') as wfp:
        for v in vocab_set:
            wfp.write("{}\n".format(v))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus-cache', required=True)
    parser.add_argument('--npz-list', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()

    main(args.corpus_cache, args.npz_list, args.outdir)
