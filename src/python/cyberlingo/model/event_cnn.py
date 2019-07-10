from __future__ import absolute_import
from __future__ import division
from __future__ import with_statement

import keras
import numpy as np
from future.builtins import zip
from keras.layers import Flatten, GlobalMaxPooling1D
from keras.layers import Input, merge
from keras.layers.convolutional import Convolution1D
from keras.layers.core import Dense, Dropout
from keras.layers.embeddings import Embedding
from keras.models import Model
from keras.optimizers import Adadelta

from cyberlingo.common.utils import F1Score
from cyberlingo.model.my_keras import MyRange
from cyberlingo.model.my_keras import MySelect


def evaluate_f1(prediction, label, none_class_index, num_true=None):
    """We will input num_true if we are using predicted triggers to score arguments

    ('- prediction=', array([[ 0.00910971,  0.00806234,  0.03608446,  0.94674349],
       [ 0.02211222,  0.01518068,  0.17702729,  0.78567982],
       [ 0.01333893,  0.00946771,  0.03522802,  0.94196534],
       ...,
       [ 0.00706887,  0.01225629,  0.01827211,  0.9624027 ],
       [ 0.0132369 ,  0.03686138,  0.02967645,  0.92022526],
       [ 0.01413057,  0.03428967,  0.02316411,  0.92841566]], dtype=float32))
    ('- label=', array([[0, 0, 0, 1],
       [0, 0, 1, 0],
       [0, 0, 0, 1],
       ...,
       [0, 0, 0, 1],
       [0, 0, 0, 1],
       [0, 0, 0, 1]], dtype=int32))

    label: matrix of size (#instance, #label-types)
    So doing an argmax along 2nd dimension amounts to
    extracting the index of the true/predicted label, for each instance

    ('- label_arg_max=', array([3, 2, 3, ..., 3, 3, 3])

    :type event_domain: event.event_domain.EventDomain
    :type none_label_index: int

    Returns:
        common.utils.F1Score
    """

    num_instances = label.shape[0]
    label_arg_max = np.argmax(label, axis=1)
    pred_arg_max = np.argmax(prediction, axis=1)

    #print('- prediction=', prediction)
    #print('- label=', label)
    #print('- none_class_index=', none_class_index)
    #print('- label_arg_max=', label_arg_max)
    #print('- pred_arg_max=', pred_arg_max)

    # check whether each element in label_arg_max != none_class_index
    # So the result is a 1-dim vector of size #instances, where each element is True or False
    # And then we sum up the number of True elements to obtain the num# of true events
    if num_true == None:
        num_true = np.sum(label_arg_max != none_class_index)
    num_predict = np.sum(pred_arg_max != none_class_index)

    c = 0
    for i, j in zip(label_arg_max, pred_arg_max):
        if i == j and i != none_class_index:
            c += 1

    return F1Score(c, num_true, num_predict)


def evaluate_arg_f1(event_domain, test_label, test_examples, predictions):
    """
    :type event_domain: event.event_domain.EventDomain
    :type test_label: np.array
    :type test_examples: list[event.event_argument.EventArgumentExample]

    Returns:
        common.utils.F1Score
    """
    assert len(test_label) == len(test_examples)
    assert len(predictions) == len(test_examples)

    none_class_index = event_domain.get_event_role_index('None')

    gold_data = set()
    test_arg_max = np.argmax(test_label, axis=1)
    for i, index in enumerate(test_arg_max):
        if index != none_class_index:
            eg = test_examples[i]
            """:type: event.event_argument.EventArgumentExample"""
            id = '{}_{}_{}'.format(eg.sentence.docid, eg.argument.head().start_char_offset(),
                                   eg.argument.head().end_char_offset())
            label = '{}_{}'.format(eg.anchor.label, event_domain.get_event_role_from_index(index))
            gold_data.add('{}__{}'.format(id, label))

    predict_data = set()
    pred_arg_max = np.argmax(predictions, axis=1)
    for i, index in enumerate(pred_arg_max):
        if index != none_class_index:
            eg = test_examples[i]
            """:type: event.event_argument.EventArgumentExample"""
            id = '{}_{}_{}'.format(eg.sentence.docid, eg.argument.head().start_char_offset(),
                                   eg.argument.head().end_char_offset())
            label = '{}_{}'.format(eg.anchor.label, event_domain.get_event_role_from_index(index))
            predict_data.add('{}__{}'.format(id, label))

    c = len(gold_data.intersection(predict_data))
    num_true = len(gold_data)
    num_predict = len(predict_data)
    return F1Score(c, num_true, num_predict)

class EventExtractionModel(object):
    verbosity = 0

    keras_custom_objects = {
        u'MyRange': MyRange,
        u'MySelect': MySelect,
        #u'ShiftPosition': ShiftPosition,
        #u'DynamicMultiPooling': DynamicMultiPooling,
        #u'DynamicMultiPooling3': DynamicMultiPooling3,
    }

    def __init__(self, params, event_domain, embeddings, batch_size, num_feature_maps, optimizer=None):
        """
        :type event_domain: event.event_domain.EventDomain
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        :type model_name: str
        """
        self.event_domain = event_domain
        self.num_event_types = len(event_domain.event_types)
        self.num_role_types = len(event_domain.event_roles)
        self.num_ne_types = len(event_domain.entity_types)

        # Input consists of two parts sentence feature and lexical feature.
        # Lexical feature is the trigger token and its surrounding context tokens.

        # Sentence feature is all the tokens in the sentences and the distance
        #  of each token to the trigger token.

        self.sent_length = params.get_int('max_sent_length')   # Number of tokens per sentence
        self.word_vec_length = 1                    # because we use word vector index

        self.position_embedding_vec_len = params.get_int('cnn.position_embedding_vec_len')
        self.filter_length = params.get_int('cnn.filter_length')
        self.dropout = params.get_float('cnn.dropout')

        self.num_feature_maps = num_feature_maps    # number of convolution feature maps

        self.word_embeddings = embeddings.word_vec
        """:type: numpy.ndarray"""
        # self.num_lexical_tokens = 3                 # number of lexical tokens

        if optimizer is None:
            optimizer = Adadelta(rho=0.95, epsilon=1e-6)
        self.optimizer = optimizer

        self.batch_size = batch_size
        self.data_keys = []
        self.keras_model = None
        #self.keras_model_filename = None
        self.num_output = None

    #def get_metric_list(self):
    #    return []

    def create_model(self):
        pass

    def __getstate__(self):
        u"""Defines what is to be pickled.
        Keras models cannot be pickled. Should call save_keras_model() and load_keras_model() separately.
        The sequence is :
        obj.save_keras_model('kerasFilename')
        pickle.dump(obj, fileHandle)
        ...
        obj = pickle.load(fileHandle)
        obj.load_keras_model()"""

        # Create state without self.keras_model
        state = dict(self.__dict__)
        state.pop(u'keras_model')
        return state

    def __setstate__(self, state):
        u"""Reload state for unpickling"""
        self.__dict__ = state
        self.keras_model = None

    # def save_keras_model(self, filename):
    #     self.keras_model_filename = filename
    #     self.keras_model.save(filename)

    def load_keras_model(self, filename=None):
        self.keras_model = keras.models.load_model(filename, self.keras_custom_objects)

    # def create_word_embedding_layer(self, trainable=False):
    #     return Embedding(self.word_embedding_array.shape[0], self.word_embedding_array.shape[1],
    #                      weights=[self.word_embedding_array], trainable=trainable)

    def fit(self, train_label, train_data_list, test_label, test_data_list, sample_weight=None, max_epoch=10):
        if self.verbosity == 1:
            print('\nevent_cnn.py : EventExtractionModel.fit()')
            print('- train_label=', train_label)
            print('- train_data_list=', train_data_list)
            print('- test_label=', test_label)
            print('- test_data_list=', test_data_list)
            print('- sample_weight=', sample_weight)
            print('- epoch=', max_epoch)

        if sample_weight is None:
            sample_weight = np.ones((train_label.shape[0]))

        #print('* invoking keras_model.fit()')
        #print('- self.keras_model=', self.keras_model)
        history = self.keras_model.fit(train_data_list, train_label,
                                       sample_weight=sample_weight, batch_size=self.batch_size, nb_epoch=max_epoch,
                                       validation_data=(test_data_list, test_label))
        #print('* returned from self.keras_model.fit()')
        return history

    def predict(self, test_data_list):
        pred_result = self.keras_model.predict(test_data_list)
        return pred_result

    # @classmethod
    # def run_model(cls, train, test, weights=range(1, 11), epoch=10, num_skipped_events=0, model_params={}):
    #     all_results = []
    #     best_f1 = 0
    #     best_model = None
    #     for weight in weights:
    #         print(u'Weight={0}'.format(weight))
    #         model = cls(**model_params)
    #         history = model.fit(train, test, event_weight=weight, epoch=epoch)
    #         # print('training')
    #         print(u'testing')
    #         pred = model.predict(test)
    #         evala = ace_eval(pred, test[u'label'], model.num_output, num_skipped_events=num_skipped_events)
    #         if evala[u'f1'] > best_f1:
    #             best_f1 = evala[u'f1']
    #             best_model = model
    #         result = {}
    #         result[u'history'] = history
    #         result[u'pred'] = pred
    #         result[u'eval'] = evala
    #         result[u'description'] = u'weight={0}'.format(weight)
    #         all_results.append(result)
    #     return (all_results, best_model)

    # def fit_weight_boost(self, train_label, train_data_list, test_label, test_data_list,
    #         event_weight=1, sample_weight=None, max_epoch=5):
    #     print('\ncnn.py : EventExtractionModel.fit()')
    #     print('- train_label=', train_label)
    #     print('- train_data_list=', train_data_list)
    #     print('- test_label=', test_label)
    #     print('- test_data_list=', test_data_list)
    #     print('- event_weight=', event_weight)
    #     print('- sample_weight=', sample_weight)
    #     print('- epoch=', max_epoch)
    #
    #     if sample_weight is None:
    #         sample_weight = np.ones((train_label.shape[0]))
    #         sample_weight[train_label[:, self.num_output - 1] != 1] = event_weight
    #
    #     print('* invoking keras_model.fit_weight_boost()')
    #     print('- self.keras_model=', self.keras_model)
    #
    #     weight = np.ones(train_label.shape[0])
    #     for epoch in range(1, max_epoch + 1):
    #         history = self.keras_model.fit(train_data_list, train_label,
    #                                    sample_weight=weight, batch_size=self.batch_size, nb_epoch=5,
    #                                    validation_data=(test_data_list, test_label))
    #         predictions = self.predict(test_data_list)
    #         evaluate_f1(predictions, test_label, self.event_domain.get_event_type_index('None'))
    #
    #         if epoch < max_epoch:
    #             predictions = self.predict(train_data_list)
    #             pred_train_argmax = np.argmax(predictions, axis=1)
    #             for i in range(len(weight)):
    #                 if train_label[i, pred_train_argmax[i]] == 1:
    #                     weight[i] /= 1.2  # I got this correct, so I'm decreasing the weight
    #                 else:
    #                     weight[i] *= 1.2  # I got this wrong, so I'm increasing the weight
    #     return history

    # @classmethod
    # def run_weight_boost_model(cls, train, test, epoch_max=10, weight_factor=1.2,
    #                            num_skipped_events=None, num_total_events=None, outfile_pattern=None, model_params={}):
    #     print('\ntrigger_class_dm_pool_model.py : EventExtractionModel().run_weight_boost_model()')
    #     print('- train=', train)
    #     print('- test=', test)
    #     print('- epoch_max=', epoch_max)
    #     print('- weight_factor=', weight_factor)
    #     print('- num_skippepd_events=', num_skipped_events)
    #     print('- num_total_events=', num_total_events)
    #     print('- outfile_pattern=', outfile_pattern)
    #     print('- model_params=', model_params)
    #
    #     model = cls(**model_params)
    #     all_results = []
    #     train_label = train[u'label']
    #     weight = np.ones(train_label.shape[0])
    #     for epoch in range(1, epoch_max + 1):
    #         epoch_start_time = time.time()
    #         print('Epoch = {0}/{1}, invoking model.fit'.format(epoch, epoch_max))
    #         history = model.fit(train, test, sample_weight=weight, epoch=1)
    #         training_time = time.time() - epoch_start_time
    #         print('* invoking model.predict')
    #         pred_test = model.predict(test)
    #         print('* invoking ace_eval()')
    #         eval_test = ace_eval(pred_test, test[u'label'], model.num_output,
    #                              num_skipped_events=num_skipped_events, num_total_events=num_total_events)
    #         print('* returned from ace_eval()')
    #         result = {}
    #         result[u'history'] = history
    #         result[u'pred'] = pred_test
    #         result[u'eval'] = eval_test
    #         result[u'description'] = u'epoch={0}'.format(epoch)
    #         if outfile_pattern:
    #             keras_model_filename = outfile_pattern.format(**{u'epoch': epoch, u'type': u'hdf'})
    #             model_filename = outfile_pattern.format(**{u'epoch': epoch, u'type': u'pickle'})
    #             model.description[u'epoch'] = epoch
    #             save_model(model, model_filename, keras_model_filename)
    #             result[u'model_filename'] = model_filename
    #         if epoch < epoch_max:
    #             print(u'Adjusting Weights')
    #             pred_train = model.predict(train)
    #             pred_train_arg = np.argmax(pred_train, axis=1)
    #             for i in range(len(weight)):
    #                 if train_label[i, pred_train_arg[i]] == 1:
    #                     weight[i] /= weight_factor  # I got this correct, so I'm decreasing the weight
    #                 else:
    #                     weight[i] *= weight_factor  # I got this wrong, so I'm increasing the weight
    #             print(u'Adjusting weight max/min={0}/{1}'.format(np.max(weight), np.min(weight)))
    #         epoch_end_time = time.time()
    #         result['train_time'] = training_time
    #         result['epoch_time'] = epoch_end_time - epoch_start_time
    #         all_results.append(result)
    #     return (all_results, model)

class TriggerModel(EventExtractionModel):
    def __init__(self, params, event_domain, embeddings):
        """
        :type event_domain: event.event_domain.EventDomain
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        """
        super(TriggerModel, self).__init__(params, event_domain, embeddings,
                                           batch_size=params.get_int('trigger.batch_size'),
                                           num_feature_maps=params.get_int('trigger.num_feature_maps'))
        self.num_output = len(event_domain.event_types)
        self.positive_weight = params.get_float('trigger.positive_weight')
        self.epoch = params.get_int('trigger.epoch')

    def fit(self, train_data_list, train_label, test_data_list, test_label):
        if self.verbosity == 1:
            print('- train_data_list=', train_data_list)
            print('- train_label=', train_label)

        none_label_index = self.event_domain.get_event_type_index('None')
        sample_weight = np.ones(train_label.shape[0])
        label_argmax = np.argmax(train_label, axis=1)
        for i, label_index in enumerate(label_argmax):
            if label_index != none_label_index:
                sample_weight[i] = self.positive_weight

        super(TriggerModel, self).fit(train_label, train_data_list, test_label, test_data_list,
                    sample_weight=sample_weight, max_epoch=self.epoch)

class MaxPoolEmbeddedTriggerModel(TriggerModel):
    def __init__(self, params, event_domain, embeddings):
        """
        :type event_domain: event.event_domain.EventDomain
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        """
        super(MaxPoolEmbeddedTriggerModel, self).__init__(params, event_domain, embeddings)
        self.train_embedding = False
        self.create_model()

    def create_model(self):
        # For each word the pos_array_input defines the distance to the target work.
        # Embed each distance into an 'embedding_vec_length' dimensional vector space
        pos_array_input = Input(shape=(self.sent_length,), dtype=u'int32', name=u'position_array')
        # the input dimension is 2*self.sent_length, because the range of numbers go from min=0 to max=2*self.sent_length
        pos_embedding = Embedding(2*self.sent_length, self.position_embedding_vec_len)(pos_array_input)

        # Input is vector of embedding indice representing the sentence
        # !!!! + 3
        context_input = Input(shape=(self.sent_length+3,), dtype=u'int32', name=u'word_vector')
        all_words = Embedding(self.word_embeddings.shape[0], self.word_embeddings.shape[1],
                             weights=[self.word_embeddings], trainable=self.train_embedding)(context_input)

        context_words = MyRange(0, -3)(all_words)

        # Sentence feature input is the result of mergeing word vectors and embeddings
        merged = merge([context_words, pos_embedding], mode=u'concat')

        # Note: border_mode='same' to keep output the same width as the input
        conv = Convolution1D(self.num_feature_maps, self.filter_length, border_mode=u'same')(merged)

        # Dynamially max pool 'conv' result into 3 max value
        maxpool = GlobalMaxPooling1D()(conv)

        Convolution1D(self.num_feature_maps, self.filter_length, border_mode=u'valid')

        # Input anchor and target words, plus +/- one context words
        # lex_vector = Input(shape=(3,self.word_vec_length), name='lex')

        # Input indicating the position of the target
        # pos_index_input = Input(shape=(1,), dtype='int32', name='position_index')
        lex_vector = MyRange(-3, None)(all_words)

        # Lexical level feature
        lex_flattened = Flatten()(lex_vector)

        # Merge sentance and lexcial features
        merged_all = merge([maxpool, lex_flattened], mode=u'concat')

        # Dense MLP layer with dropout
        dropout = Dropout(self.dropout)(merged_all)

        out = Dense(self.num_output, activation=u'softmax')(dropout)

        self.keras_model = Model(input=[context_input, pos_array_input], output=[out])

        self.keras_model.compile(optimizer=self.optimizer,
                                loss=u'categorical_crossentropy',
                                metrics=[])


class RoleModel(EventExtractionModel):
    def __init__(self, params, event_domain, embeddings):
        """
        :type event_domain: event.event_domain.EventDomain
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        """
        super(RoleModel, self).__init__(params, event_domain, embeddings,
                                        batch_size=params.get_int('role.batch_size'),
                                        num_feature_maps=params.get_int('role.num_feature_maps'))
        self.num_output = len(event_domain.event_roles)
        self.positive_weight = params.get_float('role.positive_weight')
        self.entity_embedding_vec_length = params.get_int('role.entity_embedding_vec_length')  # entity embedding vector length
        self.epoch = params.get_int('role.epoch')

    def fit(self, train_data_list, train_label, test_data_list, test_label):
        if self.verbosity == 1:
            print('- train_data_list=', train_data_list)
            print('- train_label=', train_label)

        none_label_index = self.event_domain.get_event_role_index('None')
        sample_weight = np.ones(train_label.shape[0])
        label_argmax = np.argmax(train_label, axis=1)
        for i, label_index in enumerate(label_argmax):
            if label_index != none_label_index:
                sample_weight[i] = self.positive_weight

        super(RoleModel, self).fit(train_label, train_data_list, test_label, test_data_list,
                    sample_weight=sample_weight, max_epoch=self.epoch)


class MaxPoolEmbeddedRoleModel(RoleModel):
    def __init__(self, params, event_domain, embeddings):
        """
        :type event_domain: event.event_domain.EventDomain
        :type embeddings: embeddings.word_embeddings.WordEmbedding
        """
        super(MaxPoolEmbeddedRoleModel, self).__init__(params, event_domain, embeddings)
        self.train_embedding = False
        self.create_model()

    def create_model(self):
        # For each word the pos_array_input defines two coordinates:
        # distance(word,anchor) and distance(word,target).  Embed each distances
        # into an 'embedding_vec_length' dimensional vector space
        pos_array_input = Input(shape=(2, self.sent_length), dtype=u'int32', name=u'position_array')

        anchor_pos_array = MySelect(0)(pos_array_input)
        target_pos_array = MySelect(1)(pos_array_input)

        anchor_embedding = Embedding(2 * self.sent_length, self.position_embedding_vec_len)(anchor_pos_array)
        target_embedding = Embedding(2 * self.sent_length, self.position_embedding_vec_len)(target_pos_array)

        # Each word is tagged with the SAME event number. Note sure why this event
        # number needs to be repeated, just following the description of the Chen et al
        # DMPooling paper. Embed event in vector space
        event_array_input = Input(shape=(self.sent_length,), dtype=u'int32', name=u'event_array')
        event_embedding = Embedding(self.num_event_types,
                                    self.position_embedding_vec_len)(event_array_input)

        # ne_input = Input(shape=(self.sent_length,), dtype=u'int32', name=u'ne_array')
        # ne_embedding = Embedding(self.num_ne_types,
        #                             self.position_embedding_vec_len)(ne_input)

        # Input is matrix representing a sentence of self.sent_length tokens, where each token
        # is a vectors of length self.word_vec_length + 6
        # !!!! extra 6 tokens for the two tokens around trigger, and two tokens around role argument
        context_input = Input(shape=(self.sent_length + 6,), name=u'word_vector')
        all_words = Embedding(self.word_embeddings.shape[0], self.word_embeddings.shape[1],
                              weights=[self.word_embeddings], trainable=self.train_embedding)(context_input)

        context_word_input = MyRange(0, -6)(all_words)

        # Sentence feature input is the result of mergeing word vectors and embeddings
        merged = merge([context_word_input, anchor_embedding, target_embedding, event_embedding],
                       mode=u'concat')

        # Note: border_mode='same' to keep output the same width as the input
        conv = Convolution1D(self.num_feature_maps, self.filter_length, border_mode=u'same')(merged)

        # Dynamially max pool 'conv' result into 3 max value
        maxpool = GlobalMaxPooling1D()(conv)

        # Input anchor and target words, plus +/- one context words
        # lex_input = Input(shape=(2 * self.num_lexical_tokens, self.word_vec_length), name=u'lex')
        lex_vector = MyRange(-6, None)(all_words)

        # Lexical level feature
        lex_flattened = Flatten()(lex_vector)

        # Merge sentance and lexcial features
        merged_all = merge([maxpool, lex_flattened], mode=u'concat')

        # Dense MLP layer with dropout
        dropout = Dropout(self.dropout)(merged_all)
        # outputSize = numRoles
        out = Dense(self.num_output, activation=u'softmax')(dropout)

        self.keras_model = Model(input=[context_input, pos_array_input, event_array_input],
                                 output=[out])

        self.keras_model.compile(optimizer=self.optimizer,
                                 loss=u'categorical_crossentropy',
                                 metrics=[])

