import logging
import numpy as np
import serifxml3

from similarity.event_and_arg_emb_pairwise.models import Feature
from similarity.event_and_arg_emb_pairwise.feature_extractor.models import FeatureExtractor
from similarity.event_and_arg_emb_pairwise.utils.common import create_file_name_to_path
from similarity.event_and_arg_emb_pairwise.feature_extractor.utils import get_all_synnode,get_bert_embs_from_token_span,get_event_most_frequent_head,EventRepresentative


logger = logging.getLogger(__name__)


class BertEmbCache(object):
    def __init__(self, bert_npz_path):
        with np.load(bert_npz_path,
                     allow_pickle=True) as fp2:
            embeddings = fp2['embeddings']
            token_map = fp2['token_map']
            self.d = dict()
            self.d['embeddings'] = embeddings
            self.d['token_map'] = token_map

    def get_bert_emb(self, sent_id, token_id):
        token_map = self.d['token_map']
        embeddings = self.d['embeddings']
        head_token_idx_in_bert = token_map[sent_id][token_id]
        return embeddings[sent_id][head_token_idx_in_bert]

def get_event_representative_synnode(serif_em:serifxml3.EventMention):
    syn_node_to_freq = dict()
    if serif_em.anchor_node is not None:
        if serif_em.anchor_node.head:
            syn_node_to_freq[serif_em.anchor_node.head] = syn_node_to_freq.get(serif_em.anchor_node.head,0)+1
        else:
            syn_node_to_freq[serif_em.anchor_node] = syn_node_to_freq.get(serif_em.anchor_node,0)+1
    for anchor in serif_em.anchors:
        if anchor.anchor_node is not None:
            if anchor.anchor_node.head:
                syn_node_to_freq[anchor.anchor_node.head] = syn_node_to_freq.get(anchor.anchor_node.head, 0) + 1
            else:
                syn_node_to_freq[anchor.anchor_node] = syn_node_to_freq.get(anchor.anchor_node, 0) + 1
    return max(syn_node_to_freq.items(),key=lambda x:x[1])[0]


class SerifEventMentionTypeCentroidExtractor(FeatureExtractor):

    def __init__(self,serif_list,bert_list,em_representation_mode):
        super().__init__()
        self.doc_id_to_serif_path = create_file_name_to_path(serif_list,".xml")
        self.doc_id_to_bert_path = create_file_name_to_path(bert_list,".npz")
        self.em_representation_mode = EventRepresentative[em_representation_mode]

    def extract_features(self):
        event_type_to_d = dict()
        for doc_id,serif_path in self.doc_id_to_serif_path.items():
            if doc_id in self.doc_id_to_bert_path:
                bert_cache = BertEmbCache(self.doc_id_to_bert_path[doc_id])
                serif_doc = serifxml3.Document(serif_path)
                for sentence in serif_doc.sentences or list():
                    assert isinstance(sentence,serifxml3.Sentence)
                    sent_no = sentence.sent_no
                    for sentence_theory in sentence.sentence_theories or list():
                        for event_mention in sentence_theory.event_mention_set or list():
                            representative_synnodes = None
                            if self.em_representation_mode == EventRepresentative.MostFrequentHead:
                                representative_synnodes = get_event_most_frequent_head(event_mention)
                            elif self.em_representation_mode == EventRepresentative.AllSynNode:
                                representative_synnodes = get_all_synnode(event_mention)
                            else:
                                raise ValueError(
                                    "Not supported representative_synnodes {}".format(self.em_representation_mode))
                            bert_embs = list()
                            for syn_node in representative_synnodes:
                                min_token_idx = syn_node.start_token.index()
                                max_token_idx = syn_node.end_token.index()
                                bert_embs_local = get_bert_embs_from_token_span(bert_cache, doc_id, sent_no, min_token_idx,
                                                                          max_token_idx)
                                bert_embs.extend(bert_embs_local)
                            if len(bert_embs) > 0:
                                event_types = set()
                                event_types.add(event_mention.event_type)
                                for event_type in event_mention.event_types:
                                    event_types.add(event_type.event_type)
                                for factor_type in event_mention.factor_types:
                                    event_types.add(factor_type.event_type)
                                for event_type in event_types:
                                    if event_type not in event_type_to_d:
                                        event_type_to_d[event_type] = {
                                            "sum":np.sum(bert_embs,axis=0),
                                            "cnt":len(bert_embs)
                                        }
                                    else:
                                        sum = np.sum(bert_embs,axis=0)
                                        sum = np.sum([event_type_to_d[event_type]['sum'],sum],axis=0)
                                        cnt = event_type_to_d[event_type]['cnt'] + len(bert_embs)
                                        event_type_to_d[event_type] = {
                                            "sum":sum,
                                            "cnt":cnt
                                        }
        feature_id_to_feature = dict()
        for event_type,en in event_type_to_d.items():
            fuzzy_feature = feature_id_to_feature.setdefault(
                event_type, Feature(event_type, dict(), dict()))
            fuzzy_feature.features['eventCentroid'] = {
                "sum": en['sum'],
                "cnt": en['cnt']
            }
            fuzzy_feature.aux['originalText'] = event_type
        return list(feature_id_to_feature.values())