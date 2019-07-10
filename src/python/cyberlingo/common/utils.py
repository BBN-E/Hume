from __future__ import absolute_import
from __future__ import division

import sys
import codecs
import math

class IntPair(object):
    """A utility class to store a pair of integers
   
    Attributes:
        first: first integer
        second: second integer
    """

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def to_string(self):
        return '({},{})'.format(self.first, self.second)

class Struct:
    """A structure that can have any fields defined

    Example usage:
    options = Struct(answer=42, lineline=80, font='courier')
    options.answer (prints out 42)
    # adding more
    options.cat = 'dog'
    options.cat (prints out 'dog')
    """
    def __init__(self, **entries):
        self.__dict__.update(entries)

def offset_overlap(offset1, offset2):
    """
    :type offset1: common.utils.IntPair
    :type offset2: common.utils.IntPair
    """
    if offset1.first <= offset2.first and offset2.first < offset1.second:
        return True
    elif offset2.first <= offset1.first and offset1.first < offset2.second:
        return True
    else:
        return False

def offset_same(offset1, offset2):
    """
    :type offset1: common.utils.IntPair
    :type offset2: common.utils.IntPair
    """
    if offset1.first == offset2.first and offset1.second == offset2.second:
        return True
    else:
        return False

def find_best_location(all_text, search_string, start_idx, end_idx):
    """When all_text[start_idx, end_idx] != search_string, we use this method to find the location of
    search_string within all_text, that is closest to the given (start_idx, end_idx)."""

    search_string = search_string.strip()
    best_match = (len(all_text), None)
    start = 0

    while True:
        match_pos = all_text.find(search_string, start)
        if match_pos < 0:
            break
        dist = abs(start_idx - match_pos)
        if dist < best_match[0]:
            best_match = (dist, match_pos)
        start = match_pos + 1
    if best_match[1] is not None:
        #if config.verbose:
        #    print(u' Search string and indices mismatch: ' +
        #          u'"{0}" != "{1}". Found match by shifting {2} chars'.format(
        #              search_string, all_text[start_idx:end_idx],
        #              start_idx - best_match[1]))
        start_idx = best_match[1]
        end_idx = best_match[1] + len(search_string)
    else:
        raise Exception(u'Search string ({0}) not in text.'.format(search_string))

    return (start_idx, end_idx)

def get_span_with_offsets(spans, start, end):
    """Return the span with the exact same (start, end) offsets. There should only be one, or None
    :type spans: list[text.text_span.Span]
    Returns:
        text.text_span.Span
    """
    for span in spans:
        if start == span.start_char_offset() and end == span.end_char_offset():
            return span
    return None

def get_spans_in_offsets(spans, start, end):
    """Return the list of spans (text.text_span.Span) that are within (start, end) offsets
    :type spans: list[text.text_span.Span]
    Returns:
        list[text.text_span.Span]
    """
    ret = []
    for span in spans:
        if start <= span.start_char_offset() and span.end_char_offset() <= end:
            ret.append(span)
    return ret

def get_tokens_corresponding_to_span(tokens, span):
    """Find the list of token(s) corresponding to span (of type text.text_span.Span)
    We look for exact offset match. If we cannot find an exact match, we return None
    :type tokens: list[text.text_span.Token]
    :type span: text.text_span.Span
    Returns:
        list[text.text_span.Token]
    """
    first_token_index = -1
    last_token_index = -1
    for i, token in enumerate(tokens):
        if span.start_char_offset() == token.start_char_offset():
            first_token_index = i
        if span.end_char_offset() == token.end_char_offset():
            last_token_index = i

    if first_token_index != -1 and last_token_index != -1:
        return tokens[first_token_index:last_token_index+1]
    else:
        # we try to match heuristically
        #print('Cannot find any token for span: {}'.format(span.to_string()))
        max_diff = sys.maxint
        matching_first_token_index = -1
        span_prefix = span.text.split()[0]
        for i, token in enumerate(tokens):
            if token.text == span_prefix:
                diff = int(math.fabs(span.start_char_offset() - token.start_char_offset()))
                if diff < max_diff:
                    max_diff = diff
                    matching_first_token_index = i

        if matching_first_token_index != -1:
            diff = span.start_char_offset() - tokens[matching_first_token_index].start_char_offset()
            span_start = span.start_char_offset() - diff
            span_end = span.end_char_offset() - diff
            for i, token in enumerate(tokens):
                if span_start == token.start_char_offset():
                    first_token_index = i
                if span_end == token.end_char_offset():
                    last_token_index = i

            if first_token_index != -1 and last_token_index != -1:
                #print('To align annotation offsets with token offsets, we adjust span offsets from ({},{}) to ({},{})'.format(span.start_char_offset(), span.end_char_offset(), span_start, span_end))
                span.int_pair = IntPair(span_start, span_end)
                return tokens[first_token_index:last_token_index + 1]

    #print('Cannot find any token for span: {}'.format(span.to_string()))
    #print('Returning None')
    #print('SENTENCE: {}\n'.format(' '.join('{}:{}'.format(token.start_char_offset(), token.text) for token in tokens)))
    return None

    #
    #
    # if ret[0].start_char_offset()==span_start and ret[-1].end_char_offset()==span_end:
    #     return ret
    # else:
    #     return None


def read_file_to_list(filename, utf8=False):
    """
    :type filename: str
    Returns:
        list[str]
    """
    ret = []

    f = None
    if utf8:
        f = codecs.open(filename, 'r', encoding='utf-8')
    else:
        f = open(filename, 'r')

    for line in f:
        ret.append(line.strip())
    f.close()

    return ret


class F1Score(object):
    def __init__(self, c, num_true, num_predict):
        self.c = c
        self.num_true = num_true
        self.num_predict = num_predict
        self.recall = c / num_true
        self.precision = c / num_predict
        self.f1 = (2 * self.recall * self.precision) / (self.recall + self.precision)

    def to_string(self):
        return '#C={},#R={},#P={} R,P,F={},{},{}'.format(self.c, self.num_true, self.num_predict, self.recall,
                                                         self.precision, self.f1)
