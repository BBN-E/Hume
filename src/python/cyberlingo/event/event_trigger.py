from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from collections import defaultdict

import numpy as np
from future.builtins import range

class EventTriggerGenerator(object):
    # we only accept tokens of the following part-of-speech categories as trigger candidates
    trigger_pos_category = set([u'NOUN', u'VERB', u'ADJ', u'PROPN'])

    def __init__(self, event_domain, params):
        """
        :type event_domain: event.event_domain.EventDomain
        :type params: common.parameters.Parameters
        """
        self.event_domain = event_domain
        self.params = params
        self.max_sent_length = params.get_int('max_sent_length')
        self.neighbor_dist = params.get_int('cnn.neighbor_dist')
        self.statistics = defaultdict(int)

    def generate(self, docs):
        """
        :type docs: list[text.text_theory.Document]
        """
        self.statistics.clear()

        examples = []
        """:type: list[event.event_trigger.EventTriggerExample"""

        for doc in docs:
            for sent in doc.sentences:
                examples.extend(self._generate_sentence(sent))

        for k, v in self.statistics.items():
            print('EventTriggerGenerator stats, {}:{}'.format(k, v))

        return examples

    def _generate_sentence(self, sentence):
        """
        :type sentence: text.text_span.Sentence
        """
        ret = []
        """:type: list[event.event_trigger.EventTriggerExample]"""

        if sentence.number_of_tokens() < 1:
            return ret
        if sentence.number_of_tokens() >= self.max_sent_length:
            print('Skipping overly long sentence of {} tokens'.format(sentence.number_of_tokens()))
            return ret

        # for event in sentence.events:
        #     if len(event.anchors) != 1:
        #         print('This event has {} anchors'.format(len(event.anchors)))
        #     for anchor in event.anchors:
        #         if len(anchor.tokens) > 1:
        #             word_string = ' '.join(token.text for token in anchor.tokens)
        #             pos_string = ' '.join(token.spacy_token.pos_ for token in anchor.tokens)
        #             print('Multi-word anchor:\t{}\t{}'.format(pos_string, word_string))

        tokens = [None] + sentence.tokens

        for event in sentence.events:
            self.statistics['number_event'] += 1
            for anchor in event.anchors:
                self.statistics['number_trigger'] += 1

        for token_index, token in enumerate(tokens):
            if token is None:
                continue

            # TODO if current token is a trigger for multiple event types, event_type_index is only set to 1 event_type_index
            event_type = self.get_event_type_of_token(token, sentence)

            if event_type != 'None':
                self.statistics[token.spacy_token.pos_] += 1

            if token.spacy_token.pos_ not in self.trigger_pos_category:
                continue

            #if event_type != 'None':
            #    print('event_type ', event_type)
            if event_type != 'None':
                self.statistics['number_positive_trigger'] += 1

            example = EventTriggerExample(token, sentence, self.event_domain, self.params, event_type)
            self._generate_example(example, tokens, token_index, self.max_sent_length, self.neighbor_dist)
            ret.append(example)
        return ret

    @classmethod
    def _generate_example(cls, example, tokens, token_index, max_sent_length, neighbor_dist):
        """
        :type example: event.event_trigger.EventTriggerExample
        :type tokens: list[text.text_span.Token]
        :type max_sent_length: int
        :type neighbor_dist: int
        """
        token = example.token
        event_domain = example.event_domain

        # Generate info
        #example.info['docid'] = 'dummy'
        #example.info['text_unit_no'] = token.start_char_offset()
        #example.info['trigger_token_no'] = token.index_in_sentence
        #example.info['trigger_token_i'] = token.spacy_token.i   # index of the token within the parent document

        # checks whether the current token is a trigger for multiple event types
        # this doesn't change the state of any variables, it just prints information
        # self.check_token_for_multiple_event_types(token, trigger_ids)

        # TODO if current token is a trigger for multiple event types, event_type_index is only set to 1 event_type_index
        event_type_index = event_domain.get_event_type_index(example.event_type)

        # self.label is a 2-dim matrix [#num_tokens, #event_types]
        example.label[event_type_index] = 1

        # self.vector_data = [ #instances , (max_sent_length + 2*neighbor_dist+1) ]
        # TODO why do we pad on 2*neighbor_dist+1 ??
        cls.assign_vector_data(tokens, example)

        # self.entity_type_data = [ #instances , self.gen.max_sent_length ]
        # if we are using bio index, else a single 0 element
        # if self.gen.use_bio_index:
        #    self.assign_entity_type_data(tokens, eg_index)

        # token_texts = [ self.gen.max_sent_length ]    # lexical text of each token in sentence
        # token_texts = self.assign_token_texts(tokens)

        # self.token_idx = [ #instances , self.gen.max_sent_length ]
        cls.assign_token_idx(tokens, example)  # index of token within parent document

        # self.pos_data = [ #instances , max_sent_length ]  # relative position of other words to candidate token
        # self.pos_index_data = [ #instances ]              # each candidate token -> its token index in sentence
        cls.assign_position_data(token_index, example, max_sent_length)  # position features

        # self.lex_data = [ #instances , 2*neighbor_dist+1 ]    # this is for local-window around candidate token
        # also pads the window to end of self.vector_data
        window_text = cls.assign_lexical_data(token_index, tokens, example, max_sent_length, neighbor_dist)  # generate lexical features

        #cls._assign_ner_data(tokens, example)

        # if self.gen.print_instance:
        #    self._print_inst(eg_index, token_texts, window_text, is_trigger, event_type_index)
        # if self.gen.save_text:
        #    self._instance_text_repr(eg_index, token_texts, window_text, tokens)

    @staticmethod
    def get_event_type_of_token(token, sent):
        """:type token: text.text_span.Token"""
        event_type = 'None'
        #print('target token, ', token.to_string())
        for event in sent.events:
            for anchor in event.anchors:
                #print('checking against anchor, ', anchor.to_string())
                if token.start_char_offset()==anchor.head().start_char_offset() and token.end_char_offset()==anchor.head().end_char_offset():
                    event_type = event.label
                    break
        return event_type

    @staticmethod
    def assign_vector_data(tokens, example):
        """Capture the word embeddings, or embeddings index, at each word position in sentence
        :type tokens: list[text.text_span.Token]
        :type example: event.event_trigger.EventTriggerExample
        """
        for i, token in enumerate(tokens):
            if token and token.has_vector:
                example.vector_data[i] = token.vector_index

    @staticmethod
    def _assign_ner_data(tokens, example):
        """
        :type tokens: list[text.text_span.Token]
        :type example: event.event_argument.EventArgumentExample
        """
        token_ne_type = example.sentence.get_ne_type_per_token()
        assert len(token_ne_type) == len(tokens)
        for i, token in enumerate(tokens):
            if token:
                example.ner_data[i] = example.event_domain.get_entity_type_index(token_ne_type[i])

    @staticmethod
    def assign_token_texts(tokens, max_sent_length):
        """Lexical text of each token in the sentence
        :type tokens: list[text.text_span.Token]
        :type max_sent_length: int
        """
        token_texts = ['_'] * max_sent_length
        for i, token in enumerate(tokens):
            if token:
                token_texts[i] = '{0}'.format(token.text)
        return token_texts

    @staticmethod
    def assign_token_idx(tokens, example):
        """
        :type tokens: list[text.text_span.Token]
        :type example: event.event_trigger.EventTriggerExample
        """
        for i, token in enumerate(tokens):
            if token:
                example.token_idx[i] = token.spacy_token.i

    @staticmethod
    def assign_position_data(token_index, example, max_sent_length):
        """We capture positions of other words, relative to current word
        If the sentence is not padded with a None token at the front, then eg_index==token_index

        In that case, here is an example assuming max_sent_length==10 , and there are 4 tokens
        eg_index=0 , token_index=0    pos_data[0] = [ 0  1  2  3  4  5  6  7  8  9 ]  pos_index_data[0] = 0
        eg_index=1 , token_index=1    pos_data[1] = [-1  0  1  2  3  4  5  6  7  8 ]  pos_index_data[1] = 1
        eg_index=2 , token_index=2    pos_data[2] = [-2 -1  0  1  2  3  4  5  6  7 ]  pos_index_data[2] = 2
        eg_index=3 , token_index=3    pos_data[3] = [-3 -2 -1  0  1  2  3  4  5  6 ]  pos_index_data[3] = 3

        If the sentence is padded with a None token at the front, then eg_index==(token_index-1),
        and there are 5 tokens with tokens[0]==None

        eg_index=0 , token_index=1    pos_data[0] = [-1  0  1  2  3  4  5  6  7  8 ]  pos_index_data[0] = 1
        eg_index=1 , token_index=2    pos_data[1] = [-2 -1  0  1  2  3  4  5  6  7 ]  pos_index_data[1] = 2
        eg_index=2 , token_index=3    pos_data[2] = [-3 -2 -1  0  1  2  3  4  5  6 ]  pos_index_data[2] = 3
        eg_index=3 , token_index]4    pos_data[3] = [-4 -3 -2 -1  0  1  2  3  4  5 ]  pos_index_data[3] = 4

        * Finally, note that the code below adds self.gen.max_sent_length when assigning to pos_data.
        This is to avoid any negative values. For clarity of presentation, the above examples did not do this.

        :type token_index: int
        :type example: event.event_trigger.EventTriggerExample
        """
        example.pos_data[:] = [max_sent_length + i - token_index
                               for i in range(max_sent_length)]
        example.pos_index_data[0] = token_index

    @staticmethod
    def assign_lexical_data(token_index, tokens, example, max_sent_length, neighbor_dist):
        """We want to capture [word-on-left , target-word , word-on-right]
        Use self.lex_data to capture context window, each word's embeddings or embedding index
        :type token_index: int
        :type tokens: list[text.text_span.Token]
        :type example: event.event_trigger.EventTriggerExample
        :type max_sent_length: int
        :type neighbor_dist: int

        Returns:
            list[str]
        """
        # for lex_data, I want to capture: word-on-left target-word word-on-right
        # print('token_index=', token_index, ' eg_index=', eg_index)
        token_window = EventTriggerGenerator.get_token_window(tokens, token_index, neighbor_dist)
        window_text = ['_'] * (2 * neighbor_dist + 1)
        for (i, token) in token_window:
            window_text[i] = token.text
            example.lex_data[i] = token.vector_index
            # print('lex_data[', eg_index, ', ', i, '] = ', token.text)
            example.vector_data[i + max_sent_length] = token.vector_index  # TODO why do we tag on to the back of vector_data??
        return window_text

    @staticmethod
    def get_token_window(tokens, target_index, window_size):
        """Gets the local tokens window
        :param tokens: list of tokens in the sentence
        :param target_index: indicates the target token. We want to get its surrounding tokens
        :param window_size: if this is e.g. 1, then we get its left and right neighbors
        :return: a list (max length 3) of tuples, giving the local window

        As an example, let tokens = [None, XAgent, malware, linked, to, DNC, hackers, can, now, attack, Macs]
                                      0      1        2        3    4    5      6      7    8     9      10

        If we let target_index=1, window_size=1, so we want the window around 'XAgent'. This method returns:
        [(1, XAgent), (2, malware)]

        If we let target_index=2, this method returns:
        [(0, XAgent), (1, malware), (2, linked)]

        If we let target_index=10, this method returns:
        [(0, attack), (1, Macs)]

        :type tokens: list[text.text_span.Token]
        :type target_index: int
        :type window_size: int
        Returns:
            list[(int, text.text_span.Token)]
        """
        ret = []
        for i, w in enumerate(range(target_index - window_size, target_index + window_size + 1)):
            # I am now interested in token 'w'-th in tokens (which is the list of tokens of this sentence)
            if w < 0 or w >= len(tokens):  # falls outside the current tokens, so skip
                continue
            token = tokens[w]  # type(token) == spacy_wrapper.TokenWrapper
            if token:  # the 1st token might be a padded None token, so we check for this
                ret.append((i, token))
        return ret

    def examples_to_data_dict(self, examples):
        """
        :type examples: list[event.event_trigger.EventTriggerExample
        """
        data_dict = defaultdict(list)
        for example in examples:
            #data_dict['info'].append(example.info)
            data_dict['word_vec'].append(example.vector_data)
            data_dict['pos_array'].append(example.pos_data)
            data_dict['entity_type_array'].append(example.entity_type_data)
            data_dict['pos_index'].append(example.pos_index_data)
            data_dict['lex'].append(example.lex_data)
            data_dict['label'].append(example.label)
            data_dict['token_idx'].append(example.token_idx)
        return data_dict

class EventTriggerExample(object):

    def __init__(self, token, sentence, event_domain, params, event_type=None):
        """We are given a token, sentence as context, and event_type (present during training)
        :type token: text.text_span.Token
        :type sentence: text.text_span.Sentence
        :type event_domain: event.event_domain.EventDomain
        :type params: common.parameters.Parameters
        :type event_type: str
        """
        self.token = token
        self.sentence = sentence
        self.event_domain = event_domain
        self.event_type = event_type
        self._allocate_arrays(params.get_int('max_sent_length'), params.get_int('cnn.neighbor_dist'),
                              params.get_int('embedding.none_token_index'), params.get_string('cnn.int_type'),
                              params.get_boolean('cnn.use_bio_index'))

    def _allocate_arrays(self, max_sent_length, neighbor_dist, none_token_index, int_type, use_bio_index):
        """Allocates feature vectors and matrices for examples from this sentence

        :type max_sent_length: int
        :type neighbor_dist: int
        :type none_token_index: int
        :type int_type: str
        """
        num_labels = len(self.event_domain.event_types)

        # metadata info
        # self.info_dtype = np.dtype([(b'docid', b'S40'), (b'sentNo', b'i4'), (b'trigger_token_no', b'i4')])
        # i4: 32 bit integer , S40: 40 character string
        #self.info_dtype = np.dtype([(b'docid', b'S40'), (b'text_unit_no', b'i4'),
        #                            (b'trigger_token_no', b'i4'), (b'trigger_token_i', b'i4')])
        #self.info = np.zeros(1, self.info_dtype)

        # Allocate numpy array for label
        # self.label is a 2 dim matrix: [#instances X #event-types], which I suspect will be 1-hot encoded
        self.label = np.zeros(num_labels, dtype=int_type)

        # Allocate numpy array for data
        self.vector_data = none_token_index * np.ones(max_sent_length + 2 * neighbor_dist + 1, dtype=int_type)
        self.lex_data = none_token_index * np.ones(2 * neighbor_dist + 1, dtype=int_type)
        # TODO how about replacing the above two with:
        #self.vector_data = np.zeros(max_sent_length + 2 * (2 * neighbor_dist + 1), dtype=int_type)
        #self.lex_data = np.zeros(2 * (2 * neighbor_dist + 1), dtype=int_type)

        # [#instances X max_sent_length]
        self.pos_data = np.zeros(max_sent_length, dtype=int_type)

        if use_bio_index:
            self.entity_type_data = np.zeros(max_sent_length, dtype=int_type)
        else:
            # array([ 0.])
            self.entity_type_data = np.zeros((1))

        self.pos_index_data = np.zeros(1, dtype=int_type)
        self.all_text_output = []

        # maxtrix of -1 for each element
        self.token_idx = -np.ones(max_sent_length, dtype=int_type)

        #self.ner_data = np.zeros(max_sent_length, dtype=int_type)

