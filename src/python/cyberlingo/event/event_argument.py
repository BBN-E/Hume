
from itertools import chain
from collections import defaultdict

import numpy as np

from cyberlingo.text.text_span import spans_overlap
from cyberlingo.text.text_span import Anchor
from cyberlingo.common.utils import IntPair
from cyberlingo.common.utils import Struct
from cyberlingo.event.event_trigger import EventTriggerGenerator

class EventArgumentGenerator(object):
    verbosity = 0

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

    def generate(self, docs, triggers=None):
        """
        :type docs: list[text.text_theory.Document]
        :type triggers: defaultdict(list[event.event_trigger.EventTriggerExample]
        """
        self.statistics.clear()

        examples = []
        """:type: list[event.event_argument.EventArgumentExample]"""

        for doc in docs:
            if triggers is not None:
                doc_triggers = triggers[doc.docid]
                """:type: list[event.event_trigger.EventTriggerExample]"""

                # organize the doc_triggers by sentence number
                sent_triggers = defaultdict(list)
                for trigger in doc_triggers:
                    sent_triggers[trigger.sentence.index].append(trigger)

                for sent in doc.sentences:
                    examples.extend(self._generate_sentence(sent, anchors=sent_triggers[sent.index]))
            else:
                for sent in doc.sentences:
                    examples.extend(self._generate_sentence(sent))

        for k, v in self.statistics.items():
            print('EventArgumentGenerator stats, {}:{}'.format(k,v))

        return examples

    @staticmethod
    def get_event_role(anchor, entity_mention, events):
        """If the given (anchor, entity_mention) is found in the given events, return role label, else return 'None'
        :type anchor: text.text_span.Anchor
        :type entity_mention: text.text_span.EntityMention
        :type events: list[text.text_theory.Event]
        """

        for event in events:
            for a in event.anchors:
                if anchor.start_char_offset()==a.start_char_offset() and anchor.end_char_offset()==a.end_char_offset():
                    role = event.get_role_for_entity_mention(entity_mention)
                    if role != 'None':
                        return role
        return 'None'

    def _generate_sentence(self, sentence, anchors=None):
        """We could optionally be given a list of anchors, e.g. predicted anchors
        :type sentence: text.text_span.Sentence
        :type anchors: list[event.event_trigger.EventTriggerExample]
        """
        # skip multi-token triggers, args that do not have embeddings, args that overlap with trigger
        ret = []
        """:type: list[event.event_argument.EventArgumentExample]"""

        if sentence.number_of_tokens() < 1:
            return ret
        if sentence.number_of_tokens() >= self.max_sent_length:
            print('Skipping overly long sentence of {} tokens'.format(sentence.number_of_tokens()))
            return ret

        tokens = [None] + sentence.tokens

        sent_anchors = []
        if anchors is not None:
            for anchor in anchors:
                anchor_id = '{}-s{}-t{}'.format(sentence.docid, sentence.index, len(sent_anchors))
                a = Anchor(anchor_id, IntPair(anchor.token.start_char_offset(), anchor.token.end_char_offset()), anchor.token.text,
                           anchor.event_type)
                a.with_tokens([anchor.token])
                sent_anchors.append(a)
        else:
            sent_anchors = sentence.get_all_event_anchors()
            """:type: list[text.text_span.Anchor]"""
            # to be consistent with how we train and decode triggers in EventTriggerGenerator._generate_sentence(),
            # we consider only anchors whose head token belongs to certain POS categories
            sent_anchors = [anchor for anchor in sent_anchors if anchor.head().spacy_token.pos_ in EventTriggerGenerator.trigger_pos_category]

        for anchor in sent_anchors:
            for em in sentence.entity_mentions:
                role = self.get_event_role(anchor, em, sentence.events)

                # TODO
                if spans_overlap(anchor, em):
                    if self.verbosity == 1:
                        print('Refusing to consider overlapping anchor [%s] and entity_mention [%s] as EventArgumentExample' % (anchor.to_string(), em.to_string()))
                else:
                    if role != 'None':
                        self.statistics['number_positive_argument'] += 1
                    example = EventArgumentExample(anchor, em, sentence, self.event_domain, self.params, role)
                    self._generate_example(example, tokens, self.max_sent_length, self.neighbor_dist)
                    ret.append(example)
        return ret

    @classmethod
    def _generate_example(cls, example, tokens, max_sent_length, neighbor_dist):
        """
        :type example: EventArgumentExample
        :type tokens: list[text.text_span.Token]
        :type max_sent_length: int
        :type neighbor_dist: int
        """

        anchor = example.anchor
        """:type: text.text_span.Anchor"""
        argument = example.argument
        """:type: text.text_span.EntityMention"""
        event_role = example.event_role

        # TODO need to handle multi-word arguments
        trigger_token_index = anchor.head().index_in_sentence + 1    # +1, to account for the [None] token
        # some triggers are multi-words, so we keep track of the start, end, and head token indices
        #trigger_token_indices = Struct(start=anchor.tokens[0].index_in_sentence,
        #                           end=anchor.tokens[-1].index_in_sentence, head=trigger_token_index)
        # we will just use the head token index, to be consistent with trigger training where we always use just the head for a trigger
        trigger_token_indices = Struct(start=trigger_token_index,
                                   end=trigger_token_index, head=trigger_token_index)

        arg_token_index = argument.head().index_in_sentence + 1      # +1, to account for the [None] token
        # some arguments are multi-words, so we keep track of the start, end, and head token indices
        arg_token_indices = Struct(start=argument.tokens[0].index_in_sentence + 1,
                                   end=argument.tokens[-1].index_in_sentence + 1, head=arg_token_index)
        #arg_token_indices = Struct(start=arg_token_index,
        #                           end=arg_token_index, head=arg_token_index)

        arg_role_index = example.get_event_role_index()

        # generate label data
        example.label[arg_role_index] = 1

        #if trigger_token_index == arg_token_index:
        #    print('trigger_token_index={}, trigger={}, arg_token_index={}, arg={}'.format(trigger_token_index, tokens[trigger_token_index].text, arg_token_index, tokens[arg_token_index].text))
        #    print(argument.to_string())
        #    exit(0)

        # generate lexical features, assume single token triggers
        # self.lex_data = [ #instances , 2*(2*neighbor_dist+1) ]    # local-window around trigger and argument
        # also pads the window to end of self.vector_data
        window_texts = cls._assign_lexical_data(trigger_token_indices, arg_token_indices, tokens, example, max_sent_length, neighbor_dist)

        # self.token_idx = [ #instances , self.gen.max_sent_length ]
        cls._assign_token_idx(tokens, example)

        cls._assign_event_data(tokens, example)

        # self.vector_data = [ #instances , max_sent_length + 2*(2*neighbor_dist+1) ]
        cls._assign_vector_data(tokens, example)

        # token_texts = [ self.gen.max_sent_length ]    # lexical text of each token in sentence
        token_texts = cls._assign_token_texts(tokens, max_sent_length)

        # self.pos_data = [ #instances , 2, max_sent_length ]  # relative position of other words to trigger & arg
        # self.pos_index_data = [ #instances , 2 ]  # for each example, keep track of token index of trigger & arg
        index_pair = (min(trigger_token_index, arg_token_index), max(trigger_token_index, arg_token_index))
        cls._assign_position_data(trigger_token_indices, arg_token_indices, index_pair, example, max_sent_length)

        #cls._assign_ner_data(tokens, example)

        cls._check_assertions(index_pair, tokens, trigger_token_index, arg_token_index, argument.head(), example, max_sent_length)

    @staticmethod
    def _window_indices(target_indices, window_size):
        """Generates a window of indices around target_index (token index within the sentence)

        :type target_indices: common.utils.Struct
        """
        indices = []
        indices.extend(range(target_indices.start - window_size, target_indices.start))
        indices.append(target_indices.head)
        indices.extend(range(target_indices.end + 1, target_indices.end + window_size + 1))
        return indices
        #return range(target_index - window_size, target_index + window_size + 1)

    @classmethod
    def _get_token_windows(cls, tokens, window_size, trigger_token_indices, arg_token_indices):
        """
        :type trigger_token_indices: common.utils.Struct
        :type arg_token_indices: common.utils.Struct
        :type tokens: list[text.text_span.Token]
        Returns:
            list[(int,text.text_span.Token)]
        """
        ret = []
        # chain just concatenates the 2 lists
        for i, w in enumerate(chain(cls._window_indices(trigger_token_indices, window_size),
                                    cls._window_indices(arg_token_indices, window_size))):
            if w < 0 or w >= len(tokens):
                continue
            token = tokens[w]
            if token:
                ret.append((i, token))
        return ret

    @classmethod
    def _assign_lexical_data(cls, trigger_token_indices, arg_token_indices, tokens, example, max_sent_length, neighbor_dist):
        """
        :type trigger_token_indices: common.utils.Struct
        :type arg_token_indices: common.utils.Struct
        :type example: EventArgumentExample
        :type max_sent_length: int
        :type neighbor_dist: int
        """
        # get the local token windows around the trigger and argument
        token_windows = cls._get_token_windows(tokens, neighbor_dist, trigger_token_indices, arg_token_indices)
        window_texts = ['_'] * 2 * (2 * neighbor_dist + 1)

        for (i, token) in token_windows:
            if token.has_vector:
                example.lex_data[i] = token.vector_index
                example.vector_data[i + max_sent_length] = token.vector_index
                window_texts[i] = token.text
            else:
                window_texts[i] = token.text
        return window_texts

    @staticmethod
    def _assign_token_idx(tokens, example):
        """
        :type tokens: list[text.text_span.Token]
        :type example: event.event_argument.EventArgumentExample
        """
        for i, token in enumerate(tokens):
            if token:
                example.token_idx[i] = token.spacy_token.i  # index of token within spacy document

    @staticmethod
    def _assign_event_data(tokens, example):
        """
        :type tokens: list[text.text_span.Token]
        :type example: event.event_argument.EventArgumentExample
        """
        for i, token in enumerate(tokens):
            if token:
                example.event_data[i] = example.event_domain.get_event_type_index(example.anchor.label)

    @staticmethod
    def _assign_ner_data(tokens, example):
        """
        :type tokens: list[text.text_span.Token]
        :type example: event.event_argument.EventArgumentExample
        """
        token_ne_type = example.sentence.get_ne_type_per_token()
        assert len(token_ne_type)+1 == len(tokens)
        for i, token in enumerate(tokens):
            if token:
                example.ner_data[i] = example.event_domain.get_entity_type_index(token_ne_type[i-1])

    @staticmethod
    def _assign_vector_data(tokens, example):
        """Capture the word embeddings, or embeddings index, at each word position in sentence
        :type tokens: list[text.text_span.Token]
        :type example: event.event_argument.EventArgumentExample
        """
        for i, token in enumerate(tokens):
            if token and token.has_vector:
                example.vector_data[i] = token.vector_index

    @staticmethod
    def _assign_token_texts(tokens, max_sent_length):
        """Lexical text of each token in the sentence
        :type tokens: list[text.text_span.Token]
        :type max_sent_length: int
        """
        token_texts = ['_'] * max_sent_length
        for i, token in enumerate(tokens):
            if token:
                token_texts[i] = u'{0}'.format(token.text)  # TODO want to use token.vector_text instead?
        return token_texts

    @staticmethod
    def _assign_position_data(trigger_token_indices, arg_token_indices, index_pair, example, max_sent_length):
        """
        NOTE: you do not know whether index_pair[0] refers to the trigger_token_index or arg_token_index.
        Likewise for index_pair[1]. You only know that index_pair[0] < index_pair[1]

        :type trigger_token_indices: common.utils.Struct
        :type arg_token_indices: common.utils.Struct
        :type example: event.event_argument.EventArgumentExample
        :type max_sent_length: int
        """
        # distance from trigger
        #example.pos_data[0, :] = [i - trigger_token_index + max_sent_length for i in range(max_sent_length)]
        trigger_data = []
        for i in range(max_sent_length):
            if i < trigger_token_indices.start:
                trigger_data.append(i - trigger_token_indices.start + max_sent_length)
            elif trigger_token_indices.start <= i and i <= trigger_token_indices.end:
                trigger_data.append(0 + max_sent_length)
            else:
                trigger_data.append(i - trigger_token_indices.end + max_sent_length)
        example.pos_data[0, :] = trigger_data

        # distance from argument
        #example.pos_data[1, :] = [i - arg_token_index + max_sent_length for i in range(max_sent_length)]
        arg_data = []
        for i in range(max_sent_length):
            if i < arg_token_indices.start:
                arg_data.append(i - arg_token_indices.start + max_sent_length)
            elif arg_token_indices.start <= i and i <= arg_token_indices.end:
                arg_data.append(0 + max_sent_length)
            else:
                arg_data.append(i - arg_token_indices.end + max_sent_length)
        example.pos_data[1, :] = arg_data
        
        # for each example, keep track of the token index of trigger and argument
        example.pos_index_data[0] = index_pair[0]
        example.pos_index_data[1] = index_pair[1]

    @staticmethod
    def _check_assertions(index_pair, trunc_tokens, trunc_anchor_index, trunc_target_index, target_token, example, max_sent_length):
        """
        :type trunc_tokens: list[text.text_span.Token]
        :type target_token: text.text_span.Token
        :type example: event.event_argument.EventArgumentExample
        """
        assert (trunc_anchor_index == example.pos_index_data[index_pair.index(trunc_anchor_index)])
        assert (trunc_target_index == example.pos_index_data[1-index_pair.index(trunc_anchor_index)])
        assert (target_token == trunc_tokens[example.pos_index_data[1-index_pair.index(trunc_anchor_index)]])

        #if not (example.pos_index_data[0] < example.pos_index_data[1]):
        #    raise ValueError('0:{} 1:{}'.format(example.pos_index_data[0], example.pos_index_data[1]))
        assert (example.pos_data[0, trunc_anchor_index] == max_sent_length)
        assert (example.pos_data[1, trunc_target_index] == max_sent_length)
        assert np.all(example.pos_data[:, :] < 2*max_sent_length)
        assert np.all(example.pos_data[:, :] >= 0)
        offset = 1
        assert (np.min(example.pos_index_data[:]) >= offset)

    def examples_to_data_dict(self, examples):
        """
        :type examples: list[event.event_trigger.EventArgumentExample
        """
        data_dict = defaultdict(list)
        for example in examples:
            #data_dict['info'].append(example.info)
            data_dict['word_vec'].append(example.vector_data)
            data_dict['pos_array'].append(example.pos_data)
            data_dict['event_array'].append(example.event_data)
            data_dict['pos_index'].append(example.pos_index_data)
            data_dict['lex'].append(example.lex_data)
            data_dict['label'].append(example.label)
            data_dict['token_idx'].append(example.token_idx)
            #data_dict['ne_array'].append(example.ner_data)
        return data_dict

class EventArgumentExample(object):

    def __init__(self, anchor, argument, sentence, event_domain, params, event_role=None):
        """We are given an anchor, candidate argument, sentence as context, and a role label (absent in decoding)
        :type anchor: text.text_span.Anchor
        :type argument: text.text_span.EntityMention
        :type sentence: text.text_span.Sentence
        :type event_domain: event.event_domain.EventDomain
        :type params: common.parameters.Parameters
        :type event_role: str
        """
        self.anchor = anchor
        self.argument = argument
        self.sentence = sentence
        self.event_domain = event_domain
        self.event_role = event_role
        self._allocate_arrays(params.get_int('max_sent_length'), params.get_int('cnn.neighbor_dist'),
                              params.get_int('embedding.none_token_index'), params.get_string('cnn.int_type'))

    def get_event_role_index(self):
        return self.event_domain.get_event_role_index(self.event_role)

    def _allocate_arrays(self, max_sent_length, neighbor_dist, none_token_index, int_type):
        """
        :type max_sent_length: int
        :type neighbor_dist: int
        :type none_token_index: int
        :type int_type: str
        """
        num_labels = len(self.event_domain.event_roles)

        # metadata info
        # i4: 32 bit integer , S40: 40 character string
        #self.info_dtype = np.dtype([(b'docid', b'S40'), (b'text_unit_no', b'i4'),
        #                           (b'trigger_token_no', b'i4'), (b'role_token_no', b'i4'),
        #                           (b'trigger_token_i', b'i4'), (b'role_token_i', b'i4')])
        #self.info = np.zeros(1, self.info_dtype)

        # self.label is a 2 dim matrix: [#instances , #event-roles], which I suspect will be 1-hot encoded
        self.label = np.zeros(num_labels, dtype=int_type)

        ## Allocate numpy array for data
        self.vector_data = np.zeros(max_sent_length + 2*(2*neighbor_dist+1), dtype=int_type)
        self.lex_data = np.zeros(2*(2*neighbor_dist+1), dtype=int_type)
        self.vector_data[:] = none_token_index
        self.lex_data[:] = none_token_index

        # pos_data = [ #instances , 2 , max_sent_length ]
        self.pos_data = np.zeros((2, max_sent_length), dtype=int_type)
        # pos_index_data = [ #instances , 2 ]
        self.pos_index_data = np.zeros(2, dtype=int_type)
        # event_data = [ #instances , max_sent_length ]
        self.event_data = np.zeros(max_sent_length, dtype=int_type)
        self.all_text_output = []
        # token_idx = [ #instances , max_sent_length ] , maxtrix of -1 for each element
        self.token_idx = -np.ones(max_sent_length, dtype=int_type)

        #self.ner_data = np.zeros(max_sent_length, dtype=int_type)
