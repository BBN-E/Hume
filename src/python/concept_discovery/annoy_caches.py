import json
import os
import gzip
import logging
from collections import defaultdict

import annoy

from src.python.concept_discovery.embedding_caches import BertEmbeddingCache
from src.python.concept_discovery.utils import EventMentionInstanceIdentifierTokenIdxBase

logger = logging.getLogger(__name__)


class AnnoyCorpusCache(object):
    def __init__(self, annoy_cache_path, bert_npz_path):
        self.annoy_idx_to_en = list()
        with gzip.open(os.path.join(annoy_cache_path, 'id_map.jsonl.gz'), 'rt') as fp:
            for idx, raw_en in enumerate(fp):
                en = EventMentionInstanceIdentifierTokenIdxBase.fromJSON(json.loads(raw_en))
                logger.debug("Loaded {}".format(en.to_short_id_str()))
                self.annoy_idx_to_en.append(en)
        with open(os.path.join(annoy_cache_path, "dimension")) as fp:
            self.dimension = int(fp.read())
        self.annoy_ins = annoy.AnnoyIndex(self.dimension,
                                          "angular")
        logger.info("Loading bert annoy cache")
        self.annoy_ins.load(os.path.join(annoy_cache_path, "cache.bin.ann"))
        logger.info("Loading bert annoy cache completed")
        self.en_to_annoy_idx = dict()
        for annoy_idx, en in enumerate(self.annoy_idx_to_en):
            self.en_to_annoy_idx[en.to_short_id_str()] = annoy_idx

        self.bert_cache = BertEmbeddingCache(bert_npz_path)

    def get_emb(self, em_instance):
        key = em_instance.to_short_id_str()
        if key in self.en_to_annoy_idx:
            return self.annoy_ins.get_item_vector(self.en_to_annoy_idx[key])
        else:
            return self.bert_cache.get_contextual_emb_for_span(em_instance.doc_id, em_instance.sentence_id,
                                                               em_instance.trigger_idx_span.start_offset,
                                                               em_instance.trigger_idx_span.end_offset)

    def find_nn(self, em_instance, n_neighbors=50):
        key = em_instance.to_short_id_str()
        if key in self.en_to_annoy_idx:
            entries = []
            nearest_neighbor_idxs, nearest_neighbor_distances = (
                self.annoy_ins.get_nns_by_item(
                    self.en_to_annoy_idx[key],
                    n_neighbors,
                    search_k=-1,
                    include_distances=True)
            )
            for idx in range(len(nearest_neighbor_idxs)):
                neighbor_annoy_idx = nearest_neighbor_idxs[idx]
                neighbor_distance = nearest_neighbor_distances[idx]
                entry = {
                    'src': em_instance,
                    'dst': self.annoy_idx_to_en[neighbor_annoy_idx],
                    'score': neighbor_distance,
                }
                entries.append(entry)
            return entries
        else:
            entries = list()
            span_emb = self.bert_cache.get_contextual_emb_for_span(em_instance.doc_id, em_instance.sentence_id,
                                                                   em_instance.trigger_idx_span.start_offset,
                                                                   em_instance.trigger_idx_span.end_offset)
            if span_emb is not None:
                nearest_neighbor_idxs, nearest_neighbor_distances = (
                    self.annoy_ins.get_nns_by_vector(
                        span_emb,
                        50,
                        search_k=-1,
                        include_distances=True)
                )
                for idx in range(len(nearest_neighbor_idxs)):
                    neighbor_annoy_idx = nearest_neighbor_idxs[idx]
                    neighbor_distance = nearest_neighbor_distances[idx]
                    entry = {
                        'src': em_instance,
                        'dst': self.annoy_idx_to_en[neighbor_annoy_idx],
                        'score': neighbor_distance,
                    }
                    entries.append(entry)
            return entries


class AnnoyOntologyCache(object):
    def __init__(self, annoy_cache_dir):
        self.annoy_idx_to_type = list()
        with gzip.open(os.path.join(annoy_cache_dir, 'id_map.jsonl.gz'), 'rt') as fp:
            for idx, line in enumerate(fp):
                self.annoy_idx_to_type.append(line.strip())
        self.annotations = set()
        with open(os.path.join(annoy_cache_dir, "annotations")) as fp:
            for line in fp:
                self.annotations.add(line.strip())
        with open(os.path.join(annoy_cache_dir, "dimension")) as fp:
            self.dimension = int(fp.read())
        self.annoy_ins = annoy.AnnoyIndex(self.dimension, "angular")
        logger.info("Loading bert annoy cache")
        self.annoy_ins.load(os.path.join(annoy_cache_dir, "cache.bin.ann"))
        logger.info("Loading bert annoy cache completed")
        self.type_to_annoy_idx = dict()
        for annoy_idx, t in enumerate(self.annoy_idx_to_type):
            self.type_to_annoy_idx[t] = annoy_idx

    def find_nn(self, vector, n_neighbors=50):
        ret = list()
        nearest_neighbor_idxs, nearest_neighbor_distances = (
            self.annoy_ins.get_nns_by_vector(
                vector,
                n_neighbors,
                search_k=-1,
                include_distances=True)
        )

        for idx in range(len(nearest_neighbor_idxs)):
            neighbor_annoy_idx = nearest_neighbor_idxs[idx]
            neighbor_distance = nearest_neighbor_distances[idx]
            entry = {
                'dst': self.annoy_idx_to_type[neighbor_annoy_idx],
                'score': neighbor_distance,
            }
            ret.append(entry)
        return ret

    def to_dict(self):
        result = defaultdict(list)
        for idx, event_type in enumerate(self.annoy_idx_to_type):
            result[event_type].append(self.annoy_ins.get_item_vector(idx))
        return result

    def annotations_to_dict(self):
        result = defaultdict(list)
        for idx, event_type in enumerate(self.annoy_idx_to_type):
            if event_type in self.annotations:
                result[event_type].append(self.annoy_ins.get_item_vector(idx))
        return result

