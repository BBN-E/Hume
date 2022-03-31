import gzip
import json
import os
import re
import tensorflow as tf

flags = tf.flags
FLAGS = flags.FLAGS

# bert
import tokenization
from nlplingo.common.io_utils import read_file_to_list
import serifxml3

from bert_document import BertDocument
from bert_document import TokenWithIndex

import collections

DocSentEntry = collections.namedtuple("DocSentEntry", ['doc_id', 'sent_id', 'number_of_bert_tokens'])
LingoToken = collections.namedtuple("LingoToken", ["text"])


def to_sentence_tokens(doc):
    """
    :type doc: nlplingo.text.text_theory.Document
    :rtype: list[list[TokenWithIndex]]
    """
    ret = []
    for sentence in doc.sentences:
        tokens = []
        for token in sentence.tokens:
            tokens.append(TokenWithIndex(token.text, sentence.index, token.index_in_sentence))
        ret.append(tokens)
    return ret


def get_tokens_from_serif_doc(filepath):
    """
    :rtype: (str, list[list[TokenWithIndex]])
    """
    serif_doc = serifxml3.Document(filepath)
    lingo_sentence_minic = list()
    for sent_idx, sentence in enumerate(serif_doc.sentences):
        sent_en = list()
        lingo_sentence_minic.append(sent_en)
        for token_idx, token in enumerate(sentence.token_sequence):
            sent_en.append(LingoToken(token.text))
    return serif_doc.docid, lingo_sentence_minic


def get_tokens_from_text_doc(filepath):
    """
    :rtype: (str, list[list[TokenWithIndex]])
    """
    ret = []
    docid = os.path.basename(filepath)
    lines = read_file_to_list(filepath)
    for sent_index, line in enumerate(lines):
        tokens = []
        for token_index, token_text in enumerate(line.split()):
            tokens.append(TokenWithIndex(token_text, sent_index, token_index))
        ret.append(tokens)
    return docid, ret


def read_doc_to_bert_input(filepath, tokenizer, maximum_allowed_bert_tokens_per_sentence):
    if 'SERIF:' in filepath:
        (docid, sentences_tokens) = get_tokens_from_serif_doc(re.search(r'SERIF:(\S+)', filepath).group(1))
    elif 'TEXT:' in filepath:
        (docid, sentences_tokens) = get_tokens_from_text_doc(re.search(r'TEXT:(\S+)', filepath).group(1))
    else:
        raise NotImplementedError("Cannot support {}".format(filepath))
    doc = BertDocument(docid, sentences_tokens, maximum_allowed_bert_tokens_per_sentence)
    doc.tokenize_all_sentences(tokenizer)
    return doc


def process_docs_to_bert_input(filelist_path, tokenizer, maximum_allowed_bert_tokens_per_sentence, outdir):
    filepaths = read_file_to_list(filelist_path)
    input_token_file_line_idx = 0
    with gzip.open(os.path.join(outdir, 'sent_info.info'), 'wt') as sent_info_wfp:
        with gzip.open(os.path.join(outdir, 'input_token.info'), 'wt') as input_token_wfp:
            for filepath in filepaths:
                bert_doc = read_doc_to_bert_input(filepath, tokenizer, maximum_allowed_bert_tokens_per_sentence)
                with gzip.open(os.path.join(outdir, "{}.token_map".format(bert_doc.docid)), 'wt') as token_map_wfp:
                    for sentid in range(len(bert_doc.sentences_input_tokens)):
                        sent_info = DocSentEntry(bert_doc.docid, sentid, len(bert_doc.sentences_bert_tokens[sentid]))
                        sent_string = " ".join(token.text.replace("\r", " ").replace("\n", " ") for token in
                                               bert_doc.sentences_input_tokens[sentid])
                        sent_string = sent_string + '\n'
                        sent_string = json.dumps({"text": sent_string}, ensure_ascii=False)
                        input_token_wfp.write("{}\n".format(sent_string))
                        input_token_file_line_idx += 1
                        sent_info_wfp.write("{}\n".format(json.dumps(dict(sent_info._asdict()))))
                        token_map_wfp.write(
                            "{}\n".format(" ".join([str(index) for index in bert_doc.sentences_token_map[sentid]])))


if __name__ == "__main__":
    flags.DEFINE_string("filelist", None, "")
    flags.DEFINE_string("bert_vocabfile", None, "")
    flags.DEFINE_integer("maximum_allowed_bert_tokens_per_sentence", None, "")
    flags.DEFINE_string("outdir", None, "")

    # Copy from original repo https://github.com/google-research/bert/blob/cc7051dc592802f501e8a6f71f8fb3cf9de95dc9/extract_features.py#L58
    flags.DEFINE_bool(
        "do_lower_case", True,
        "Whether to lower case the input text. Should be True for uncased "
        "models and False for cased models.")

    tokenizer = tokenization.FullTokenizer(vocab_file=FLAGS.bert_vocabfile, do_lower_case=FLAGS.do_lower_case)
    process_docs_to_bert_input(FLAGS.filelist, tokenizer, FLAGS.maximum_allowed_bert_tokens_per_sentence, FLAGS.outdir)
