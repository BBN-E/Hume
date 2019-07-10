import sys
import argparse
import json
import codecs
from collections import defaultdict

import serifxml

from nlplingo.common.utils import IntPair
from nlplingo.common.io_utils import ComplexEncoder
from nlplingo.text.text_span import Token


def ascii(s):
    return s.encode('ascii', 'ignore')


class TokenInfo(object):
    def __init__(self, offset, text):
        """
        :type offset: nlplingo.common.utils.IntPair
        :type text: str
        """
        self.offset = offset
        self.text = text
        self.sentence_offset = None
        self.sentence_text = None


def to_tokens(sentence):
    """
    :type sentence: serifxml.Sentence
    :rtype: list[nlplingo.text.text_span.Token]
    """
    ret = []
    """:type: list[nlplingo.text.text_span.Token]"""

    root = sentence.parse.root
    if root is None:
        return ret

    """:type: serifxml.SynNode"""
    for i, t in enumerate(root.terminals):
        t_text = t.text
        t_start = t.start_char
        t_end = t.end_char
        t_pos_tag = t.parent.tag
        ret.append(Token(IntPair(t_start, t_end), i, t_text, lemma=None, pos_tag=t_pos_tag))
    return ret


def record_unigram_info(docid, tokens, vocab_locations, sentence):
    """We only record nouns and verbs
    :type tokens: list[nlplingo.text.text_span.Token]
    :type sentence: serifxml.Sentence
    """
    for token in tokens:
        pos_suffix = None
        if token.pos_tag == 'NN' or token.pos_tag == 'NNS':
            pos_suffix = '.n'
        elif token.pos_tag.startswith('VB'):
            pos_suffix = '.v'
        if pos_suffix is not None:
            word_string = token.text.lower() + pos_suffix

            token_info = TokenInfo(token.int_pair, token.text)
            token_info.sentence_offset = IntPair(sentence.start_char, sentence.end_char)
            token_info.sentence_text = sentence.text

            if word_string not in vocab_locations:
                doc_offsets = defaultdict(list)
                doc_offsets[docid].append(token_info)
                vocab_locations[word_string] = doc_offsets
            else:
                vocab_locations[word_string][docid].append(token_info)

            # Fixed lookup w/o POS tags
            word_string = token.text.lower() 

            if word_string not in vocab_locations:
                doc_offsets = defaultdict(list)
                doc_offsets[docid].append(token_info)
                vocab_locations[word_string] = doc_offsets
            else:
                vocab_locations[word_string][docid].append(token_info)


def record_bigram_info(docid, tokens, vocab_locations, sentence):
    """We only record nouns and verbs
    :type tokens: list[nlplingo.text.text_span.Token]
    :type sentence: serifxml.Sentence
    """
    for i in range(len(tokens) - 1):
        offset = IntPair(tokens[i].start_char_offset(), tokens[i+1].end_char_offset())
        word_string = '{} {}'.format(ascii(tokens[i].text.lower()), ascii(tokens[i+1].text.lower()))
        word_string_ori = '{} {}'.format(ascii(tokens[i].text), ascii(tokens[i+1].text))

        token_info = TokenInfo(offset, word_string_ori)
        token_info.sentence_offset = IntPair(sentence.start_char, sentence.end_char)
        token_info.sentence_text = sentence.text

        if word_string not in vocab_locations:
            doc_offsets = defaultdict(list)
            doc_offsets[docid].append(token_info)
            vocab_locations[word_string] = doc_offsets
        else:
            vocab_locations[word_string][docid].append(token_info)


def record_doc_vocab(filepath, vocab_locations):
    """
    :type vocab_locations: dict[str, defaultdict(list)]
    """
    serif_doc = serifxml.Document(filepath)
    """:type: serifxml.Document"""

    docid = serif_doc.docid
    for st_index, sentence in enumerate(serif_doc.sentences):
        #st = sentence.sentence_theories[0]
        """:type: serifxml.SentenceTheory"""
        #st_text, st_start, st_end = get_snippet(serif_doc, st)

        tokens = to_tokens(sentence)
        record_unigram_info(docid, tokens, vocab_locations, sentence)
        record_bigram_info(docid, tokens, vocab_locations, sentence)


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        params = json.load(f)

    serifxml_filelist = params['serifxml_filelist']
    wordlist = params['wordlist']
    outdir = params['outdir']

    filepaths = []
    with codecs.open(serifxml_filelist, 'r', encoding='utf-8') as f:
        for line in f:
            filepaths.append(line.strip())

    vocab_locations = dict()
    """:type: dict[str, defaultdict(list[TokenInfo])]"""
    counter = 0
    for filepath in filepaths:
        record_doc_vocab(filepath, vocab_locations)
        counter += 1
        if (counter % 100)==0:
            print('Processed {} out of {} documents'.format(counter, len(filepaths)))

    word_strings = []
    with codecs.open(wordlist, 'r', encoding='utf-8') as f:
        for line in f:
            word_strings.append(line.strip().lower())

    data_points = []
    for ws in word_strings:
        if ws in vocab_locations:
            for docid in vocab_locations[ws]:
                for token_info in vocab_locations[ws][docid]:
                    d = dict()
                    d['text_normalized'] = ws
                    d['text'] = token_info.text
                    d['docid'] = docid
                    d['start'] = token_info.offset.first
                    # Nudging for nlplingo
                    d['end'] = token_info.offset.second + 1
                    d['sent_start'] = token_info.sentence_offset.first
                    d['sent_end'] = token_info.sentence_offset.second
                    d['sent_text'] = token_info.sentence_text
                    data_points.append(d)

    with codecs.open(outdir + '/word_string.json', 'w', encoding='utf-8') as o:
        o.write(json.dumps(data_points, indent=4, cls=ComplexEncoder, ensure_ascii=False))

