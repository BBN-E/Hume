
import enum
import numpy as np
import logging

logger = logging.getLogger(__name__)

def merge_features_by_calculating_centroid_sum(list_of_features, feature_id_to_feature, cap,care_feature_ids):

    for feature_idx, feature in enumerate(list_of_features):
        feature_id = feature.feature_id
        if feature_id not in care_feature_ids:
            continue
        for feature_name_dst,feature_dict_dst in feature.features.items():
            if feature_id in feature_id_to_feature:
                d = feature_id_to_feature[feature_id].features.get(feature_name_dst)
                if d is not None and isinstance(d,dict):
                    if d['cnt'] < cap:
                        d['sum'] = d['sum'] + feature_dict_dst['sum']
                        d['cnt'] = d['cnt'] + feature_dict_dst['cnt']
                    else:
                        # exceed cap. Prevent further sampling
                        pass
                else:
                    feature_id_to_feature[feature_id].features[feature_name_dst] = feature_dict_dst

            else:
                feature_id_to_feature[feature_id] = feature

        feature_id_to_feature[feature_id].aux = {**feature_id_to_feature[feature_id].aux, **feature.aux}

    return feature_id_to_feature

def merge_feature_by_calculating_centroid_ave(feature_id_to_feature):
    for featurd_id, feature in feature_id_to_feature.items():
        for feature_name,feature_dict in feature.features.items():
            if isinstance(feature_dict,dict):
                feature.features[feature_name] = feature_dict['sum'] / feature_dict['cnt']
    return feature_id_to_feature

class EventRepresentative(enum.Enum):
    MostFrequentHead = 0
    AllSynNode = 1
    SEMANTIC_PHRASE = 2

def get_event_most_frequent_head(serif_em):
    syn_node_to_freq = dict()
    if serif_em.anchor_node is not None:
        runner = serif_em.anchor_node
        while runner.head is not None:
            runner = runner.head
        syn_node_to_freq[runner] = syn_node_to_freq.get(runner,0)+1
    for anchor in serif_em.anchors:
        if anchor.anchor_node is not None:
            runner = anchor.anchor_node
            while runner.head is not None:
                runner = runner.head
            syn_node_to_freq[runner] = syn_node_to_freq.get(runner, 0) + 1
    return [max(syn_node_to_freq.items(),key=lambda x:x[1])[0]]

def get_all_synnode(serif_em):
    all_syn_node = set()
    if serif_em.anchor_node is not None:
        all_syn_node.add(serif_em.anchor_node)
    for anchor in serif_em.anchors:
        if anchor.anchor_node is not None:
            all_syn_node.add(anchor.anchor_node)
    return list(all_syn_node)

def get_bert_embs_from_token_span(bert_cache,doc_id,sent_no,min_token_idx,max_token_idx):
    bert_embs = list()
    for token_idx in range(min_token_idx, max_token_idx + 1):
        bert_emb = None
        try:
            bert_emb = bert_cache.get_bert_emb(sent_no, token_idx)
        except KeyError as e:
            logger.error(
                "Cannot find bert emb for {} {} {}"
                    .format(doc_id, sent_no, token_idx))
            pass
        except IndexError as e:
            logger.error(
                "Cannot find bert emb for {} {} {}"
                    .format(doc_id, sent_no, token_idx))
            pass
        if bert_emb is not None:
            bert_embs.append(bert_emb)
    return bert_embs