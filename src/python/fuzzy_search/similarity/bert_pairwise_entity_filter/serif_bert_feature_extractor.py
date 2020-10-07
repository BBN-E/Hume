import collections
import typing

import numpy as np
import serifxml3

from causal_factor_structure import EntityMentionGenerator
from similarity.bert_pairwise_entity_filter.feature_extractor import Feature, FeatureExtractor

InstanceId = collections.namedtuple('InstanceId', ['docid', 'sent_idx', 'span_start', 'span_end'])


class MyEventMentionFeature(Feature):
    def __init__(self, feature_id, feature, canonical_names, aux):
        super().__init__(feature_id, feature, aux)
        self.canonical_names = canonical_names

    def reprJSON(self):
        d = super().reprJSON()
        d['canonical_names'] = list(self.canonical_names)
        return d

    @staticmethod
    def fromJSON(d):
        return MyEventMentionFeature(InstanceId(**d['feature_id']), d['feature'], set(d.get('canonical_names', list())),
                                     d.get('aux', dict()))


class BertSerifSingleDocumentFeatureExtractor(FeatureExtractor):

    def __init__(self, serif_doc_path, bert_npz_path):
        super().__init__()
        self.serif_doc_path = serif_doc_path
        self.bert_npz_path = bert_npz_path

    def extract(self) -> typing.List[MyEventMentionFeature]:
        serif_doc = serifxml3.Document(self.serif_doc_path)
        docid = serif_doc.docid
        entity_to_canonical_name = EntityMentionGenerator._entity_to_canonical_name(serif_doc)
        mention_to_entity = dict()
        for serif_entity in serif_doc.entity_set:
            for serif_mention in serif_entity.mentions:
                mention_to_entity[serif_mention] = serif_entity

        with np.load(self.bert_npz_path, allow_pickle=True) as fp2:
            embeddings = fp2['embeddings']
            tokens = fp2['tokens']
            token_map = fp2['token_map']
        res = list()
        for sent_idx, sentence in enumerate(serif_doc.sentences):
            for sentence_theory in sentence.sentence_theories:
                if len(sentence_theory.token_sequence) < 1:
                    continue

                if len(token_map) <= sent_idx:
                    continue

                if len(token_map[sent_idx]) < 1:
                    continue

                token_idx_to_token = dict()
                for token_idx, token in enumerate(sentence_theory.token_sequence):
                    token_idx_to_token[token_idx] = token
                token_to_token_idx = {v: k for k, v in token_idx_to_token.items()}

                for event_mention in sentence_theory.event_mention_set:
                    semantic_phrase_start = int(event_mention.semantic_phrase_start)
                    semantic_phrase_end = int(event_mention.semantic_phrase_end)
                    serif_em_semantic_phrase_text = " ".join(i.text for i in sentence_theory.token_sequence[int(semantic_phrase_start):int(semantic_phrase_end)+1])

                    canonical_name_in_evt_argument = set()
                    for argument in event_mention.arguments:
                        if argument.mention != None:
                            if entity_to_canonical_name.get(mention_to_entity.get(argument.mention, None),
                                                            None) is not None:
                                canonical_name_in_evt_argument.add(
                                    entity_to_canonical_name.get(mention_to_entity.get(argument.mention, None), None))

                    sum_embeddings = None
                    cnt_embeddings = 0

                    for token_idx in range(semantic_phrase_start,semantic_phrase_end+1):
                        token = token_idx_to_token[token_idx]
                        if len(token_map) <= sent_idx or len(token_map[sent_idx]) <= token_idx:
                            continue
                        head_token_idx_in_bert = token_map[sent_idx][token_idx]
                        current_vec = embeddings[sent_idx][head_token_idx_in_bert]
                        if sum_embeddings is None:
                            sum_embeddings = np.array(current_vec)
                        else:
                            sum_embeddings = sum_embeddings + np.array(current_vec)
                        cnt_embeddings += 1
                    instance_id = InstanceId(docid, sent_idx, semantic_phrase_start, semantic_phrase_end)
                    aux = {"semantic_phrase_start": semantic_phrase_start,
                           "semantic_phrase_end": semantic_phrase_end, 'anchor_str': serif_em_semantic_phrase_text,
                           'sentence_str': " ".join(i.text for i in token_idx_to_token.values()),
                           "event_type": list(i.event_type for i in event_mention.event_types)}
                    if cnt_embeddings > 0:
                        res.append(
                        MyEventMentionFeature(instance_id, np.true_divide(sum_embeddings,cnt_embeddings).tolist(), canonical_name_in_evt_argument,aux))
                    # for anchor in event_mention.anchors:
                    #     anchor_node = anchor.anchor_node
                    #     end_token = anchor_node.end_token
                    #     end_token_idx = token_to_token_idx[end_token]
                    #     if len(token_map) <= sent_idx or len(token_map[sent_idx]) <= end_token_idx:
                    #         continue
                    #     head_token_idx_in_bert = token_map[sent_idx][end_token_idx]
                    #     current_vec = embeddings[sent_idx][head_token_idx_in_bert]
                    #     instance_id = InstanceId(docid, sent_idx, anchor_node.start_char, anchor_node.end_char)
                    #     aux = {"semantic_phrase_start": semantic_phrase_start,
                    #            "semantic_phrase_end": semantic_phrase_end, 'anchor_str': anchor_node.text,
                    #            'sentence_str': " ".join(i.text for i in token_idx_to_token.values()),
                    #            "event_type": list(i.event_type for i in event_mention.event_types)}
                    #     res.append(
                    #         MyEventMentionFeature(instance_id, current_vec.tolist(), canonical_name_in_evt_argument,
                    #                               aux))
        return res
