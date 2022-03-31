import serifxml3
import logging
import numpy as np

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.models import Feature
from similarity.event_and_arg_emb_pairwise.feature_extractor.models import FeatureExtractor
from similarity.utils.get_pretrained_embeddings import get_pretrained_embeddings


class BertEmbCache(object):
    def __init__(self, doc_id_to_bert_npz_path):
        self.doc_id_to_bert_npz_path = doc_id_to_bert_npz_path
        self.doc_id_to_bert = dict()

    def get_bert_emb(self, docid, sent_id, token_id):
        if docid not in self.doc_id_to_bert.keys():
            with np.load(self.doc_id_to_bert_npz_path[docid],
                         allow_pickle=True) as fp2:
                embeddings = fp2['embeddings']
                token_map = fp2['token_map']
                d = self.doc_id_to_bert.setdefault(docid, dict())
                d['embeddings'] = embeddings
                d['token_map'] = token_map
        token_map = self.doc_id_to_bert[docid]['token_map']
        embeddings = self.doc_id_to_bert[docid]['embeddings']
        head_token_idx_in_bert = token_map[sent_id][token_id]
        return embeddings[sent_id][head_token_idx_in_bert]


class NLPLingoFeatureExtractor(object):
    def __init__(self, bert_emb_cache, key_getter_str_lists):
        self.bert_emb_cache = bert_emb_cache
        self.em_to_feature_dict = dict()
        self.em_to_names = dict()

        self.trigger_extractor_name_to_key_getter_str = dict()
        self.argument_extractor_name_to_key_getter_str = dict()

        self.em_to_serif_doc = dict()

        for key_getter_str in key_getter_str_lists:
            getter_type, extractor_name = self.get_type_and_extractor_name(
                key_getter_str)
            if getter_type == "triggers":
                self.trigger_extractor_name_to_key_getter_str[
                    extractor_name] = key_getter_str
            elif getter_type == "arguments":
                self.argument_extractor_name_to_key_getter_str[
                    extractor_name] = key_getter_str

    @staticmethod
    def get_type_and_extractor_name(key_getter_str):
        getter_type = key_getter_str.split(".")[0]
        extractor_name = ".".join(key_getter_str.split(".")[1:])
        assert getter_type == "triggers" or getter_type == "arguments"
        return getter_type, extractor_name

    def _add_missing_vectors(self):

        key_to_dimensions = dict()
        for em, features in self.em_to_feature_dict.items():
            for key, feature_list in features.items():
                key_to_dimensions[key] = max(key_to_dimensions.get(key, 0),
                                             len(feature_list))
        for em, features in self.em_to_feature_dict.items():
            for key, dimensions in key_to_dimensions.items():
                if key not in features:
                    features[key] = [0.0] * dimensions

    def event_trigger_callback_builder(self):
        if len(self.trigger_extractor_name_to_key_getter_str) < 1:
            return lambda *args, **kwargs: None
        else:
            def event_mention_trigger_callback(serif_doc,
                                               event_mention,
                                               trigger_vecs):
                docid = serif_doc.docid
                self.em_to_serif_doc[event_mention] = serif_doc
                kvs = self.trigger_extractor_name_to_key_getter_str.items()

                if len(trigger_vecs) > 0:

                    # 1 dict per anchor
                    for trigger_vec_dict in trigger_vecs:
                        for extractor_name, key_getter_str in kvs:
                            feature_embs = None
                            if extractor_name == "bert":
                                sent_id, token_id = (
                                    trigger_vec_dict[extractor_name])
                                try:
                                    feature_embs = (
                                        self.bert_emb_cache.get_bert_emb(
                                            docid, sent_id, token_id))
                                except KeyError as e:
                                    logger.error(
                                        "Cannot find bert emb for {} {} {}"
                                        .format(docid, sent_id, token_id))
                                    pass
                                except IndexError as e:
                                    logger.error(
                                        "Cannot find bert emb for {} {} {}"
                                        .format(docid, sent_id, token_id))
                                    pass
                            else:
                                feature_embs = trigger_vec_dict.get(
                                    extractor_name, (None,)*3)[2]

                            if feature_embs is not None:
                                self.em_to_feature_dict.setdefault(
                                    event_mention, dict()).setdefault(
                                    key_getter_str, list()).append(feature_embs)

            return event_mention_trigger_callback

    def event_argument_callback_builder(self):

        # always run callback, so that arg names are collected

        def event_mention_argument_callback(serif_doc,
                                            event_mention,
                                            trigger_vecs,
                                            argument,
                                            argument_vecs):
            docid = serif_doc.docid
            self.em_to_serif_doc[event_mention] = serif_doc
            kvs = self.argument_extractor_name_to_key_getter_str.items()
            if len(argument_vecs) > 0:

                # 1 dict per node/key associated with argument
                for argument_vec_dict in argument_vecs:

                    # store arg actor names even if extractor isn't used
                    name = get_name(argument, event_mention)
                    for extractor_name in argument_vec_dict:
                        key_getter_str = "arguments.{}".format(
                            extractor_name)
                        self.em_to_names.setdefault(
                            event_mention, dict()).setdefault(
                            key_getter_str, set()).add(name)

                    for extractor_name, key_getter_str in kvs:
                        feature_embs = None
                        if extractor_name == "bert":
                            sent_id, token_id = (
                                argument_vec_dict[extractor_name])
                            try:
                                feature_embs = (
                                    self.bert_emb_cache.get_bert_emb(
                                        docid, sent_id, token_id))
                            except KeyError as e:
                                logger.error(
                                    "Cannot find bert emb for {} {} {}"
                                    .format(docid, sent_id, token_id))
                                pass
                            except IndexError as e:
                                logger.error(
                                    "Cannot find bert emb for {} {} {}"
                                    .format(docid, sent_id, token_id))
                                pass
                        else:
                            feature_embs = argument_vec_dict.get(
                                extractor_name, (None,)*6)[5]

                        if feature_embs is not None:
                            self.em_to_feature_dict.setdefault(
                                event_mention, dict()).setdefault(
                                key_getter_str, list()).append(feature_embs)

        return event_mention_argument_callback

    def accumulate_feature_embeddings(self):
        for event_mention in self.em_to_feature_dict.keys():

            # take mean for each feature across all anchors
            for key in self.trigger_extractor_name_to_key_getter_str.values():
                if key in self.em_to_feature_dict[event_mention]:
                    self.em_to_feature_dict[event_mention][key] = np.mean(
                        self.em_to_feature_dict[event_mention][key],
                        axis=0
                    ).tolist()

            # take mean for each feature across all arguments
            for key in self.argument_extractor_name_to_key_getter_str.values():
                if key in self.em_to_feature_dict[event_mention]:
                    self.em_to_feature_dict[event_mention][key] = np.mean(
                        self.em_to_feature_dict[event_mention][key],
                        axis=0
                    ).tolist()


def get_name(arg: serifxml3.EventMentionArg,
             event_mention: serifxml3.EventMention):
    name = arg.value.text
    if name is None and hasattr(arg.value, 'head'):
        name = arg.value.head.text
    sentence = event_mention.owner_with_type(serifxml3.Sentence)
    assert isinstance(sentence, serifxml3.Sentence)
    for actor_mention in sentence.actor_mention_set:
        mention = actor_mention.mention
        if mention == arg.value:
            if actor_mention.actor_name:
                name = actor_mention.actor_name
            elif actor_mention.geo_text:
                name = actor_mention.geo_text
            elif actor_mention.paired_agent_name:
                name = actor_mention.paired_agent_name
            elif actor_mention.paired_actor_name:
                name = actor_mention.paired_actor_name
            break
    return name


def get_original_sentence_with_em_marking(event_mention:serifxml3.EventMention):
    sentence = event_mention.owner_with_type(serifxml3.Sentence)
    assert isinstance(sentence, serifxml3.Sentence)
    sentence_theory = sentence.sentence_theory
    token_idx_to_token = dict()
    for token_idx, token in enumerate(sentence.token_sequence):
        token_idx_to_token[token_idx] = token
    token_to_token_idx = {v: k for k, v in token_idx_to_token.items()}

    token_to_token_left_marking= dict()
    token_to_token_right_marking = dict()

    for anchor_node in ([event_mention.anchor_node] +
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

class SerifNLPLingoFeatureExtractor(FeatureExtractor):
    def __init__(self,serif_list_path,
                                   npz_folder,
                                   doc_id_to_bert_npz_path,
                                   key_getter_str_list):
        super().__init__()
        self.serif_list_path = serif_list_path
        self.npz_folder = npz_folder
        self.doc_id_to_bert_npz_path = doc_id_to_bert_npz_path
        self.key_getter_str_list = key_getter_str_list

    def extract_features(self):
        bert_emb_cache = BertEmbCache(self.doc_id_to_bert_npz_path)
        nlplingo_feature_extractor = NLPLingoFeatureExtractor(bert_emb_cache,
                                                              self.key_getter_str_list)

        get_pretrained_embeddings(
            self.serif_list_path,
            self.npz_folder,
            nlplingo_feature_extractor.event_trigger_callback_builder(),
            nlplingo_feature_extractor.event_argument_callback_builder())

        # accumulate over arguments and anchors
        nlplingo_feature_extractor.accumulate_feature_embeddings()

        # don't fill in missing vectors with zeroes -- take intersection in pairwise
        # nlplingo_feature_extractor.add_missing_vectors()

        feature_id_to_feature = dict()
        for em, nlplingo_features in (
                nlplingo_feature_extractor.em_to_feature_dict.items()):
            serif_doc = nlplingo_feature_extractor.em_to_serif_doc[em]
            syn_nodes = set([em.anchor_node] + [a.anchor_node for a in em.anchors])
            syn_node_ids = sorted(i.id for i in syn_nodes)
            em_id = "{}_{}".format(serif_doc.docid, "#".join(syn_node_ids))
            features = {key_getter_str: nlplingo_features[key_getter_str]
                        for key_getter_str in self.key_getter_str_list
                        if key_getter_str in nlplingo_features}
            aux = {"originalText": get_original_sentence_with_em_marking(em),
                   "argument_names": {
                       key_getter_str: list(names) for key_getter_str, names in
                       nlplingo_feature_extractor.em_to_names.get(em, {}).items()}}
            fuzzy_feature = feature_id_to_feature.setdefault(
                em_id, Feature(em_id, dict(), dict()))
            fuzzy_feature.features.update(features)
            fuzzy_feature.aux.update(aux)
        return list(feature_id_to_feature.values())

