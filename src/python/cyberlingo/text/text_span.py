from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

import re

from cyberlingo.common.utils import Struct
from cyberlingo.common.utils import IntPair

span_types = Struct(TEXT='TEXT', SENTENCE='SENTENCE', TOKEN='TOKEN', ENTITY_MENTION='ENTITY_MENTION',
                    EVENTSPAN='EVENTSPAN', ANCHOR='ANCHOR', EVENT_ARGUMENT='EVENT_ARGUMENT')

"""Classes here:
Span (this is abstract)

EntityMention(Span)
Anchor(Span)
EventSpan(Span)
EventArgument(Span)

Token(Span)
Sentence(Span)
"""

class Span(object):
    """An abstract class. A Span can be any sequence of text
    :int_pair: representing the start and end character offsets of this span
    :text: the text of this span
    """

    __metaclass__ = ABCMeta

    def __init__(self, int_pair, text):
        self.int_pair = int_pair
        self.text = text

    def start_char_offset(self):
        return self.int_pair.first

    def end_char_offset(self):
        return self.int_pair.second

    @abstractmethod
    def span_type(self):
        """Return a string representing the type of span this is."""
        pass

class TextSpan(Span):
    """A simple span of texts"""
    def __init__(self, int_pair, text):
        Span.__init__(self, int_pair, text)

    def span_type(self):
        return span_types.TEXT

class EntityMention(Span):
    """A consecutive span representing an entity mention.
    label: the NER type, e.g. Person, Organization, GPE
    """

    time_words = ['time', 'a.m.', 'am', 'p.m.', 'pm', 'day', 'days', 'week', 'weeks', 'month', 'months', 'year',
                  'years', 'morning', 'afternoon', 'evening', 'night', 'anniversary', 'second', 'seconds', 'minute',
                  'minutes', 'hour', 'hours', 'decade', 'decades', 'january', 'february', 'march', 'april', 'may',
                  'june', 'july', 'august', 'september', 'october', 'november', 'december', 'today', 'yesterday',
                  'tomorrow', 'past', 'future', 'present', 'jan', 'jan.', 'feb', 'feb.', 'mar', 'mar.', 'apr', 'apr.',
                  'jun', 'jun.', 'jul', 'jul.', 'aug', 'aug.', 'sept', 'sept.', 'oct', 'oct.', 'nov', 'nov.', 'dec',
                  'dec.']

    def __init__(self, id, int_pair, text, label):
        Span.__init__(self, int_pair, text)
        self.id = id
        self.label = label
        self.tokens = None
        """:type: list[text.text_span.Token]"""

    def with_tokens(self, tokens):
        """:type tokens: list[text.text_span.Token]"""
        self.tokens = tokens

    def coarse_label(self):
        if '.' in self.label:
            type = re.match(r'^(.*?)\.', self.label).group(1)   # get coarse grained NE type
        else:
            type = self.label
        return type

    @staticmethod
    def find_first_word_before(tokens, markers):
        """
        :type tokens: list[text.text_span.Token]
        :type markers: set[str]
        """
        for i, token in enumerate(tokens):
            if token.text.lower() in markers and i > 0:
                return tokens[i-1]
        return None

    def head(self):
        """
        Strategy for multi-word entity mentions.
        - Crime :
            (i) if there is a verb, use it as headword
            (ii) if there is 'of' or 'to', use the word before as the head
            (iii) else, use last word as head
        - Job-Title :
            (i) if there is a 'of' or 'at', use the word before as the head
            (ii) else, use last word as head
        - Numeric : use last word as head
        - Sentence : use last word as head
        - Time : look for the words in time_words (in order) and use it as the head if found. Else, use last word.
        - All other NE types:
            (i) remove any token consisting of just numbers and periods
            (ii) use last word as head

        Returns:
            text.text_span.Token
        """
        if len(self.tokens) == 1:
            return self.tokens[0]

        type = self.coarse_label()

        if type == 'Crime':
            for token in self.tokens:
                if token.spacy_token.pos_ == u'VERB':
                    return token
            t = self.find_first_word_before(self.tokens, set(['of', 'to']))
            if t is not None:
                return t
            else:
                return self.tokens[-1]
        elif type == 'Job-Title':
            t = self.find_first_word_before(self.tokens, set(['of', 'at']))
            if t is not None:
                return t
            else:
                return self.tokens[-1]
        elif type == 'Numeric' or type == 'Sentence':
            return self.tokens[-1]
        elif type == 'Time':
            for w in self.time_words:
                for token in self.tokens:
                    if token.text.lower() == w:
                        return token
            return self.tokens[-1]
        else:
            toks = []
            for token in self.tokens:
                if re.search(r'[a-zA-Z]', token.text) is not None:
                    toks.append(token)
            if len(toks) > 0:
                return toks[-1]
            else:
                return self.tokens[-1]

    def span_type(self):
        return span_types.ENTITY_MENTION

    # def start_char_offset(self):
    #     if self.tokens is not None:
    #         return self.tokens[0].start_char_offset()
    #     else:
    #         return self.int_pair.first
    #
    # def end_char_offset(self):
    #     if self.tokens is not None:
    #         return self.tokens[-1].end_char_offset()
    #     else:
    #         return self.int_pair.second

    def to_string(self):
        return ('%s: %s (%d,%d) "%s" %s' % (self.span_type(), self.id, self.start_char_offset(), self.end_char_offset(), self.text, self.label))


class Anchor(Span):
    """A consecutive span representing an anchor
    label: the event type represented by the anchor, e.g. Conflict.Attack, CyberAttack, Vulnerability
    """

    def __init__(self, id, int_pair, text, label):
        Span.__init__(self, int_pair, text)
        self.id = id
        self.label = label
        self.tokens = None
        """:type: list[text.text_span.Token]"""

    def with_tokens(self, tokens):
        """:type tokens: list[text.text_span.Token]"""
        self.tokens = tokens

    def head(self):
        """If the anchor is just a single token, we return the single token.
        If the anchor is multi-words, we heuristically determine a single token as the head

        Returns:
            text.text_span.Token
        """
        if len(self.tokens) == 1:
            return self.tokens[0]
        else:
            if self.tokens[0].spacy_token.pos_ == u'VERB':
                return self.tokens[0]
            else:
                return self.tokens[-1]

    def span_type(self):
        return span_types.ANCHOR

    # def start_char_offset(self):
    #     if self.tokens is not None:
    #         return self.tokens[0].start_char_offset()
    #     else:
    #         return self.int_pair.first
    #
    # def end_char_offset(self):
    #     if self.tokens is not None:
    #         return self.tokens[-1].end_char_offset()
    #     else:
    #         return self.int_pair.second

    def to_string(self):
        return ('%s: %s (%d,%d) "%s" %s' % (self.span_type(), self.id, self.start_char_offset(), self.end_char_offset(), self.text, self.label))


class EventSpan(Span):
    """A consecutive span representing an event. Sometimes we explicitly label e.g. a sentence as the event span.
    label: the event type represented by the event, e.g. Conflict.Attack, CyberAttack, Vulnerability
    """

    def __init__(self, id, int_pair, text, label):
        Span.__init__(self, int_pair, text)
        self.id = id
        self.label = label
        self.tokens = None
        """:type: list[text.text_span.Token]"""
        self.sentences = None

    def with_tokens(self, tokens):
        """:type tokens: list[text.text_span.Token]"""
        self.tokens = tokens

    def with_sentences(self, sentences):
        """:type sentences: list[text.text_span.Sentence]"""
        self.sentences = sentences

    # def start_char_offset(self):
    #     if self.tokens is not None:
    #         return self.tokens[0].start_char_offset()
    #     else:
    #         return self.int_pair.first
    #
    # def end_char_offset(self):
    #     if self.tokens is not None:
    #         return self.tokens[-1].end_char_offset()
    #     else:
    #         return self.int_pair.second

    def span_type(self):
        return span_types.EVENTSPAN

    def to_string(self):
        return ('%s: %s (%d,%d) "%s" %s' % (self.span_type(), self.id, self.start_char_offset(), self.end_char_offset(), self.text, self.label))


class EventArgument(Span):
    """A consecutive span representing an event argument
    label: the event argument role, e.g. Source, Target
    """

    def __init__(self, id, entity_mention, label):
        """:type entity_mention: text.text_span.EntityMention"""
        Span.__init__(self, IntPair(entity_mention.start_char_offset(), entity_mention.end_char_offset()), entity_mention.text)
        self.id = id
        self.label = label
        self.entity_mention = entity_mention

    def copy_with_entity_mention(self, entity_mention):
        """Sometimes we want to reassign the entity_mention with one that is backed by tokens
        :type entity_mention: text.text_span.EntityMention"""
        return EventArgument(self.id, entity_mention, self.label)

    def span_type(self):
        return span_types.EVENT_ARGUMENT

    def to_string(self):
        return ('%s: %s (%d,%d) "%s" %s' % (self.span_type(), self.id, self.start_char_offset(), self.end_char_offset(), self.text, self.label))


class Token(Span):
    """An individual word token.
    :spacy_token: an optional spacy token
    """

    def __init__(self, int_pair, text, spacy_token, index):
        Span.__init__(self, int_pair, text)
        assert spacy_token is not None
        self.spacy_token = spacy_token
        self.lemma = spacy_token.lemma_
        self.is_punct = spacy_token.is_punct
        self.index_in_sentence = index     # token index in sentence

        # following deals with word embeddings
        self.has_vector = False
        self.vector_index = -1
        self.word_vector = None

    def span_type(self):
        return span_types.TOKEN

    def to_string(self):
        return ('%s: (%d,%d) "%s"' % (self.span_type(), self.start_char_offset(), self.end_char_offset(), self.text))

class Sentence(Span):
    """Represents a sentence
    :tokens: a list of Token
    """

    def __init__(self, docid, int_pair, text, tokens, index):
        """:index: int giving the sentence number (starting from 0) within the document"""
        Span.__init__(self, int_pair, text)
        self.docid = docid
        self.tokens = tokens
        """:type: list[text.text_span.Token]"""
        self.entity_mentions = []
        """:type: list[text.text_span.EntityMention]"""
        self.events = []
        """:type: list[text.text_theory.Event]"""
        self.index = index

    def add_entity_mention(self, entity_mention):
        """:type entity_mention: text.text_span.EntityMention"""
        self.entity_mentions.append(entity_mention)

    def add_event(self, event):
        """:type event: text.text_theory.Event"""
        self.events.append(event)

    def number_of_tokens(self):
        return len(self.tokens)

    def span_type(self):
        return span_types.SENTENCE

    def get_all_event_anchors(self):
        """Returns a list of all event anchors
        Returns:
            list[text.text_span.Anchor]
        """
        # TODO: when reading in events from the annotation files, ensure each token/anchor is only used once
        ret = []
        for event in self.events:
            for anchor in event.anchors:
                ret.append(anchor)
        return ret

    def get_ne_type_per_token(self):
        """Get coarse-grained NE type of each token"""
        ret = []
        for token in self.tokens:
            found_ne = False
            for em in self.entity_mentions:
                if token.index_in_sentence == em.head().index_in_sentence:
                    ret.append(em.coarse_label())
                    found_ne = True
                    break
            if not found_ne:
                ret.append('None')
        assert len(ret) == len(self.tokens)
        return ret

    def to_string(self):
        print('(%d,%d):[%s]' % (self.start_char_offset(), self.end_char_offset(), self.text))

def to_sentence(text, start, end):
    """Converts a sentence raw text to a Sentence object."""
    charOffsets = IntPair(start, end)
    tokens = []

    offset = start
    for t in text.split():
        token = Token(IntPair(offset, offset+len(t)), t)
        tokens.append(token)
        offset += len(t)+1    # +1 to account for white-space

    return Sentence(charOffsets, text, tokens)

def file_to_document(filepath):
    f = open(filepath, 'rU')
    sentences = []

    offset = 0
    for line in f:
        sentence = to_sentence(line, offset, offset+len(line))
        sentences.append(sentence)
        offset += len(line);    # +1 for account for newline
    f.close()

    s_strings = [s.label for s in sentences]
    doc_text = "\n".join(s_strings)

    return Document(IntPair(0, offset-1), doc_text, sentences)


def spans_overlap(span1, span2):
    """
    :type span1: text.text_span.Span
    :type span2: text.text_span.Span
    """
    start1 = span1.start_char_offset()
    end1 = span1.end_char_offset()
    start2 = span2.start_char_offset()
    end2 = span2.end_char_offset()

    if start1 != start2 and end1 != end2 and (end1 <= start2 or end2 <= start1):
        return False
    else:
        return True

