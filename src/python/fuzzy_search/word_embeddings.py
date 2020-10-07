import numpy as np
import six


class WordEmbedding():
    def load_word_vec_file(self, embedding_filepath, vocab_size, vector_size):
        npz_file = embedding_filepath + '.npz'
        data = np.load(npz_file)
        return (data['words'], data['word_vec'])

    def __init__(self, embedding_filepath, vocab_size, vector_size, none_token, missing_token):
        """
        :type params: nlplingo.common.parameters.Parameters
        """

        print('Loading embeddings file ', embedding_filepath)
        words, word_vec = self.load_word_vec_file(embedding_filepath, vocab_size, vector_size)
        self.words = words
        """:type: numpy.ndarray"""
        self.word_vec = word_vec
        """:type: numpy.ndarray"""

        self.word_lookup = dict((w, i) for i, w in enumerate(self.words))
        self.vector_length = vector_size
        self.base_size = len(self.words)
        # self.word_vecLength = None
        # self.token_map = dict()
        # self.accessed_indices = set()

        self.none_token = none_token
        text, self.none_index, vec = self.get_vector(self.none_token)
        assert self.none_index != -1

        self.missing_token = missing_token
        text, self.missing_index, vec = self.get_vector(self.missing_token)
        assert self.missing_index != -1

    def get_none_vector(self):
        return self.get_vector(self.none_token)

    def get_missing_vector(self):
        return self.get_vector(self.missing_token)

    def get_vector(self, token, embedding_prefix=None, try_lower=True, try_lemma=True, sent=None):
        """
        Returns:
            (str, int, np.array[float])
        :param token: could be a string or nlplingo.text.text_span.Token
        :param sent: Fitting the interface, not used
        :return: str==(original token string, lowercase, or lemma), int==embedding-index, np.array=embedding-vector
        """
        idx = -1
        vec = None
        if isinstance(token, six.string_types) or type(token) is np.unicode_:
            text = self.to_token_text(token, embedding_prefix)

            if text in self.word_lookup:
                idx = self.word_lookup[text]
                vec = self.word_vec[idx]
            if idx < 0:
                text = None
        else:
            text = self.to_token_text(token.text, embedding_prefix)
            if text in self.word_lookup:
                idx = self.word_lookup[text]
                vec = self.word_vec[idx]
            if idx < 0:
                text = self.to_token_text(token.text.lower(), embedding_prefix)
                if text in self.word_lookup:
                    idx = self.word_lookup[text]
                    vec = self.word_vec[idx]
            if idx < 0:
                text = self.to_token_text(token.lemma, embedding_prefix)
                if text in self.word_lookup:
                    idx = self.word_lookup[text]
                    vec = self.word_vec[idx]
            if idx < 0:
                text = None
        # if idx > -1:
        #    self.accessed_indices.add(idx)
        return (text, idx, vec)

    def get_vector_by_index(self, idx):
        if idx < self.base_size:
            return (self.words[idx], idx, self.word_vec[idx])
        else:
            raise ValueError('Given an idx which is out of bounds for embedding vocab')

    def to_token_text(self, text, embedding_prefix):
        if text is None:
            return None
        if embedding_prefix is not None:
            text = embedding_prefix + text
        return text
