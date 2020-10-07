import argparse
import codecs
import json
import os
import sys

import numpy as np

import serifxml3
from serif.theory.mention import Mention
from serif.theory.syn_node import SynNode
from serif.theory.value_mention import ValueMention

from similarity.event_and_arg_emb_pairwise import serif_nlplingo_feature_extractor
from similarity.event_and_arg_emb_pairwise import run

def get_docid_to_embeddings(embeddings_dir):
    embeddings_map = {}
    if embeddings_dir is not None:
        for npz in os.listdir(embeddings_dir):
            if npz.endswith('.npz'):
                docid = npz[:-len('.npz')]
                embeddings_map[docid] = os.path.join(embeddings_dir, npz)
    return embeddings_map


def load_embeddings(docid, npz_files):
    """
    Loads an npz file containing embeddings generated by NlpLingo.
    The output of this function has the following format:
    {
        "triggers": {
            <trigger_extractor_name>: {

                # key for triggers:
                (int(<start_offset>), int(<end_offset>)): (

                    int(<start_offset>),
                    int(<end_offset>),
                    ndarray(<trigger_embedding>)), [...]

            }, [...]
        },

        "arguments": {
            <argument_extractor_name>: {

                # key for arguments:
                (str(<trigger_class_label>),
                 int(<trigger_start_offset>),
                 int(<trigger_end_offset>),
                 int(<argument_start_offset>),
                 int(<argument_end_offset>)): (

                    str(<trigger_class_label>),
                    int(<trigger_start_offset>),
                    int(<trigger_end_offset>),
                    int(<argument_start_offset>),
                    int(<argument_end_offset>),
                    ndarray(<argument_embedding>)), [...]

            }, [...]
        },

        "bert": {
            # for triggers, the trigger key above:
            (int(<start_offset>), int(<end_offset>)): (

                int(<sentence_id>),
                int(<token_id>)),

            # for arguments, the argument key above:
            (str(<trigger_class_label>),
             int(<trigger_start_offset>),
             int(<trigger_end_offset>),
             int(<argument_start_offset>),
             int(<argument_end_offset>)): (

                int(<sentence_id>),
                int(<token_id>)),

        }
    }

    :param docid: a docid
    :param npz_files: a docid2filepath dict for NlpLingo npz output files
    :return: dict as described above
    """
    npz_file = npz_files.get(docid)
    if npz_file is None:
        return None
    else:
        ret = {}
        np_object = np.load(npz_file, allow_pickle=True)
        ret["bert"] = np_object["bert"].item()
        try:
            ret["triggers"] = np_object["triggers"].item()
        except KeyError:
            ret["trigger"] = None
        try:
            ret["arguments"] = np_object["arguments"].item()
        except KeyError:
            ret["arguments"] = None
        return ret


def get_serif_objects(serifxml_path):
    serif_doc = serifxml3.Document(serifxml_path)
    event_mentions = []

    for sentence_id, sentence in enumerate(serif_doc.sentences):
        st = sentence.sentence_theories[0]
        """:type: serifxml3.SentenceTheory"""
        em_set = []
        if sentence.event_mention_set is not None:
            em_set = sentence.event_mention_set
        elif st.event_mention_set is not None:
            em_set = st.event_mention_set
        event_mentions.extend(list(em_set))

    return serif_doc, event_mentions


def get_embedding_keys(event_mentions):
    """
    Find vector keys for event mentions and arguments.
    :param event_mentions:
    :return:
    """
    event_mention_map = {}
    argument_map = {}
    for event_mention in event_mentions:

        # get the offset pairs for all anchors in this EM
        trig_offset_list = [
            # end offset in NLPLingo is Serif's edt offset -1
            (a.start_char, a.end_char + 1)
            for a in set([event_mention.anchor_node] +
                         [a.anchor_node for a in event_mention.anchors])]
        event_mention_map[event_mention] = trig_offset_list

        for argument in event_mention.arguments:
            arg_offset_set = set()
            if isinstance(argument.value, Mention):
                arg_node = argument.value.head
            elif isinstance(argument.value, ValueMention):
                arg_node = argument.value
            else:
                raise ValueError(
                    "argument.value should be a Mention or a ValueMention")

            # end offset in NLPLingo is Serif's edt offset -1
            arg_offset_set.add((arg_node.start_char, arg_node.end_char + 1))

            # NlpLingo and SERIF disagree on how many tokens a "head" can be.
            if isinstance(arg_node, SynNode):
                for node in arg_node:
                    arg_offset_set.add((node.start_char, node.end_char + 1))

            # get all possible keys of the mention
            arg_offset_set = {
                (trigger_type.event_type,) + anchor_offsets + arg_offsets
                for anchor_offsets in trig_offset_list
                for arg_offsets in arg_offset_set
                for trigger_type in event_mention.event_types
                + event_mention.factor_types
            }

            argument_map[argument] = list(arg_offset_set)

    return event_mention_map, argument_map


def get_argument_vectors_from_keys(embeddings, keys, sentence_index, token_index):
    return _get_vectors_from_keys(embeddings, keys, "arguments", sentence_index, token_index)


def get_trigger_vectors_from_keys(embeddings, keys, sentence_index, token_index):
    return _get_vectors_from_keys(embeddings, keys, "triggers", sentence_index, token_index)


def _get_vectors_from_keys(embeddings, keys, vector_type, s_idx, t_idx):
    ret = []
    for key in keys:
        if key in embeddings['bert']:
            model_vectors = {
                extractor: vectors[key]
                for extractor, vectors in embeddings[vector_type].items()
                if key in vectors}
            model_vectors['bert'] = embeddings['bert'][key]
            ret.append(model_vectors)
    if len(ret) == 0 and s_idx is not None and t_idx is not None:
        model_vectors = {'bert': (s_idx, t_idx)}
        ret.append(model_vectors)

    # # debug
    # if not ret:
    #     print('$$$', vector_type, keys, embeddings['bert'].keys())
    return ret


def get_pretrained_embeddings(serifxml_list, npz_dir, event_mention_trigger_callback, event_mention_argument_callback):
    # collect npzs
    npz_dir = os.path.realpath(os.path.abspath(npz_dir))
    npz_map = get_docid_to_embeddings(npz_dir)

    # collect serifxmls
    serifxml_list = os.path.realpath(os.path.abspath(serifxml_list))
    with codecs.open(serifxml_list, 'r', encoding='utf8') as fh:
        serifxmls = [path.strip() for path in fh.readlines()]

    # process serifxmls
    for path in serifxmls:
        serif_doc, event_mentions = get_serif_objects(path)
        docid = serif_doc.docid
        npz = load_embeddings(docid, npz_map)

        if npz is None:  # NLPLingo found nothing for this document.
            continue

        # get maps from serif objects to vector addresses
        event_mention_to_vector_keys, argument_to_vector_keys = (
            get_embedding_keys(event_mentions))

        # get embeddings themselves
        for event_mention, trigger_keys in event_mention_to_vector_keys.items():
            # arbitrarily chosen from among the EventMention's anchors
            s_idx = event_mention.anchor_node.sent_no
            t_idx = event_mention.anchor_node.start_token.original_token_index
            trigger_vecs = get_trigger_vectors_from_keys(
                npz, trigger_keys, s_idx, t_idx)

            event_mention_trigger_callback(
                serif_doc, event_mention, trigger_vecs)

            for argument in event_mention.arguments:
                t_idx = None
                if hasattr(argument.value, "start_token"):
                    t_idx = argument.value.start_token.original_token_index
                else:
                    t_idx = argument.value.head.start_token.original_token_index
                argument_keys = argument_to_vector_keys[argument]
                argument_vecs = get_argument_vectors_from_keys(
                    npz, argument_keys, s_idx, t_idx)
                event_mention_argument_callback(
                    serif_doc,
                    event_mention,
                    trigger_vecs,
                    argument,
                    argument_vecs)


def event_mention_trigger_print_callback_builder(bert_cache=None):

    def event_mention_trigger_print_callback(serif_doc, event_mention, trigger_vecs):
        print("\n### {} \n{}".format(serif_doc.docid, event_mention.anchor_node, event_mention.event_type))
        print(trigger_vecs)
        if bert_cache is not None and len(trigger_vecs) > 0:
            bert_indices = trigger_vecs[0]['bert']  # 1st anchor arbitrarily used
            bert_embedding = bert_cache.get_bert_emb(serif_doc.docid, *bert_indices)
            print('BERT:\n{}'.format(bert_embedding))
    return event_mention_trigger_print_callback


def event_mention_argument_print_callback_builder(bert_cache=None):
    def event_mention_argument_print_callback(serif_doc, event_mention, trigger_vecs, argument, argument_vecs):
        print("--- {} \n{}".format(argument.role, argument.value))
        print(argument_vecs)
        if bert_cache is not None and len(argument_vecs) > 0:
            bert_indices = argument_vecs[0]['bert']  # 1st SynNode arbitrarily used
            bert_embedding = bert_cache.get_bert_emb(serif_doc.docid, *bert_indices)
            print('BERT:\n{}'.format(bert_embedding))
    return event_mention_argument_print_callback


if __name__ == '__main__':
    serifxmls = sys.argv[1]
    npzs = sys.argv[2]
    bert_filelist = sys.argv[3]
    # serifxmls = "/nfs/raid88/u10/users/hqiu/runjob/expts/Hume/fuzzy_test.012020/dump_serifxml_into_features/batch_files/00000"
    # npzs = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/nlplingo_decoder.012020.modified/nn_events/embeddings"
    # bert_filelist = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/causeex_sams_estonia.120719.121419/bert/bert_npz.list"
    docid_to_bertfile = run.create_doc_id_to_path(bert_filelist, '.npz')
    bert_emb_cache = serif_nlplingo_feature_extractor.BertEmbCache(docid_to_bertfile)
    get_pretrained_embeddings(serifxmls, npzs, event_mention_trigger_print_callback_builder(bert_emb_cache),
                              event_mention_argument_print_callback_builder(bert_emb_cache))