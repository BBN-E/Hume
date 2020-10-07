import collections
import typing

import numpy as np
import serifxml3

from causal_factor_structure import EntityMentionGenerator, to_tokens, ActionGenerator
from similarity.bert_pairwise_entity_filter.feature_extractor import Feature, FeatureExtractor

QueryId = collections.namedtuple("QueryId", ["query_id", "query_str"])


class MyQueryFeature(Feature):
    def __init__(self, feature_id, feature, canonical_names, aux):
        super().__init__(feature_id, feature, aux)
        self.canonical_names = canonical_names

    def reprJSON(self):
        d = super().reprJSON()
        d['canonical_names'] = list(self.canonical_names)
        return d

    @staticmethod
    def fromJSON(d):
        return MyQueryFeature(QueryId(**d['feature_id']), d['feature'], set(d['canonical_names']), d['aux'])


class QueryFeatureExtractor(FeatureExtractor):

    def __init__(self, serif_doc_path, bert_npz_path):
        super().__init__()
        self.serif_doc_path = serif_doc_path
        self.bert_npz_path = bert_npz_path

    def extract(self) -> typing.List[MyQueryFeature]:
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
        ret = list()
        for sent_idx, sentence in enumerate(serif_doc.sentences):
            for sentence_theory in sentence.sentence_theories:
                if len(sentence_theory.token_sequence) < 1:
                    continue

                if len(token_map[sent_idx]) < 1:
                    continue

                token_idx_to_token = dict()
                for token_idx, token in enumerate(sentence_theory.token_sequence):
                    token_idx_to_token[token_idx] = token
                token_to_token_idx = {v: k for k, v in token_idx_to_token.items()}
                query_str = ' '.join(t.text for t in token_idx_to_token.values())
                entity_mentions = EntityMentionGenerator.get_entity_mentions(sentence_theory, serif_doc,
                                                                             to_tokens(sentence_theory))
                all_actions, all_semantic_phrases = ActionGenerator.get_actions(sentence_theory,
                                                                                to_tokens(sentence_theory))
                pruned_actions = ActionGenerator.discard_actions_covered_by_entity_mentions(all_actions,
                                                                                            entity_mentions)
                entity_mentions = set(i.canonical_name for i in entity_mentions)


                sum_embeddings = None
                cnt_embeddings = 0
                for token_idx, token in enumerate(sentence_theory.token_sequence):
                    head_token_idx_in_bert = token_map[sent_idx][token_idx]
                    current_vec = embeddings[sent_idx][head_token_idx_in_bert]
                    if sum_embeddings is None:
                        sum_embeddings = np.array(current_vec)
                    else:
                        sum_embeddings = sum_embeddings + np.array(current_vec)
                    cnt_embeddings += 1
                query_id = QueryId(query_str, query_str)
                ret.append(MyQueryFeature(query_id, np.true_divide(sum_embeddings,cnt_embeddings).tolist(), entity_mentions, dict()))

                # sorted_actions = sorted(pruned_actions, key=lambda x: x.end_char)

                # for idx, action in enumerate(sorted_actions):
                #     query_id = QueryId(query_str, " ".join(i.text for i in action.tokens))
                #     end_token_idx = action.tokens[-1].token_index
                #     head_token_idx_in_bert = token_map[sent_idx][end_token_idx]
                #     current_vec = embeddings[sent_idx][head_token_idx_in_bert]
                #     ret.append(MyQueryFeature(query_id, current_vec.tolist(), entity_mentions, dict()))
        return ret
