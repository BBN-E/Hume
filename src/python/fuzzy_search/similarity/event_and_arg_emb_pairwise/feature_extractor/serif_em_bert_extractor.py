import logging

logger = logging.getLogger(__name__)
import numpy as np
import serifxml3

from similarity.event_and_arg_emb_pairwise.models import Feature
from similarity.event_and_arg_emb_pairwise.feature_extractor.models import FeatureExtractor
from similarity.event_and_arg_emb_pairwise.utils.common import create_file_name_to_path
from similarity.event_and_arg_emb_pairwise.feature_extractor.utils import get_all_synnode, \
    get_bert_embs_from_token_span, get_event_most_frequent_head, EventRepresentative


def get_original_sentence_with_em_marking(event_mention: serifxml3.EventMention):
    sentence = event_mention.owner_with_type(serifxml3.Sentence)
    assert isinstance(sentence, serifxml3.Sentence)
    sentence_theory = sentence.sentence_theory
    token_idx_to_token = dict()
    for token_idx, token in enumerate(sentence.token_sequence):
        token_idx_to_token[token_idx] = token
    token_to_token_idx = {v: k for k, v in token_idx_to_token.items()}

    token_to_token_left_marking = dict()
    token_to_token_right_marking = dict()

    if event_mention.semantic_phrase_start is not None and event_mention.semantic_phrase_end is not None:
        token_to_token_left_marking.setdefault(
            event_mention.sentence.token_sequence[event_mention.semantic_phrase_start], list()).append("[")
        token_to_token_right_marking.setdefault(
            event_mention.sentence.token_sequence[event_mention.semantic_phrase_end], list()).append("]")
    else:
        for anchor_node in set([event_mention.anchor_node] +
                               [a.anchor_node for a in event_mention.anchors]):
            token_to_token_left_marking.setdefault(
                anchor_node.start_token, list()).append("[")
            token_to_token_right_marking.setdefault(
                anchor_node.end_token, list()).append("]")

    for argument in event_mention.arguments:
        mention_or_value = argument.value
        if isinstance(mention_or_value, serifxml3.Mention):
            head = mention_or_value.atomic_head
            token_to_token_left_marking.setdefault(
                head.start_token, list()).append("{")
            token_to_token_right_marking.setdefault(
                head.end_token, list()).append("}")
        elif isinstance(mention_or_value, serifxml3.ValueMention):
            token_to_token_left_marking.setdefault(
                mention_or_value.start_token, list()).append("{")
            token_to_token_right_marking.setdefault(
                mention_or_value.end_token, list()).append("}")
    token_arr = []

    for idx, token in enumerate(sentence_theory.token_sequence):
        text = token.text.replace("\n", " ").replace("\t", " ")
        if token in token_to_token_left_marking:
            text = "{}{}".format(
                "".join(token_to_token_left_marking[token]), text)
        if token in token_to_token_right_marking:
            text = "{}{}".format(
                text, "".join(token_to_token_right_marking[token]))
        token_arr.append(text)
    return " ".join(token_arr)


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


class SerifEventMentionBertExtractor(FeatureExtractor):

    def __init__(self, serif_list, bert_list, em_representation_mode, drop_generic_event):
        super().__init__()
        self.doc_id_to_serif_path = create_file_name_to_path(serif_list, ".xml")
        self.doc_id_to_bert_path = create_file_name_to_path(bert_list, ".npz")
        self.em_representation_mode = EventRepresentative[em_representation_mode]
        self.drop_generic_event = drop_generic_event

    def extract_features(self):
        feature_id_to_feature = dict()
        for doc_id, serif_path in self.doc_id_to_serif_path.items():
            if doc_id in self.doc_id_to_bert_path:
                bert_cache = BertEmbCache(self.doc_id_to_bert_path[doc_id])
                added_event_mention_spans = set()
                serif_doc = serifxml3.Document(serif_path)
                event_mention_to_events = dict()
                for event in serif_doc.event_set or ():
                    for event_mention in event.event_mentions:
                        event_mention_to_events.setdefault(event_mention, set()).add(event)
                for sentence in serif_doc.sentences:
                    assert isinstance(sentence, serifxml3.Sentence)
                    sent_no = sentence.sent_no
                    for sentence_theory in sentence.sentence_theories or list():
                        for event_mention in sentence_theory.event_mention_set or list():
                            representative_synnodes = None
                            if self.em_representation_mode == EventRepresentative.MostFrequentHead:
                                representative_synnodes = get_event_most_frequent_head(event_mention)
                            elif self.em_representation_mode == EventRepresentative.AllSynNode:
                                representative_synnodes = get_all_synnode(event_mention)
                            elif self.em_representation_mode == EventRepresentative.SEMANTIC_PHRASE:
                                pass
                            else:
                                raise ValueError(
                                    "Not supported representative_synnodes {}".format(self.em_representation_mode))

                            bert_embs = list()
                            min_event_mention_token_idx = len(sentence.token_sequence)
                            max_event_mention_token_idx = -1
                            if self.em_representation_mode == EventRepresentative.SEMANTIC_PHRASE:
                                min_event_mention_token_idx = event_mention.semantic_phrase_start
                                max_event_mention_token_idx = event_mention.semantic_phrase_end
                                for token_idx in range(event_mention.semantic_phrase_start,
                                                       event_mention.semantic_phrase_end + 1):
                                    bert_embs_local = get_bert_embs_from_token_span(bert_cache, doc_id, sent_no,
                                                                                    token_idx,
                                                                                    token_idx)
                                    bert_embs.extend(bert_embs_local)
                            else:
                                for syn_node in representative_synnodes:
                                    min_token_idx = syn_node.start_token.index()
                                    max_token_idx = syn_node.end_token.index()
                                    min_event_mention_token_idx = min(min_event_mention_token_idx, min_token_idx)
                                    max_event_mention_token_idx = max(max_event_mention_token_idx, max_token_idx)
                                    bert_embs_local = get_bert_embs_from_token_span(bert_cache, doc_id, sent_no,
                                                                                    min_token_idx,
                                                                                    max_token_idx)
                                    bert_embs.extend(bert_embs_local)
                            if len(bert_embs) > 0:
                                event_emb = np.mean(bert_embs, axis=0)
                                em_id = "{}_{}".format(serif_doc.docid, event_mention.id)
                                features = {
                                    "bert": event_emb
                                }
                                event_types = set()
                                event_types.add(event_mention.event_type)
                                for event_type in event_mention.event_types:
                                    event_types.add(event_type.event_type)
                                for event_type in event_mention.factor_types:
                                    event_types.add(event_type.event_type)
                                if self.drop_generic_event and len(event_types.difference({"Event"})) < 1:
                                    continue
                                if self.drop_generic_event:
                                    event_types = event_types.difference({"Event"})
                                for event_type in event_types:
                                    if (
                                    serif_doc.docid, sent_no, min_event_mention_token_idx, max_event_mention_token_idx,
                                    event_type) in added_event_mention_spans:
                                        continue
                                    added_event_mention_spans.add((
                                                                  serif_doc.docid, sent_no, min_event_mention_token_idx,
                                                                  max_event_mention_token_idx, event_type))
                                    aux = {"docid": serif_doc.docid, "sent_id": sent_no, "event_type": event_type,
                                           "start_token_idx": min_event_mention_token_idx,
                                           "end_token_idx": max_event_mention_token_idx, "originalText": "{}".format(
                                            get_original_sentence_with_em_marking(event_mention)),
                                           "em_id": event_mention.id, "event_ids": list(
                                            i.id for i in event_mention_to_events.get(event_mention, set()))}
                                    fuzzy_feature = feature_id_to_feature.setdefault(
                                        em_id, Feature(em_id, dict(), dict()))
                                    fuzzy_feature.features.update(features)
                                    fuzzy_feature.aux.update(aux)

        return list(feature_id_to_feature.values())
