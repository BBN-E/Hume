import codecs
import os
import sys
import argparse

sys.path.append('/nfs/mercury-04/u22/Active/Projects/SERIF/python')
import serifxml


def get_tokenized_text(sentence_theory):
    tokens = []
    offsets = []
    for token in sentence_theory.token_sequence:
        tokens.append(token.text)
        offsets.append((token.start_char, token.end_char))
    return (tokens, offsets)


def extractSentences(serifXmlPath):
    serif_doc = serifxml.Document(serifXmlPath)

    doc_tokens = []
    doc_offsets = []
    for s in serif_doc.sentences:
        st = s.sentence_theories[0]
        (tokens, offsets) = get_tokenized_text(st)
        doc_tokens.append(tokens)
        doc_offsets.append(offsets)

    return (doc_tokens, doc_offsets)


def find_words(serifXmlPath, word_to_class, outfilepath, lemmas):
    """
    :type words: set(str)
    """
    (doc_tokens, doc_offsets) = extractSentences(serifXmlPath)

    filename = os.path.basename(serifXmlPath)
    docid = filename[0:filename.rfind('.')]

    f = codecs.open(outfilepath, 'w', encoding='utf-8')
    for i in range(len(doc_tokens)):
        tokens = doc_tokens[i]
        offsets = doc_offsets[i]
        for j in range(len(tokens)):
            w = tokens[j].lower()
            lemma = get_lemma(w, lemmas)
            if lemma in word_to_class:
                (start, end) = offsets[j]
                f.write('{} {} {} {} {}\n'.format(docid, word_to_class[lemma], tokens[j], start, end))    
    f.close()


def read_vocab(filepath):
    ret = set()
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            ret.add(line.strip())
    return ret


def read_clusterfile(filepath):
    ret = dict()	# lemma -> classname
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.strip().split()
            classname = tokens[0]
            for token in tokens[2:]:
                # a word might be in more than 1 cluster. We respect the first, since clusters are ordered in terms of cluster-score
                if token not in ret:
                    ret[token] = classname
    return ret


def get_lemma(w, lemma_dict):
    if w in lemma_dict:
        return lemma_dict[w]
    else:
        return w


def read_lemma_dict(filepath):
    ret = dict()
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.strip().split()
            w = tokens[0]
            lemma = tokens[1]
            ret[w] = lemma
    return ret


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serifxml_list')		# the SerifXML on which you want to find generic triggers
    parser.add_argument('--cluster_file')
    parser.add_argument('--vocab')
    parser.add_argument('--lemma_dict')
    parser.add_argument('--output_dir')	# as we find triggers, we write them (text, char-offsets) to this file
    args = parser.parse_args()

    word_to_class = read_clusterfile(args.cluster_file)
    #words = read_vocab(args.vocab)

    print('Reading lemma dict')
    lemmas = read_lemma_dict(args.lemma_dict)

    filepaths = []
    with codecs.open(args.serifxml_list, 'r', encoding='utf-8') as f:
        for line in f:
            filepaths.append(line.strip())

    for filepath in filepaths:
        filename = os.path.basename(filepath)
        docid = filename[0:filename.rfind('.')]
        print(docid)

        find_words(filepath, word_to_class, os.path.join(args.output_dir, docid), lemmas)




