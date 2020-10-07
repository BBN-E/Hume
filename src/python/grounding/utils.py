
import enum
import io
import json
import os
import sys

import numpy
# from scipy.spatial.distance import cosine
# from annoy import AnnoyIndex

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'knowledge_base'))
    from internal_ontology import utility as ontology_utils
except ImportError as e:
    raise e


numpy.random.seed(123456)


class AnnoyModel(object):

    def __init__(self, embeddings, annoy_idx):
        self.embeddings = embeddings
        self.embeddings_inv = {y:x for x,y in embeddings.items()}
        self.annoy_idx = annoy_idx

    @staticmethod
    def load_model(root_node, embeddings):
        pass
        # pull out the code used to create embeddings used by nodes/candidates
        # - participants embedding (A)
        # - properties embedding (P)
        # - processes embedding (E)
        # - (name/string/exemplars embedding)
        # for each ontology node index its A/P/E/Name/Exemplars embeddings
        # for a mention candidate, get (1-?) best matching A/P/E/N/X embedding
        # combine the results in some way


class SimilarityMode(enum.Enum):
    COMPARE_MENTION_STRING_TO_EXEMPLARS_MAX = 1
    COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG = 2
    COMPARE_MENTION_STRING_TO_TYPE_NAME = 3
    COMPARE_MENTION_SENTENCES_TO_TEXTUAL_MENTIONS_MAX = 4 # not implemented
    COMPARE_MENTION_SENTENCES_TO_TEXTUAL_MENTIONS_AVG = 5 # not implemented
    COMPARE_MENTION_PROCESSES_TO_EXEMPLARS_MAX = 6 # not implemented
    COMPARE_MENTION_PARTICIPANTS_TO_EXEMPLARS_MAX = 7 # not implemented
    COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG = 8
    COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT = 9


def get_similarity(mention_candidate, node, mode, embeddings_lookup):
    """
    :type mention_candidate: mention_candidate.MentionCandidate
    :type node: internal_ontology.node.Node
    :param mode:
    :param embeddings_lookup:
    :return:
    """

    if mode == SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_MAX:
        mention_embedding = mention_candidate.get_mention_string_embedding()
        if mention_embedding is None:
            mention_embedding = ontology_utils.get_embeddings_for_mention_text(
                mention_candidate.get_mention_string(),
                embeddings_lookup
            )
            mention_candidate.set_mention_string_embedding(mention_embedding)
        max_score = 0.0
        for exemplar, exemplar_embedding in node.get_exemplar_to_embeddings().items():
            score = get_vec_similarity(mention_embedding, exemplar_embedding)
            if score > max_score:
                max_score = score
        return max_score

    elif mode == SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME:
        mention_embedding = mention_candidate.get_mention_string_embedding()
        if mention_embedding is None:
            mention_embedding = ontology_utils.get_embeddings_for_mention_text(
                mention_candidate.get_mention_string(),
                embeddings_lookup
            )
            mention_candidate.set_mention_string_embedding(mention_embedding)
        node_name_embedding = node.get_name_embeddings()
        return max(0.0,
                   get_vec_similarity(mention_embedding, node_name_embedding))

    elif mode == SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG:
        mention_embedding = mention_candidate.get_mention_string_embedding()
        if mention_embedding is None:
            mention_embedding = ontology_utils.get_embeddings_for_mention_text(
                mention_candidate.get_mention_string(),
                embeddings_lookup
            )
            mention_candidate.set_mention_string_embedding(mention_embedding)
        node_average_exemplar_embedding = node.get_average_exemplar_embeddings()

        # debugging code for identifying exemplars with high impact on scores
        '''
        if '_STRING_TO_FIND' in mention_candidate.get_original_mention_string():
            print('#########')
            for e, v2 in node._exemplar_embedding_lookup.items():
                t_set = set()
                for t in ontology_utils.get_filtered_tokens(
                        mention_candidate.get_mention_string()):

                    v1 = embeddings_lookup.get(t)
                    s = get_vec_similarity(v1, v2)
                    print('Mention token: {}'.format(t))
                    print('Exemplar: {}'.format(e))
                    print('Similarity: {}'.format(s))
                    t_set.add(t)

                seen = set()
                for t1 in t_set:
                    for t2 in t_set:
                        if t1 != t2 and (t1, t2) not in seen:
                            seen.add((t1, t2))
                            seen.add((t2, t1))
                            v1 = ontology_utils.get_average_embeddings(
                                [t1, t2], embeddings_lookup)
                            s = get_vec_similarity(v1, v2)
                            print('Mention token pair: {}, {}'.format(t1, t2))
                            print('Exemplar: {}'.format(e))
                            print('Similarity: {}'.format(s))

                v1 = mention_embedding
                s = get_vec_similarity(v1, v2)
                print('Full mention: {}'.format(
                    mention_candidate.get_mention_string()))
                print('Exemplar: {}'.format(e))
                print('Similarity: {}'.format(s))

                print('------')
            print('#########')
        '''

        return max(0.0, get_vec_similarity(mention_embedding,
                                           node_average_exemplar_embedding))

    elif mode == SimilarityMode.COMPARE_MENTION_SENTENCES_TO_TEXTUAL_MENTIONS_MAX:
        raise NotImplementedError

    elif mode == SimilarityMode.COMPARE_MENTION_SENTENCES_TO_TEXTUAL_MENTIONS_AVG:
        raise NotImplementedError

    elif mode == SimilarityMode.COMPARE_MENTION_PROCESSES_TO_EXEMPLARS_MAX:
        raise NotImplementedError

    elif mode == SimilarityMode.COMPARE_MENTION_PARTICIPANTS_TO_EXEMPLARS_MAX:
        raise NotImplementedError

    elif mode == SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG:

        # TODO this logic should be moved to creation of the MentionCandidatel

        participants_embedding = mention_candidate.get_participants_embedding()
        if participants_embedding is None:
            participants_embedding = ontology_utils.get_embeddings_for_mention_text(
                u' '.join(mention_candidate.get_participants()),
                embeddings_lookup)
            mention_candidate.set_participants_embedding(participants_embedding)

        processes_embedding = mention_candidate.get_processes_embedding()
        if processes_embedding is None:
            processes_embedding = ontology_utils.get_embeddings_for_mention_text(
                u' '.join(mention_candidate.get_processes()),
                embeddings_lookup)
            mention_candidate.set_processes_embedding(processes_embedding)

        properties_embedding = mention_candidate.get_properties_embedding()
        if properties_embedding is None:
            properties_embedding = ontology_utils.get_embeddings_for_mention_text(
                u' '.join(mention_candidate.get_properties()),
                embeddings_lookup)
            mention_candidate.set_properties_embedding(properties_embedding)

        # values_embedding = ontology_utils.get_embeddings_for_mention_text(
        #     ...
        number_of_data_types_in_candidate = sum(
            [int(type(v) is numpy.ndarray)
             for v in [participants_embedding,
                       processes_embedding,
                       properties_embedding]])

        node_participants_embedding = node.get_average_participants_embedding()
        node_processes_embedding = node.get_average_processes_embedding()
        node_properties_embedding = node.get_average_properties_embedding()

        similarities = [
            max(0.0, get_vec_similarity(
                participants_embedding, node_participants_embedding)),
            max(0.0, get_vec_similarity(
                processes_embedding, node_processes_embedding)),
            max(0.0, get_vec_similarity(
                properties_embedding, node_properties_embedding)),
            # max(0.0, get_vec_similarity(
            #    values_embedding, node_average_exemplar_embedding)),
        ]

        # TODO use weights for different types

        similarities = [s for s in similarities if s > 0]
        if len(similarities) == 0:
            return 0.0
        else:
            return sum(similarities) / number_of_data_types_in_candidate

    elif mode == SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT:
        node_embedding = node.get_average_contextual_embedding()
        mention_embedding = mention_candidate.get_contextual_embedding()
        if mention_embedding is None or node_embedding is None:
            return 0.0
        else:
            return max(0.0,
                       get_vec_similarity(node_embedding, mention_embedding))

    else:
        raise NotImplementedError


def get_legacy_cache_key(mention_candidate, internal_entry_point_strs, root_str):
    return u'|||'.join([
        root_str,
        u';'.join(internal_entry_point_strs),
        mention_candidate.get_original_mention_string()
    ])


def read_stopwords_from_hume_resources(path):
    sws = set()
    with io.open(path, 'r', encoding='utf8') as f:
        for line in f:
            sws.add(line.strip())
    return sws


def read_keywords_from_bbn_annotation(path):
    kws = {'participants': set(), 'processes': set(), 'properties': set()}
    with io.open(path, 'r', encoding='utf8') as f:
        for line in f:
            line = line.strip()
            kw = line.split('\t')[-1]
            if line.startswith('a'):
                kws['participants'].add(kw)
            elif line.startswith('e'):
                kws['processes'].add(kw)
            elif line.startswith('p'):
                kws['properties'].add(kw)
    return kws


def get_vec_similarity(vec1, vec2):
    if any(type(v) is not numpy.ndarray for v in [vec1, vec2]):
        return 0.0
    #c = 1 - cosine(vec1, vec2)  # 2-3x slower than np
    return numpy.dot(vec1, vec2) / (numpy.linalg.norm(vec1) * numpy.linalg.norm(vec2))


def merge_groundings(groundings, new_groundings):
    for grounding, score in new_groundings.items():
        if grounding in groundings:
            if score > groundings[grounding]:
                groundings[grounding] = score
        else:
            groundings[grounding] = score


def load_json(json_path):
    with io.open(json_path, 'r', encoding='utf8') as fh:
        return json.load(fh)


def load_contextual_npz(npz_path, truncation_span=None):
    with numpy.load(npz_path, allow_pickle=True) as doc_embedding_data:
        return truncation_npz(doc_embedding_data,truncation_span)

def truncation_npz(doc_embedding_data, truncation_span=None):
    contextual_embeddings = doc_embedding_data['embeddings']
    if truncation_span is not None:
        start, end = [int(x) for x in truncation_span.split(':')]
        for i in range(len(contextual_embeddings)):
            contextual_embeddings[i] = (
                contextual_embeddings[i][:, start:end])
    # contextual_tokens = doc_embedding_data['tokens']  # unused
    contextual_token_map = doc_embedding_data['token_map']
    return contextual_embeddings, contextual_token_map

def build_docid_to_npz_map(npz_file_list):
    docid_to_npz = dict()
    if os.path.isfile(npz_file_list):
        with open(npz_file_list, 'r') as fh:
            for npz_file_path in fh:
                npz_file_path = npz_file_path.strip()
                docid = os.path.basename(npz_file_path).replace(".npz", "")
                docid_to_npz[docid] = npz_file_path
    return docid_to_npz


def get_serif_event_mention_to_contextual_embedding(
        sentence_theory,
        sentence_index,
        contextual_embeddings,
        contextual_token_map):
    """
    :param sentence_theory: a serifxml3.SentenceTheory
    :param sentence_index: index of sentence_theory's sentence in serifxml
    :param contextual_embeddings:
        nump.ndarray of shape (#_sentences, ) where each row is of shape
        (#_contextualized_tokens, #_dimensions_in_embedding)
        -- as a side note, BERT creates two "extra" wordpieces [CLS] and [SEP].
    :param contextual_token_map:
        nump.ndarray of shape (#_sentences, ) where each row contains
        #_serifxml_tokens_in_sentence columns, whose values are the
        contextualized_token_index
    :return:
        tuple(dict(event_mention: numpy.ndarray),
              dict(event_mention: list(numpy.ndarray)))
    """
    token_index_to_token_map = {
        i: t for (i, t) in enumerate(sentence_theory.token_sequence)}
    token_to_token_index_map = {
        t: i for (i, t) in token_index_to_token_map.items()}
    mention_to_embedding = dict()
    mention_to_anchor_embeddings = dict()
    for event_mention in sentence_theory.event_mention_set:
        anchor_embeddings = []
        for anchor in event_mention.anchors:
            anchor_node = anchor.anchor_node

            # TODO something more sophisticated?  Average of anchor?
            head_token = anchor_node.end_token
            head_token_index = token_to_token_index_map[head_token]

            # BERT may not embed an anchor because of sentence size limits
            sentence_contextual_token_map = contextual_token_map[sentence_index]
            if sentence_contextual_token_map.shape[0] > head_token_index:
                contextual_head_token_index = (
                    sentence_contextual_token_map[head_token_index])
                head_token_embedding = contextual_embeddings[
                    sentence_index][contextual_head_token_index]
                anchor_embeddings.append(head_token_embedding)
            else:
                print("Dropped due to BERT size limits")

        if len(anchor_embeddings) > 0:
            mention_embedding = ontology_utils.get_average_of_vectors(
                anchor_embeddings)
            mention_to_embedding[event_mention] = mention_embedding
            mention_to_anchor_embeddings[event_mention] = anchor_embeddings

    return mention_to_embedding, mention_to_anchor_embeddings


def read_test_json_to_mention_candidates(path):
    with io.open(path, 'r', encoding='utf8') as f:
        j = json.load(f)
    ret = []
    for mc_dict in j:
        text = mc_dict['text']
        entry_points = mc_dict.get('entry_points', [])
        sentence = mc_dict.get('sentence', 'DUMMY')
        mc = MentionCandidate(text, sentence)
        ret.append(mc)
    return ret
