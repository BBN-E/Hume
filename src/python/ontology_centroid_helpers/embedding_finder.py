import argparse
import gzip
import os, json, logging
from collections import defaultdict

import numpy as np
import annoy
import time

from src.python.concept_discovery.embedding_caches import BertEmbeddingCache, WordAvgEmbeddings, \
    TrimmedBertEmbeddingCache
from src.python.concept_discovery.annoy_caches import AnnoyOntologyCache
from hume_ontology.internal_ontology import build_internal_ontology_tree_without_exampler
from external_ontology import parse_external_ontology_metadata_new

logger = logging.getLogger(__name__)

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
hume_root = os.path.realpath(os.path.join(project_root, os.path.pardir, os.path.pardir, os.path.pardir))


def build_annoy_index(ontology_name_to_embeddings, annotation_types, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    annoy_ins = None
    idx_line = 0
    dimension = 0
    with gzip.open(os.path.join(output_dir, 'id_map.jsonl.gz'), 'wt') as wfp:
        for event_type, embs in ontology_name_to_embeddings.items():
            if len(embs) > 0:
                avg_emb = np.mean(embs, axis=0)
                dimension = len(avg_emb)
                if annoy_ins is None:
                    annoy_ins = annoy.AnnoyIndex(dimension, "angular")
                    annoy_ins.on_disk_build(os.path.join(output_dir, "cache.bin.ann"))
                annoy_ins.add_item(idx_line, avg_emb)
                idx_line += 1
                wfp.write("{}\n".format(event_type))

    logger.info("Begin building annoy index")
    annoy_ins.build(100)
    # logger.info("Begin saving annoy index")
    # annoy_ins.save(
    #     os.path.join(output_dir, "cache.bin.ann"))
    logger.info("Finish saving annoy index")
    with open(os.path.join(output_dir, 'dimension'), 'w') as wfp:
        wfp.write("{}".format(dimension))
    with open(os.path.join(output_dir, 'annotations'), 'w') as wfp:
        for event_type in annotation_types:
            wfp.write("{}\n".format(event_type))


def get_annotation_embeddings_from_existing_cache(existing_cache_path):
    cache = AnnoyOntologyCache(existing_cache_path)
    return cache.annotations_to_dict()


def get_embeddings_for_external_nodes_based_on_annotation(event_annotation_jsonl_path,
                                                          internal_ontology_name_to_external_ontology_names,
                                                          emb_cache):
    """
    Returns a dictionary mapping each external ontology node to a list of embeddings from annotation
    """
    node_to_embeddings_map = defaultdict(list)
    doc_id_to_annotation_en = defaultdict(list)
    external_type_count = defaultdict(int)

    with open(event_annotation_jsonl_path) as fp:
        for i in fp:
            i = i.strip()
            en = json.loads(i)
            doc_id_to_annotation_en[en['docid']].append(en)

    for doc_index, (docid, ens) in enumerate(doc_id_to_annotation_en.items()):
        for en in ens:
            doc_id, sent_idx, trigger_start_idx, trigger_end_idx, event_type = en['docid'], en['sent_idx'], en[
                'trig_idx_start'], en['trig_idx_end'], en['event_type']
            external_types = internal_ontology_name_to_external_ontology_names.get(event_type, set())
            # print("External types: {}".format(external_types))
            emb = emb_cache.get_contextual_emb_for_token(doc_id, sent_idx, trigger_end_idx)
            if emb is not None:
                for t in external_types:
                    node_to_embeddings_map[t].append(emb)
                    external_type_count[t] += 1

        if ((doc_index + 1) % 10) == 0:
            logger.info('processed {}/{} docs'.format((doc_index + 1), len(doc_id_to_annotation_en)))

    logger.info('processed {} total docs'.format(len(doc_id_to_annotation_en)))
    for t, count in external_type_count.items():
        logger.info("{} #embeddings based on annotations={}".format(t, count))

    return node_to_embeddings_map


def get_embeddings_for_external_nodes_based_on_exemplars(external_ontology_metadata_path, embeddings):
    """
    Returns a dictionary mapping each external ontology node to a list of embeddings based on its metadata examples
    """


    node_to_embeddings_map = defaultdict(list)
    external_ontology_path_to_node = parse_external_ontology_metadata_new(external_ontology_metadata_path)

    for external_ontology_path, node in external_ontology_path_to_node.items():
        if len(node.examples) > 0:
            c = 0
            for example in node.examples:
                tokens = example.split(" ")
                embs = list()
                for token in tokens:
                    emb = embeddings.get_emb(token)
                    if emb is not None:
                        embs.append(emb)
                    else:
                        logger.info('{} does not exist in normalized_word_ave_emb'.format(token.lower()))

                if len(embs) > 1:
                    average_emb = np.mean(embs, axis=0)
                    node_to_embeddings_map[external_ontology_path].append(average_emb)
                    c += 1
                elif len(embs) == 1:
                    node_to_embeddings_map[external_ontology_path].append(embs[0])
                    c += 1
                else:
                    logger.info('missed', example)
            logger.info('{}, has embeddings for {}/{} keywords'.format(external_ontology_path, c, len(node.examples)))

    for external_ontology_path, node in external_ontology_path_to_node.items():
        if len(node.examples) > 0:
            if external_ontology_path not in node_to_embeddings_map:
                logger.info("{} not exists".format(external_ontology_path))

    return node_to_embeddings_map


def build_internal_to_external_ontology_mapping(internal_ontology_path):
    internal_ontology_name_to_external_ontology_names = defaultdict(set)
    ontology_tree_root, node_name_to_nodes_mapping = build_internal_ontology_tree_without_exampler(
        internal_ontology_path)
    for node_name, nodes in node_name_to_nodes_mapping.items():
        for node in nodes:
            for source in node._source:
                if source.startswith("WM:"):
                    internal_ontology_name_to_external_ontology_names[node_name].add(source.split("WM:")[1].strip())
    """
    print('== internal_ontology_name_to_external_ontology_names')
    for key, value in internal_ontology_name_to_external_ontology_names.items():
        print(key, value)
    # example of (key,value) = CovidVirus {'/wm/concept/health/disease/COVID'}
    # example of (key,value) = HumanDisease {'/wm/concept/health/disease'}
    """
    return internal_ontology_name_to_external_ontology_names


def main(trimmed_annotation_npz, event_annotation_jsonl_path, internal_ontology_path, external_ontology_metadata_path,
         word_embeddings, output_dir, existing_cache=None):

    internal_ontology_name_to_external_ontology_names = build_internal_to_external_ontology_mapping(
        internal_ontology_path)

    if existing_cache is not None:
        ann_dict = get_annotation_embeddings_from_existing_cache(existing_cache)
    else:
        annotation_embeddings = TrimmedBertEmbeddingCache(trimmed_annotation_npz)
        ann_dict = get_embeddings_for_external_nodes_based_on_annotation(
            event_annotation_jsonl_path, internal_ontology_name_to_external_ontology_names, annotation_embeddings)

    exemplar_dict = get_embeddings_for_external_nodes_based_on_exemplars(external_ontology_metadata_path,
                                                                         word_embeddings)

    # Final embedding dict contains annotation-based embeddings when available and exemplar-based embeddings otherwise
    external_ontology_name_to_embeddings = exemplar_dict.copy()
    external_ontology_name_to_embeddings.update(ann_dict)

    print('=== We now have embeddings for these ontology nodes ==')
    for key in sorted(external_ontology_name_to_embeddings):
        print(key)

    build_annoy_index(external_ontology_name_to_embeddings, ann_dict.keys(), output_dir)


if __name__ == "__main__":

    tic = time.perf_counter()

    wm_internal_ontology_path = os.path.join(
        hume_root, "resource", "ontologies", "internal", "hume", "compositional_event_ontology.yaml")

    parser = argparse.ArgumentParser()
    parser.add_argument('--embtype', required=True)
    parser.add_argument('--outdir', required=True)
    parser.add_argument('--annotation-event-jsonl', required=True)
    parser.add_argument('--ontology-metadata-path', required=True)
    parser.add_argument('--trimmed-annotation-npz', required=True)
    parser.add_argument('--averaged-embeddings', required=True)
    parser.add_argument('--existing-cache', default=None)
    args = parser.parse_args()

    if args.embtype == "bert" or args.embtype == "distilbert":
        word_emb_cache = WordAvgEmbeddings(args.averaged_embeddings)
    else:
        logger.error("Invalid embedding type: {}".format(args.embtype))

    main(args.trimmed_annotation_npz, args.annotation_event_jsonl, wm_internal_ontology_path, args.ontology_metadata_path,
         word_emb_cache, args.outdir, args.existing_cache)

    toc = time.perf_counter()
    print(f'Total Processing Time: {toc - tic:0.4f} seconds')
