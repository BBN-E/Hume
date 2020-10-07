import os
import sys
import codecs
from collections import defaultdict
import logging
import argparse
import json

import serifxml3 as serifxml


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)


class Token(object):
    def __init__(self, start_char, end_char, token_index, text, pos_tag, sentence_index):
        self.start_char = start_char
        self.end_char = end_char
        self.token_index = token_index
        self.text = text
        self.pos_tag = pos_tag
        self.sentence_index = sentence_index


class EntityMention(object):
    def __init__(self, start_char, end_char, text, canonical_name, label, tokens=None, head_tokens=None):
        self.start_char = start_char
        self.end_char = end_char
        self.text = text
        if canonical_name is None:
            self.canonical_name = canonical_name
        else:
            self.canonical_name = canonical_name.lower()
        self.label = label
        self.tokens = tokens
        self.head_tokens = head_tokens
        """:type: list[Token]"""

    def get_indices_lists(self):
        head_indices = []
        all_indices = []
        for t in self.head_tokens:
            head_indices.append((t.sentence_index, t.token_index))
        for t in self.tokens:
            all_indices.append((t.sentence_index, t.token_index))
        return [head_indices, all_indices]

    def to_string(self):
        tokens_text = '_'.join(token.text for token in self.tokens)
        head_tokens_text = '_'.join(token.text for token in self.head_tokens)
        return '({},{}) text={} canonical_name={} label={} tokens_text={} head_tokens_text={}'.format(
            self.start_char, self.end_char, self.text, self.canonical_name, self.label, tokens_text, head_tokens_text)

    def to_dict(self):
        d = dict()
        d['canonical_name'] = self.canonical_name
        d['text'] = ' '.join(t.text for t in self.head_tokens)
        d['start'] = self.head_tokens[0].start_char
        d['end'] = self.head_tokens[-1].end_char
        d['label'] = self.label
        d['indices_lists'] = self.get_indices_lists()
        return d


class EntityMentionGenerator(object):
    @staticmethod
    def get_entity_mentions(st, doc, tokens):
        """
        :type st: serifxml.SentenceTheory
        :type doc: serifxml.Document
        :type tokens: list[Token]
        :rtype: list[EntityMention]
        """

        mention_to_entity = dict()
        for entity in doc.entity_set:
            for mention in entity.mentions:
                mention_to_entity[mention] = entity

        entity_canonical_name = EntityMentionGenerator._entity_to_canonical_name(doc)
        """:type: dict[serifxml.Entity, str]"""

        ret = []
        for m in st.mention_set:
            if m.entity_subtype != 'UNDET':
                m_type = '{}.{}'.format(m.entity_type, m.entity_subtype)
            else:
                m_type = m.entity_type
            if m_type == 'OTH':
                continue

            canonical_name = None
            if m in mention_to_entity:
                entity = mention_to_entity[m]
                assert entity in entity_canonical_name
                canonical_name = entity_canonical_name[entity]

            start_char = m.syn_node.start_token.start_edt
            end_char = m.syn_node.end_token.end_edt

            em_tokens = get_token_sequence_for_offsets(tokens, start_char, end_char)
            em_head_tokens = get_token_sequence_for_offsets(tokens, m.head.start_token.start_edt, m.head.end_token.end_edt)
            em = EntityMention(start_char, end_char, m.text, canonical_name, m_type, tokens=em_tokens, head_tokens=em_head_tokens)
            ret.append(em)

        return EntityMentionGenerator._discard_covered_entity_mentions(ret)


    @staticmethod
    def _get_longest_string(strings):
        longest_string = None
        l = None
        for e in strings:
            if l is None or len(e) > l:
                longest_string = e
                l = len(e)
        return longest_string

    @staticmethod
    def _entity_to_canonical_name(doc):
        """
        Map each entity to its canonical name
        :type doc: serifxml.Document
        :rtype: dict[Entity, str]
        """
        ret = dict()

        entity_to_actor_entity = dict()
        for actor_entity in doc.actor_entity_set:
            if actor_entity.confidence >= 0.55:
                entity_to_actor_entity[actor_entity.entity] = actor_entity

        for entity in doc.entity_set:
            if entity in entity_to_actor_entity:
                actor_entity = entity_to_actor_entity[entity]
                if actor_entity.actor_name != 'UNKNOWN-ACTOR':
                    ret[entity] = actor_entity.actor_name.lower()
                    continue

            # if the entity is not associated with an actor, then we loop through mentions of the entity
            name_mentions_text = set()
            all_mentions_text = set()
            for mention in entity.mentions:
                all_mentions_text.add(mention.head.text)
                if mention.mention_type == serifxml.MentionType.name:
                    name_mentions_text.add(mention.head.text)
            if len(name_mentions_text) > 0:
                ret[entity] = EntityMentionGenerator._get_longest_string(name_mentions_text).lower()
            else:
                ret[entity] = EntityMentionGenerator._get_longest_string(all_mentions_text).lower()

        return ret

    @staticmethod
    def _discard_covered_entity_mentions(entity_mentions):
        """
        :type entity_mentions: list[EntityMention]
        :return: list[EntityMention]
        """

        covered_indices = set()
        for i, em1 in enumerate(entity_mentions):
            covered = False
            em1_start = em1.head_tokens[0].start_char
            em1_end = em1.head_tokens[-1].end_char

            for j, em2 in enumerate(entity_mentions):
                em2_start = em2.head_tokens[0].start_char
                em2_end = em2.head_tokens[-1].end_char

                if i != j:
                    if em2_start <= em1_start and em1_end <= em2_end:
                        covered = True
                        break

            if covered:
                covered_indices.add(i)

        ret = []
        for i, em in enumerate(entity_mentions):
            if i not in covered_indices:
                ret.append(em)

        return ret


class SemanticPhrase(object):
    def __init__(self, semantic_phrase, event_type_and_score_pairs, tokens):
        """
        :type semantic_phrase: str
        :type event_types: list[list[str, float]]
        :type tokens: list[Token]
        """
        self.semantic_phrase = semantic_phrase
        self.event_type_and_score_pairs = sorted(
            event_type_and_score_pairs,
            key=lambda x: (-x[1], x[0])
        )
        self.tokens = tokens

    def get_indices_lists(self):
        all_indices = []
        for t in self.tokens:
            all_indices.append((t.sentence_index, t.token_index))
        return [all_indices]

    def to_dict(self):
        d = dict()
        d['text'] = self.semantic_phrase
        d['event_types'] = self.event_type_and_score_pairs
        d['indices_lists'] = self.get_indices_lists()
        return d


class Action(object):
    def __init__(self, start_char, end_char, tokens):
        self.start_char = start_char
        self.end_char = end_char
        self.tokens = tokens

    def to_dict(self):
        d = dict()
        d['text'] = ' '.join(t.text for t in self.tokens)
        d['start'] = self.start_char
        d['end'] = self.end_char
        return d


class ActionGenerator(object):
    @staticmethod
    def get_actions(st, tokens):
        """
        :type st: serifxml.SentenceTheory
        :type tokens: list[Tokens]
        """
        ret = []
        ret_semantic_phrases = []
        for em in st.event_mention_set:
            em_start = int(em.semantic_phrase_start)
            em_end = int(em.semantic_phrase_end)

            em_tokens = tokens[em_start:em_end+1]
            em_phrase = ' '.join(token.text for token in em_tokens)

            event_type_score_pairs = [[et.event_type, et.score] 
                                      for et in em.event_types]
            ret_semantic_phrases.append(SemanticPhrase(em_phrase,
                                                       event_type_score_pairs,
                                                       em_tokens))

            for anchor in em.anchors:
                start_char = anchor.anchor_node.start_token.start_edt
                end_char = anchor.anchor_node.end_token.end_edt

                anchor_tokens = get_token_sequence_for_offsets(tokens, start_char, end_char)
                ret.append(Action(start_char, end_char, anchor_tokens))

        return ret, ret_semantic_phrases

    @staticmethod
    def discard_actions_covered_by_entity_mentions(actions, entity_mentions):
        """
        :type actions: list[Action]
        :type entity_mentions: list[EntityMention]
        :rtype: list[Action]
        """
        ret = []

        for action in actions:
            action_start = action.tokens[0].start_char
            action_end = action.tokens[-1].end_char
            covered = False

            for em in entity_mentions:
                em_start = em.head_tokens[0].start_char
                em_end = em.head_tokens[-1].end_char

                if em_start <= action_start and action_end <= em_end:
                    covered = True
                    break

            if not covered:
                ret.append(action)

        return ret


def to_tokens(st, sentence_index):
    """
    :type st: serifxml.SentenceTheory
    :rtype: list[Token]
    """
    ret = []

    root = st.parse.root
    """:type: serifxml.SynNode"""
    for i, t in enumerate(root.terminals):
        token = Token(t.start_token.start_edt, t.end_token.end_edt, i, t.text, t.parent.tag, sentence_index)
        ret.append(token)
    return ret


def get_token_sequence_for_offsets(tokens, start_char, end_char):
    """
    :type tokens: list[Token]
    :type start_char: int
    :type end_char: int
    :return: list[Token]
    """
    start_index = None
    end_index = None

    for i, token in enumerate(tokens):
        if token.start_char == start_char and start_index is None:
            start_index = i
        if token.end_char == end_char and end_index is None:
            end_index = i

    assert start_index is not None
    assert end_index is not None

    return tokens[start_index:end_index + 1]


def parse_serifxml(doc):
    """
    :doc: serifxml.Document
    """
    info_dict = []

    docid = doc.docid

    for st_index, sentence in enumerate(doc.sentences):
        st = sentence.sentence_theories[0]
        """:type: serifxml.SentenceTheory"""
        if len(st.token_sequence) == 0:
            continue

        tokens = to_tokens(st, st_index)
        """:type: list[Token]"""

        entity_mentions = EntityMentionGenerator.get_entity_mentions(st, doc, tokens)
        """:type: list[EntityMention]"""

        #print(' '.join(token.text for token in tokens))
        #for em in entity_mentions:
        #    print(em.to_string())

        all_actions, all_semantic_phrases = ActionGenerator.get_actions(st, tokens)
        pruned_actions = ActionGenerator.discard_actions_covered_by_entity_mentions(all_actions, entity_mentions)

        d = dict()
        d['docid'] = docid
        d['text'] = ' '.join(t.text for t in tokens)
        d['semantic_phrases'] = [semantic_phrase.to_dict() for semantic_phrase in all_semantic_phrases]
        d['actions'] = [action.to_dict() for action in pruned_actions]
        d['entity_mentions'] = [em.to_dict() for em in entity_mentions]
        info_dict.append(d)

    return info_dict


def print_entity_mentions(doc):
    for st_index, sentence in enumerate(doc.sentences):
        st = sentence.sentence_theories[0]

        for m in st.mention_set:
            if m.entity_subtype != 'UNDET':
                m_type = '{}.{}'.format(m.entity_type, m.entity_subtype)
            else:
                m_type = m.entity_type
            print('id={} text={} type={} head={}'.format(m.id, m.text, m_type, m.head.text))


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('--serifxml_filelist', required=True)
    parser.add_argument('--outfile', required=True)
    args = parser.parse_args()


    with codecs.open(args.serifxml_filelist, 'r', encoding='utf-8') as f:
        filepaths = [line.strip() for line in f]

    infos = []
    for filepath in filepaths:
        doc = serifxml.Document(filepath)
        #print('#### {} ####'.format(doc.docid))
        infos.extend(parse_serifxml(doc))
        #print('')

    with codecs.open(args.outfile, 'w', encoding='utf-8') as o:
        o.write(json.dumps(infos, indent=4, cls=ComplexEncoder, ensure_ascii=False))
