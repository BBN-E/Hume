
from collections import defaultdict
import enum
import pickle
import re
import string

import numpy


numpy.random.seed(123456)


class TokenizationMode(enum.Enum):

    @staticmethod
    def tokenize_on_whitespace(tokens):
        new_tokens = []
        for token in tokens:
            new_tokens.extend(token.split())
        return new_tokens

    @staticmethod
    def tokenize_on_underscore(tokens):
        new_tokens = []
        for token in tokens:
            new_tokens.extend(token.split(u'_'))
        return new_tokens

    @staticmethod
    def tokenize_on_punct(tokens):
        punct_re = re.compile(r'([' + re.escape(string.punctuation) + r']+)')
        new_tokens = []
        for token in tokens:
            spaced_token = punct_re.sub(u' \0 ', token)
            new_tokens.extend(spaced_token.split())
        return new_tokens

    @staticmethod
    def tokenize_camelcase(tokens):
        camel_case = re.compile(
            '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
        new_tokens = []
        for token in tokens:
            for match in camel_case.finditer(token):
                new_tokens.append(match.group(0))
        return new_tokens

    WHITESPACE = tokenize_on_whitespace
    UNDERSCORE = tokenize_on_underscore
    CAMELCASE = tokenize_camelcase
    PUNCTUATION = tokenize_on_punct


def get_embedding_lookup(embeddings_file_path):
    # currently assumes the embeddings_file to be a pickle file in a specific
    # format: [word_list,embeddings_list], where all embeddings are of type
    # numpy.ndarray
    try:
        with open(embeddings_file_path, 'rb') as embeddings_file:
            [word_list, embeddings_list] = pickle.load(
                embeddings_file, encoding='bytes')
    except ValueError as err:
        raise err
    if isinstance(embeddings_list, numpy.ndarray) and embeddings_list.size == 0:
        raise ValueError('embeddings_list cannot be empty')
    if not isinstance(embeddings_list[0], numpy.ndarray):
        raise ValueError(
            'embeddings_list must be a list of numpy.ndarray elements')
    embeddings = {}
    for i in range(len(word_list)):
        word = word_list[i]
        embeddings[word] = embeddings_list[i]
    all_dims = []
    number_of_dims = 0
    for vector in embeddings.values():
        number_of_dims = len(vector)
        for dim in vector:
            all_dims.append(dim)
    mean = numpy.mean(all_dims)
    standard_deviation = numpy.std(all_dims)
    better_embeddings = defaultdict(
        lambda: numpy.random.normal(
            loc=mean, scale=standard_deviation, size=number_of_dims))
    for token, vector in embeddings.items():
        better_embeddings[token] = vector
    return better_embeddings


def as_numpy_array(vector_list):
    return numpy.asarray(vector_list)


def strip_comments(line):
    return line.split('#')[0].strip()


def decay(factor):
    return numpy.exp(-factor)


def get_filtered_tokens(
        untokenized_string,
        tokenization_modes=None,
        keywords=None,
        stopwords=None):

    if tokenization_modes is None:
        tokenization_modes = [
            TokenizationMode.PUNCTUATION, TokenizationMode.WHITESPACE
        ]

    tokens = [untokenized_string.strip().lower()]
    for tokenization_function in tokenization_modes:
        tokens = tokenization_function(tokens)

    if keywords is not None:
        new_tokens = []
        for token in tokens:
            if token in keywords:
                new_tokens.append(token)
        tokens = new_tokens

    if stopwords is not None:
        new_tokens = []
        for token in tokens:
            if token not in stopwords:
                new_tokens.append(token)
        tokens = new_tokens

    return tokens


def get_average_embeddings(tokens, embedding_lookup, weights=None):
    token_vectors = [embedding_lookup[t] for t in tokens]
    return get_average_of_vectors(token_vectors, weights)


def get_average_of_vectors(vecs, weights=None):
    if len(vecs) == 0:
        return 0
    if weights is None:
        weights = [1.0, ] * len(vecs)
    weighted_vecs = []
    for i, v in enumerate(vecs):
        weighted_vecs.append(v * weights[i])
    return sum(weighted_vecs) / sum(weights)


def get_embeddings_for_mention_text(
        mention_text,
        embedding_lookup,
        tokenization_modes=None,
        keywords=None,
        stopwords=None):
    """
    Tokenize and get the average embedding of a string.  Tokenization modes
    are applied in order.
    :type mention_text: str
    :type embedding_lookup: defaultdict
    :type tokenization_modes: list
    :type keywords: set
    :type stopwords: set
    """
    tokens = get_filtered_tokens(
        mention_text, tokenization_modes, keywords, stopwords)
    return get_average_embeddings(tokens, embedding_lookup)
