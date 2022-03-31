import logging
import argparse
import numpy as np

from src.python.concept_discovery.annoy_caches import AnnoyOntologyCache, AnnoyCorpusCache
from src.python.concept_discovery.embedding_caches import StaticEmbCache
from src.python.concept_discovery.utils import cbc_cluster_words_reader, cbc_cluster_reader

logger = logging.getLogger(__name__)


def find_nearest_ontology_nodes(cluster_id_to_records, corpus_cache, ontology_cache, output_file):

    outlines = []
    for idx, cluster_id in enumerate(cluster_id_to_records.keys()):
        print("Handling ({}/{})".format(idx + 1, len(cluster_id_to_records.keys())))
        cluster_embs = list()
        ens = cluster_id_to_records[cluster_id]
        for en in ens:
            emb = corpus_cache.get_emb(en)
            if emb is not None:
                cluster_embs.append(emb)
                # print("{}".format(get_linted_sentence(en.doc_id, int(en.sentence_id),
                #                                      int(en.trigger_idx_span.start_offset),
                #                                      int(en.trigger_idx_span.end_offset),
                #                                      doc_id_sent_id_to_sent_en)))
            else:
                print("Could not find embedding for {}".format(en.to_short_id_str()))
        if len(cluster_embs) > 0:
            cluster_avg_emb = np.mean(cluster_embs, axis=0)
            neighbors = ontology_cache.find_nn(cluster_avg_emb, 10)
            if len(neighbors) > 0:
                outlines.append("{},{},{}".format(cluster_id,
                                                  ",".join(n['dst'] for n in neighbors),
                                                  ",".join(str(n['score']) for n in neighbors)))
            # if neighbors[0] is not None:
            #    print("{},{:f},{}".format(cluster_id, neighbors[0]['score'], neighbors[0]['dst']))
            # print("Cluster {}:".format(cluster_id))
            # for entry in neighbors:
            #    print("\t{} {}".format(entry['score'], entry['dst']))

    with open(output_file, 'w', encoding='utf-8') as o:
        for line in outlines:
            o.write(line)
            o.write('\n')


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


def main(cbc_cluster_path, npz_list, corpus_cache_path, ontology_cache_path, output_file):
    cluster_id_to_records = cbc_cluster_reader(cbc_cluster_path)
    print("Building bert cache: {}".format(npz_list))
    bert_cache = AnnoyCorpusCache(corpus_cache_path, npz_list)
    ontology_cache = AnnoyOntologyCache(ontology_cache_path)
    find_nearest_ontology_nodes(cluster_id_to_records, bert_cache, ontology_cache, output_file)


def static_main(cbc_cluster_path, static_corpus_cache_path, ontology_cache_path, output_file):
    cluster_id_to_words = cbc_cluster_words_reader(cbc_cluster_path)
    print("Building static embedding cache: {}".format(static_corpus_cache_path))
    static_corpus_cache = StaticEmbCache(static_corpus_cache_path)
    ontology_cache = AnnoyOntologyCache(ontology_cache_path)
    find_nearest_ontology_nodes(cluster_id_to_words, static_corpus_cache, ontology_cache, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cbc_cluster', required=True)
    parser.add_argument('--corpus_cache', required=True)
    parser.add_argument('--ontology_cache', required=True)
    parser.add_argument('--embtype', required=True)
    parser.add_argument('--embedding_path', required=True)
    parser.add_argument('--output_file', required=True)

    args = parser.parse_args()

    if args.embtype == "bert" or args.embtype == "distilbert":
        main(args.cbc_cluster, args.embedding_path, args.corpus_cache, args.ontology_cache, args.output_file)
    elif args.embtype == "glove" or args.embtype == "composes":
        static_main(args.cbc_cluster, args.embedding_path, args.ontology_cache, args.output_file)
    else:
        logger.error("Invalid embedding type: {}".format(args.emb_type))

