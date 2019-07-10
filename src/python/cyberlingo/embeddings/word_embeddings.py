from __future__ import absolute_import
from __future__ import with_statement

import os
import codecs

import numpy as np

class WordEmbedding(object):

    def __init__(self, params):
        """
        :type params: common.parameters.Parameters
        """

        embedding_filepath = params.get_string('embedding.embedding_file')
        vocab_size = params.get_int('embedding.vocab_size')
        vector_size = params.get_int('embedding.vector_size')

        print('Loading embeddings file ', embedding_filepath)
        words, word_vec = self.load_word_vec_file(embedding_filepath, vocab_size, vector_size)
        self.words = words
        """:type: numpy.ndarray"""
        self.word_vec = word_vec
        """:type: numpy.ndarray"""
        self.none_token = params.get_utf8_string('embedding.none_token')
        self.missing_token = params.get_utf8_string('embedding.missing_token')
        self.word_lookup = dict((w, i) for i, w in enumerate(self.words))
        self.vector_length = vector_size
        self.base_size = len(self.words)
        self.word_vecLength = None
        self.token_map = dict()
        self.accessed_indices = set()

    def load_word_vec_file(self, embedding_filepath, vocab_size, vector_size):
        # npz_file = vector_file.replace('.txt', '.npz')
        npz_file = embedding_filepath + '.trial.npz'
        if os.path.exists(npz_file):
            data = np.load(npz_file)
            return (data['words'], data['word_vec'])

        words = []
        word_vec = np.empty((vocab_size, vector_size), dtype=np.float32)

        with codecs.open(embedding_filepath, 'r', encoding='utf8') as f:
            i = 0
            for line in f:
                fields = line.strip().split()
                if len(fields) == 2:  # header in embeddings file
                    continue
                word = fields[0]
                words.append(word)
                word_vec[i, :] = np.asarray([float(x) for x in fields[1:]])
                i += 1

        words = np.asarray(words)
        np.savez(npz_file, words=words, word_vec=word_vec)
        return (words, word_vec)


    def get_none_vector(self):
        return self.get_vector(self.none_token)

    def get_missing_vector(self):
        return self.get_vector(self.missing_token)

    def get_vector(self, token, try_lower=True, try_lemma=True):
        """
        Returns:
            (str, int, np.array[float])
        :param token: could be a string or text.text_span.Token
        :return: str==(original token string, lowercase, or lemma), int==embedding-index, np.array=embedding-vector
        """
        idx = -1
        vec = None
        if type(token) is str or type(token) is unicode or type(token) is np.unicode_:
            text = token
            if text in self.word_lookup:
                idx = self.word_lookup[text]
                vec = self.word_vec[idx]
            if idx < 0:
                text = None
        else:
            text = token.text
            if text in self.word_lookup:
                idx = self.word_lookup[text]
                vec = self.word_vec[idx]
            if idx < 0:
                text = text.lower()
                if text in self.word_lookup:
                    idx = self.word_lookup[text]
                    vec = self.word_vec[idx]
            if idx < 0:
                text = token.lemma
                if text in self.word_lookup:
                    idx = self.word_lookup[text]
                    vec = self.word_vec[idx]
            if idx < 0:
                text = None
        if idx > -1:
            self.accessed_indices.add(idx)
        return (text, idx, vec)

    def get_vector_by_index(self, idx):
        if idx < self.base_size:
            return (self.words[idx], idx, self.word_vec[idx])
        else:
            raise ValueError('Given an idx which is out of bounds for embedding vocab')

