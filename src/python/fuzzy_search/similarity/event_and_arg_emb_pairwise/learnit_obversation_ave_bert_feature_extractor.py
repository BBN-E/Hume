import collections,json,os
import typing
import logging
import functools
import numpy as np

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.feature import Feature


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
        return dict(
            np.load(self.doc_id_to_npz[doc_id], allow_pickle=True)["sent_id_to_token_to_emb"].item())

    def get_bert_npz_for_token(self,doc_id,sent_id,token_idx):
        emb = self.get_npz_for_doc(doc_id)
        return emb.get(sent_id, dict()).get(token_idx, None)

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



def extract_average_bert_emb_for_learnit_obversation(bert_npz_list,input_learnit_pattern_instance_json_file):
    with open(input_learnit_pattern_instance_json_file) as fp:
        entry_list = json.load(fp)
    bert_emb_cache = CustomBertEmbCache(bert_npz_list)
    feature_id_to_feature = dict()
    for pattern_instances_entry in entry_list:
        pattern_id_string = pattern_instances_entry['learnItObservation']['toIDString']
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
            pattern_emb = np.mean(embs, axis=0)
            fuzzy_feature = feature_id_to_feature.setdefault(
                pattern_id_string, Feature(pattern_id_string, dict(), dict()))
            fuzzy_feature.features['aveBERTEmb'] = pattern_emb

    return list(feature_id_to_feature.values())