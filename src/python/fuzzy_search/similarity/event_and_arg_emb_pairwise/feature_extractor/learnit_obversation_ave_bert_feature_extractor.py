import json,os
import logging
import functools
import numpy as np

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.models import Feature
from similarity.event_and_arg_emb_pairwise.feature_extractor.models import FeatureExtractor

class CustomBertEmbCache(object):
    # THIS IS NOT THE FORMAT FROM HUME BERT STAGE
    def __init__(self,bert_npz_list):
        self.doc_id_to_npz = dict()
        with open(bert_npz_list) as fp:
            for i in fp:
                i = i.strip()
                doc_id = os.path.basename(i)[:-len(".npz")]
                self.doc_id_to_npz[doc_id] = i
        # self.bert_emb_cache = dict()

    @functools.lru_cache(32)
    def get_npz_for_doc(self,doc_id):
        with np.load(self.doc_id_to_npz[doc_id],
                     allow_pickle=True) as fp2:
            embeddings = fp2['embeddings']
            token_map = fp2['token_map']
            d = dict()
            d['embeddings'] = embeddings
            d['token_map'] = token_map
            return d

    def get_bert_npz_for_token(self,doc_id,sent_id,token_idx):
        d = self.get_npz_for_doc(doc_id)
        head_token_idx_in_bert = d['token_map'][sent_id][token_idx]
        return d['embeddings'][sent_id][head_token_idx_in_bert]

    def get_bert_npz_for_span(self,doc_id,sent_id,start_idx,end_idx):
        ret = list()
        for token_id in range(start_idx, end_idx + 1):
            feature_embs = None
            try:
                feature_embs = self.get_bert_npz_for_token(doc_id,sent_id,token_id)
            except KeyError as e:
                logger.error(
                    "Cannot find bert emb for {} {} {}"
                        .format(doc_id, sent_id, token_id))
                pass
            except IndexError as e:
                logger.error(
                    "Cannot find bert emb for {} {} {}"
                        .format(doc_id, sent_id, token_id))
                pass
            if feature_embs is not None:
                ret.append(feature_embs)
        if len(ret) > 0:
            return np.mean(ret, axis=0)
        else:
            return None

class LearnItObversationFeatureExtractor(FeatureExtractor):

    def __init__(self,input_feature_list,input_bert_list,cap,output_path):
        super().__init__()
        self.input_feature_list = input_feature_list
        self.input_bert_list = input_bert_list
        self.output_path = output_path
        self.cap = int(cap)

    def extract_features(self):
        entry_list = list()
        with open(self.input_feature_list) as fp:
            for i in fp:
                i = i.strip()
                with open(i) as fp2:
                    entry_list.extend(json.load(fp2))
        bert_emb_cache = CustomBertEmbCache(self.input_bert_list)
        feature_id_to_feature = dict()
        for idx,pattern_instances_entry in enumerate(entry_list):
            if idx % 1000 == 0:
                logger.info("Handling {}/{}".format(idx,len(entry_list)))
            pattern_id_string = pattern_instances_entry['learnItObservation']['toIDString']
            pattern_pretty_string = pattern_instances_entry['learnItObservation']['toPrettyString']
            instances = pattern_instances_entry['chosenInstances']
            embs = list()
            for instance in instances:
                emb = None
                doc_id = instance['docId']
                sent_idx = instance['sentId']
                slot0_start = instance['slot0Start']
                slot0_end = instance['slot0End']
                slot1_start = instance['slot1Start']
                slot1_end = instance['slot1End']
                emb0 = bert_emb_cache.get_bert_npz_for_span(doc_id, sent_idx, slot0_start, slot0_end)
                if "empty" in instance['slot1Type'].lower():
                    emb = emb0
                else:
                    emb1 = bert_emb_cache.get_bert_npz_for_span(doc_id, sent_idx, slot1_start, slot1_end)
                    if emb0 is not None and emb1 is not None:
                        emb = np.concatenate((emb0, emb1), axis=None)
                if emb is not None:
                    embs.append(emb)
                else:
                    logger.warning("Cannot find emb for {}".format(instance))
            if len(embs) > 0:
                fuzzy_feature = feature_id_to_feature.setdefault(
                    pattern_id_string, Feature(pattern_id_string, dict(), dict()))
                cnt = len(embs)
                if "aveBERTEmb" in fuzzy_feature.features:
                    cnt = fuzzy_feature.features["aveBERTEmb"]["cnt"] + cnt
                    embs.append(fuzzy_feature.features["aveBERTEmb"]["sum"])
                fuzzy_feature.features['aveBERTEmb'] = {
                    "sum":np.sum(embs,axis=0),
                    "cnt":cnt
                }
                fuzzy_feature.aux["originalText"] = pattern_pretty_string

        return list(feature_id_to_feature.values())