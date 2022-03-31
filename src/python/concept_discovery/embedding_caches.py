import gzip
import json
import logging
import os
import annoy
import numpy as np
import functools
from abc import ABC, abstractmethod

from src.python.concept_discovery.utils import build_doc_id_to_path_mapping, sentence_jsonl_reader, \
    EventMentionInstanceIdentifierTokenIdxBase

logger = logging.getLogger(__name__)


class EmbeddingCache(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def get_emb(self, word):
        pass


class ContextualEmbeddingCache(ABC):
    def __init__(self):
        super(ContextualEmbeddingCache, self).__init__()

    @abstractmethod
    def get_contextual_emb_for_token(self, doc_id, sent_id, token_id):
        pass

    def get_contextual_emb_for_span(self, doc_id, sent_id, start_idx, end_idx):
        ret = list()
        for token_id in range(start_idx, end_idx + 1):
            feature_embs = None
            try:
                feature_embs = self.get_contextual_emb_for_token(doc_id, sent_id, token_id)
            except KeyError as e:
                logger.error(
                    "Cannot find bert emb for {} {} {}".format(doc_id, sent_id, token_id))
                pass
            except IndexError as e:
                logger.error(
                    "Cannot find bert emb for {} {} {}".format(doc_id, sent_id, token_id))
                pass
            if feature_embs is not None:
                ret.append(feature_embs)

        if len(ret) > 0:
            return np.mean(ret, axis=0)
        else:
            return None


class StaticEmbCache(EmbeddingCache):

    def __init__(self, embeddings_path, missing_token=None, normalize=True):
        super(StaticEmbCache, self).__init__()
        self.word_to_vec = self._load_dict_from_npz(embeddings_path)
        self.missing_token = missing_token
        self.normalize = normalize

    def get_emb(self, word):
        if self.normalize is True:
            word = self._normalize(word)
        if word in self.word_to_vec:
            return self.word_to_vec[word]
        else:
            logger.warning("Missing {} in word_to_vec".format(word))
            if self.missing_token is not None:
                return self.word_to_vec[self.missing_token]
            else:
                return None

    @staticmethod
    def _normalize(word):
        return str.lower(word)

    @staticmethod
    def _load_dict_from_text_file(filename):
        result = {}
        with open(filename, 'r', encoding="utf8") as f:
            for line in f:
                values = line.split()
                try:
                    word = values[0]
                    vector = np.asarray(values[1:], "float32")
                    result[word] = vector
                except ValueError:
                    logger.error("Could not parse embedding entry: Word: {} First Val {}".format(word, values[1]))
        return result

    @staticmethod
    def _load_dict_from_npz(npz_file):
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
        return word_to_word_vec


class WordAvgEmbeddings(EmbeddingCache):
    def __init__(self, path):
        super(WordAvgEmbeddings, self).__init__()
        self.emb_dict = dict()
        word_avg_emb_dict = dict(np.load(path, allow_pickle=True)["word_to_emb_ave"].item())
        # normalize each word
        for word, emb in word_avg_emb_dict.items():
            self.emb_dict[self._normalize(word)] = emb

    def get_emb(self, word):
        norm_word = self._normalize(word)
        if norm_word in self.emb_dict:
            return self.emb_dict[norm_word]
        else:
            return None

    @staticmethod
    def _normalize(word):
        return word.lower()


class StaticEmbCacheForCorpus(ContextualEmbeddingCache):

    def __init__(self, embeddings_cache, sentence_jsonl_list):
        super(StaticEmbCacheForCorpus, self).__init__()
        self.emb_cache = embeddings_cache
        self.doc_id_sent_id_to_sent_en = dict()
        with open(sentence_jsonl_list) as fp:
            for line in fp:
                line = line.strip()
                d = sentence_jsonl_reader(line)
                self.doc_id_sent_id_to_sent_en.update(d)

    def get_emb(self, word):
        return self.emb_cache.get_emb(word)

    def get_contextual_emb_for_token(self, doc_id, sent_id, token_id):
        emb = None
        word = None
        try:
            sentence_en = self.doc_id_sent_id_to_sent_en[(doc_id, sent_id)]
            word = sentence_en['sentenceInfo']['token'][token_id]
            if word is None:
                logger.error("Cannot find token for {} {} {}".format(doc_id, sent_id, token_id))
            emb = self.get_emb(word)
        except KeyError as e:
            logger.error("Cannot find GloVe emb for {} {} {} {}".format(doc_id, sent_id, token_id, word))
            pass
        except IndexError as e:
            logger.error("Cannot find GloVe emb for {} {} {} {}".format(doc_id, sent_id, token_id, word))
            pass

        return emb


class TrimmedBertEmbeddingCache(ContextualEmbeddingCache):
    """ Stores only the embeddings for relevant tokens, e.g. trigger spans """
    def __init__(self, path):
        super(TrimmedBertEmbeddingCache, self).__init__()
        self.emb_dict = dict(np.load(path, allow_pickle=True)["tokens_to_embeddings"].item())

    def get_contextual_emb_for_token(self, doc_id, sent_id, token_idx):
        emb = None
        try:
            emb = self.emb_dict[(doc_id, sent_id, token_idx)]
        except KeyError as e:
            logger.error("Cannot find Bert embedding for {} {} {}".format(doc_id, sent_id, token_idx))
            pass
        return emb


class BertEmbeddingCache(ContextualEmbeddingCache):
    # THIS IS NOT THE FORMAT FROM HUME BERT STAGE
    def __init__(self, bert_npz_list):
        super(BertEmbeddingCache, self).__init__()
        self.doc_id_to_npz = build_doc_id_to_path_mapping(bert_npz_list, suffix=".npz")

    @functools.lru_cache(32)
    def get_npz_for_doc(self, doc_id):
        with np.load(self.doc_id_to_npz[doc_id],
                     allow_pickle=True) as fp2:
            embeddings = fp2['embeddings']
            token_map = None
            if 'token_map' in fp2:
                token_map = fp2['token_map']
            d = dict()
            d['embeddings'] = embeddings
            d['token_map'] = token_map
            return d

    def get_contextual_emb_for_token(self, doc_id, sent_id, token_idx):
        emb = None
        try:
            d = self.get_npz_for_doc(doc_id)
            head_token_idx_in_bert = token_idx
            if 'token_map' in d and d['token_map'] is not None:
                head_token_idx_in_bert = d['token_map'][sent_id][token_idx]
            emb = d['embeddings'][sent_id][head_token_idx_in_bert]
        except KeyError as e:
            logger.error("Cannot find bert emb for {} {} {}".format(doc_id, sent_id, token_idx))
            pass
        except IndexError as e:
            logger.error("Cannot find bert emb for {} {} {}".format(doc_id, sent_id, token_idx))
            pass
        return emb


class MyStaticCacheDB(object):
    def __init__(self, annoy_cache_path):
        self.annoy_idx_to_en = list()
        with gzip.open(os.path.join(annoy_cache_path, 'id_map.jsonl.gz'), 'rt') as fp:
            for idx, raw_en in enumerate(fp):
                self.annoy_idx_to_en.append(EventMentionInstanceIdentifierTokenIdxBase.fromJSON(json.loads(raw_en)))
        with open(os.path.join(annoy_cache_path, "dimension")) as fp:
            self.dimension = int(fp.read())
        self.annoy_ins = annoy.AnnoyIndex(self.dimension,
                                          "angular")
        logger.info("Loading annoy cache")
        self.annoy_ins.load(os.path.join(annoy_cache_path, "cache.bin.ann"))
        logger.info("Loading annoy cache completed")
        self.en_to_annoy_idx = dict()
        for annoy_idx, en in enumerate(self.annoy_idx_to_en):
            self.en_to_annoy_idx[en] = annoy_idx

    def find(self, word):
        if word in self.en_to_annoy_idx:
            entries = []
            nearest_neighbor_idxs, nearest_neighbor_distances = (
                self.annoy_ins.get_nns_by_item(
                    self.en_to_annoy_idx[word],
                    200,
                    search_k=-1,
                    include_distances=True)
            )
            for idx in range(len(nearest_neighbor_idxs)):
                neighbor_annoy_idx = nearest_neighbor_idxs[idx]
                neighbor_distance = nearest_neighbor_distances[idx]
                entry = {
                    'src': word,
                    'dst': self.annoy_idx_to_en[neighbor_annoy_idx],
                    'score': neighbor_distance,
                }
                entries.append(entry)
            return entries
        else:
            entries = list()
            return entries


