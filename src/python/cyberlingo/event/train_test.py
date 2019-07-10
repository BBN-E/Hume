from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
import codecs
import re

import spacy

import pickle

from collections import defaultdict

import numpy as np

from cyberlingo.text.text_theory import Document
from cyberlingo.annotation.idt import process_idt_file
from cyberlingo.annotation.enote import process_enote_file
from cyberlingo.embeddings.word_embeddings import WordEmbedding
from cyberlingo.event.event_trigger import EventTriggerGenerator
from cyberlingo.event.event_argument import EventArgumentGenerator
from cyberlingo.event.event_domain import CyberDomain
from cyberlingo.event.event_domain import AceDomain
import cyberlingo.common.utils as text_utils
from cyberlingo.common.parameters import Parameters

from cyberlingo.model.event_cnn import MaxPoolEmbeddedTriggerModel
from cyberlingo.model.event_cnn import MaxPoolEmbeddedRoleModel
from cyberlingo.model.event_cnn import evaluate_f1
from cyberlingo.model.event_cnn import evaluate_arg_f1

from cyberlingo.annotation.ace import AceAnnotation

def parse_filelist_line(line):
    text_file = None
    idt_file = None
    enote_file = None
    acetext_file = None # ACE text file, where we only care about texts not within xml-tags
    apf_file = None     # ACE xml file

    for file in line.strip().split():
        if file.startswith('TEXT:'):
            text_file = file[len('TEXT:'):]
        elif file.startswith('IDT:'):
            idt_file = file[len('IDT:'):]
        elif file.startswith('ENOTE:'):
            enote_file = file[len('ENOTE:'):]
        elif file.startswith('ACETEXT:'):
            acetext_file = file[len('ACETEXT:'):]
        elif file.startswith('APF:'):
            apf_file = file[len('APF:'):]

    if text_file is None and acetext_file is None:
        raise ValueError('text_file or acetext_file must be present!')
    return (text_file, idt_file, enote_file, acetext_file, apf_file)

def read_doc_annotation(filelists):
    """
    :type filelists: list[str]
    Returns:
        list[text.text_theory.Document]
    """
    docs = []
    """:type docs: list[text.text_theory.Document]"""
    for line in filelists:
        (text_file, idt_file, enote_file, acetext_file, apf_file) = parse_filelist_line(line)

        if text_file is not None:
            docid = os.path.basename(text_file)
            text_f = codecs.open(text_file, 'r', encoding='utf-8')
            all_text = text_f.read()
            text_f.close()
            doc = Document(docid, all_text.strip())

        if acetext_file is not None:
            docid = re.match(r'(.*).sgm', os.path.basename(acetext_file)).group(1)
            text_list = AceAnnotation.process_ace_textfile_to_list(acetext_file)
            # sometimes, e.g. for ACE, we need to keep the sentence strings separate. In ACE sgm files, it contains
            # things like '&amp;' which Spacy normalizes to a single character '&' and Spacy thus changed the original
            # character offsets. This is bad for keeping correspondences with the .apf file for character offsets.
            # So we let it affect 1 sentence or 1 paragraph, but not the rest of the document.

            # Some ACE text files have words that end with a dash e.g. 'I-'. This presents a problem. The annotation
            # file annotates 'I', but Spacy keeps it as a single token 'I-', and then I won't be able to find
            # Spacy tokens to back the Anchor or EntityMention. To prevent these from being dropped, we will replace
            # all '- ' with '  '.
            text_list = [s.replace(r'- ', '  ') for s in text_list]
            text_list = [s.replace(r' ~', '  ') for s in text_list]
            text_list = [s.replace(r'~ ', '  ') for s in text_list]
            text_list = [s.replace(r' -', '  ') for s in text_list]
            text_list = [s.replace(r'.-', '. ') for s in text_list] # e.g. 'U.S.-led' => 'U.S. led', else Spacy splits to 'U.S.-' and 'led'
            text_list = [s.replace(r'/', ' ') for s in text_list]

            doc = Document(docid, text=None, sentence_strings=text_list)

        if idt_file is not None:
            doc = process_idt_file(doc, idt_file)  # adds entity mentions
        if enote_file is not None:
            doc = process_enote_file(doc, enote_file, auto_adjust=True)  # adds events
        if apf_file is not None:
            doc = AceAnnotation.process_ace_xmlfile(doc, apf_file)

        docs.append(doc)
    return docs

def prepare_docs(filelists):
    # read IDT and ENote annotations
    docs = read_doc_annotation(text_utils.read_file_to_list(filelists))

    # apply Spacy for sentence segmentation and tokenization, using Spacy tokens to back Anchor and EntityMention
    spacy_en = spacy.load('en')
    for doc in docs:
        doc.annotate_sentences(spacy_en, word_embeddings)

    number_anchors = 0
    number_args = 0
    number_assigned_anchors = 0
    number_assigned_args = 0
    number_assigned_multiword_anchors = 0
    for doc in docs:
        for event in doc.events:
            number_anchors += event.number_of_anchors()
            number_args += event.number_of_arguments()
        for sent in doc.sentences:
            for event in sent.events:
                number_assigned_anchors += event.number_of_anchors()
                number_assigned_args += event.number_of_arguments()
                for anchor in event.anchors:
                    if len(anchor.tokens) > 1:
                        number_assigned_multiword_anchors += 1

    # print('In train_test.prepare_docs')
    # for doc in docs:
    #     for sent in doc.sentences:
    #         for event in sent.events:
    #             for arg in event.arguments:
    #                 if len(arg.entity_mention.tokens) > 1:
    #                     print('Multiword argument: {} {}'.format(arg.entity_mention.label, ' '.join(token.text for token in arg.entity_mention.tokens)))
    # exit(0)

    print('In %d documents, #anchors=%d #assigned_anchors=%d #assigned_multiword_anchors=%d, #args=%d #assigned_args=%d' % \
          (len(docs), number_anchors, number_assigned_anchors, number_assigned_multiword_anchors, number_args, number_assigned_args))
    return docs

def get_predicted_positive_triggers(predictions, examples, none_class_index, event_domain):
    """Collect the predicted positive triggers and organize them by docid
    Also, use the predicted event_type for each such trigger example

    :type predictions: numpy.nparray
    :type examples: list[event.event_trigger.EventTriggerExample]
    :type event_domain: event.event_domain.EventDomain
    """
    assert len(predictions)==len(examples)
    ret = defaultdict(list)

    pred_arg_max = np.argmax(predictions, axis=1)
    for i, index in enumerate(pred_arg_max):
        if index != none_class_index:
            eg = examples[i]
            """:type: event.event_trigger.EventTriggerExample"""
            eg.event_type = event_domain.get_event_type_from_index(index)
            ret[eg.sentence.docid].append(eg)
    return ret

def generate_trigger_data_feature(generator, docs):
    """
    :type generator: event.event_trigger.EventTriggerGenerator
    :type docs: list[text.text_theory.Document]
    """
    examples = generator.generate(docs)
    data = generator.examples_to_data_dict(examples)
    data_list = [np.asarray(data['word_vec']), np.asarray(data['pos_array'])]
    label = np.asarray(data['label'])

    print('#examples=%d' % (len(examples)))
    print('data word_vec.len=%d pos_array.len=%d label.len=%d' % (
        len(data['word_vec']), len(data['pos_array']), len(data['label'])))
    return (examples, data, data_list, label)

def trigger_modeling(params, train_docs, test_docs, event_domain, word_embeddings):
    """
    :type params: common.parameters.Parameters
    :type train_docs: list[text.text_theory.Document]
    :type test_docs: list[text.text_theory.Document]
    :type event_domain: event.event_domain.EventDomain
    :type word_embeddings: embeddings.word_embeddings.WordEmbedding
    """
    generator = EventTriggerGenerator(event_domain, params)

    (train_examples, train_data, train_data_list, train_label) = generate_trigger_data_feature(generator, train_docs)

    # train_examples = generator.generate(train_docs)
    # train_data = generator.examples_to_data_dict(train_examples)
    # train_data_list = [np.asarray(train_data['word_vec']), np.asarray(train_data['pos_array'])]
    # train_label = np.asarray(train_data['label'])
    #
    # print('#train_examples=%d' % (len(train_examples)))
    # print('train_data word_vec.len=%d pos_array.len=%d label.len=%d' % (
    #     len(train_data['word_vec']), len(train_data['pos_array']), len(train_data['label'])))

    (test_examples, test_data, test_data_list, test_label) = generate_trigger_data_feature(generator, test_docs)

    # test_examples = generator.generate(test_docs)
    # test_data = generator.examples_to_data_dict(test_examples)
    # test_data_list = [np.asarray(test_data['word_vec']), np.asarray(test_data['pos_array'])]
    # test_label = np.asarray(test_data['label'])
    #
    # print('#test_examples=%d' % (len(test_examples)))
    # print('test_data word_vec.len=%d pos_array.len=%d label.len=%d' % (
    #     len(test_data['word_vec']), len(test_data['pos_array']), len(test_data['label'])))

    trigger_model = MaxPoolEmbeddedTriggerModel(params, event_domain, word_embeddings)
    trigger_model.fit(train_data_list, train_label, test_data_list, test_label)

    predictions = trigger_model.predict(test_data_list)
    predicted_positive_triggers = get_predicted_positive_triggers(predictions, test_examples, event_domain.get_event_type_index('None'), event_domain)

    # calculate the recall denominator
    number_test_anchors = 0
    for doc in test_docs:
        for event in doc.events:
            number_test_anchors += event.number_of_anchors()

    score = evaluate_f1(predictions, test_label, event_domain.get_event_type_index('None'), num_true=number_test_anchors)
    print(score.to_string())

    output_dir = params.get_string('output_dir')
    with open(os.path.join(output_dir, 'train_trigger.score'), 'w') as f:
        f.write(score.to_string() + '\n')

    print('==== Saving Trigger model ====')
    trigger_model.keras_model.save(os.path.join(output_dir, 'trigger.hdf'))
    with open(os.path.join(output_dir, 'trigger.pickle'), u'wb') as f:
        pickle.dump(trigger_model, f)

    return predicted_positive_triggers


def train_trigger(params, word_embeddings, event_domain):
    """
    :type params: common.parameters.Parameters
    :type word_embeddings: embeddings.word_embeddings.WordEmbedding
    :type event_domain: event.event_domain.EventDomain
    """
    train_docs = prepare_docs(params.get_string('filelist.train'))
    test_docs = prepare_docs(params.get_string('filelist.dev'))

    predicted_positive_triggers = trigger_modeling(params, train_docs, test_docs, event_domain, word_embeddings)
    #argument_modeling(params, train_docs, test_docs, event_domain, word_embeddings, predicted_positive_triggers)

def load_trigger_model(model_dir):
    with open(os.path.join(model_dir, 'trigger.pickle'), u'rb') as f:
        trigger_model = pickle.load(f)
        """:type: model.event_cnn.EventExtractionModel"""
        trigger_model.load_keras_model(filename=os.path.join(model_dir, 'trigger.hdf'))
        return trigger_model

def load_argument_model(model_dir):
    with open(os.path.join(model_dir, 'argument.pickle'), u'rb') as f:
        argument_model = pickle.load(f)
        """:type: model.event_cnn.EventExtractionModel"""
        argument_model.load_keras_model(filename=os.path.join(model_dir, 'argument.hdf'))
        return argument_model

def test_trigger(params, event_domain):
    """
    :type params: common.parameters.Parameters
    :type event_domain: event.event_domain.EventDomain
    """
    generator = EventTriggerGenerator(event_domain, params)
    test_docs = prepare_docs(params.get_string('filelist.test'))

    (test_examples, test_data, test_data_list, test_label) = generate_trigger_data_feature(generator, test_docs)

    # test_examples = generator.generate(test_docs)
    # test_data = generator.examples_to_data_dict(test_examples)
    # test_data_list = [np.asarray(test_data['word_vec']), np.asarray(test_data['pos_array'])]
    # test_label = np.asarray(test_data['label'])
    #
    # print('#test_examples=%d' % (len(test_examples)))
    # print('test_data word_vec.len=%d pos_array.len=%d label.len=%d' % (
    #     len(test_data['word_vec']), len(test_data['pos_array']), len(test_data['label'])))

    print('==== Loading Trigger model ====')
    output_dir = params.get_string('output_dir')
    trigger_model = load_trigger_model(output_dir)

    predictions = trigger_model.predict(test_data_list)
    predicted_positive_triggers = get_predicted_positive_triggers(predictions, test_examples,
                                                                  event_domain.get_event_type_index('None'),
                                                                  event_domain)

    score = evaluate_f1(predictions, test_label, event_domain.get_event_type_index('None'))
    print(score.to_string())

    with open(os.path.join(output_dir, 'test_trigger.score'), 'w') as f:
        f.write(score.to_string() + '\n')
    return predicted_positive_triggers


def generate_argument_data_feature(generator, docs, predicted_triggers=None):
    """
    :type generator: event.event_trigger.EventArgumentGenerator
    :type docs: list[text.text_theory.Document]
    """
    examples = generator.generate(docs, triggers=predicted_triggers)
    data = generator.examples_to_data_dict(examples)
    data_list = [np.asarray(data['word_vec']), np.asarray(data['pos_array']), np.asarray(data['event_array'])]
    label = np.asarray(data['label'])

    print('#examples=%d' % (len(examples)))
    print('data word_vec.len=%d pos_array.len=%d event_array.len=%d label.len=%d' % (
        len(data['word_vec']), len(data['pos_array']), len(data['event_array']), len(data['label'])))
    return (examples, data, data_list, label)

def argument_modeling(params, train_docs, test_docs, event_domain, word_embeddings):
    """
    :type params: common.parameters.Parameters
    :type train_docs: list[text.text_theory.Document]
    :type test_docs: list[text.text_theory.Document]
    :type event_domain: event.event_domain.EventDomain
    :type word_embeddings: embeddings.word_embeddings.WordEmbedding
    #:type predicted_positive_triggers: list[event.event_trigger.EventTriggerExample]
    """
    generator = EventArgumentGenerator(event_domain, params)

    (train_examples, train_data, train_data_list, train_label) = generate_argument_data_feature(generator, train_docs)

    # train_examples = generator.generate(train_docs)
    # train_data = generator.examples_to_data_dict(train_examples)
    # train_data_list = [np.asarray(train_data['word_vec']), np.asarray(train_data['pos_array']), np.asarray(train_data['event_array'])]
    # train_label = np.asarray(train_data['label'])
    #
    # print('#train_examples=%d' % (len(train_examples)))
    # print('train_data word_vec.len=%d pos_array.len=%d event_array.len=%d label.len=%d' % (
    #     len(train_data['word_vec']), len(train_data['pos_array']), len(train_data['event_array']),
    #     len(train_data['label'])))

    (test_examples, test_data, test_data_list, test_label) = generate_argument_data_feature(generator, test_docs)

    # test_examples: list[event.event_argument.EventArgumentExample]

    # test_examples = generator.generate(test_docs)
    # test_data = generator.examples_to_data_dict(test_examples)
    # test_data_list = [np.asarray(test_data['word_vec']), np.asarray(test_data['pos_array']), np.asarray(test_data['event_array'])]
    # test_label = np.asarray(test_data['label'])
    #
    # print('#test_examples=%d' % (len(test_examples)))
    # print('test_data word_vec.len=%d pos_array.len=%d event_array.len=%d label.len=%d' % (
    #     len(test_data['word_vec']), len(test_data['pos_array']), len(test_data['event_array']),
    #     len(test_data['label'])))

    # using predicted triggers to generate arg examples
    # test_examples_pt = generator.generate(test_docs, predicted_positive_triggers)
    # test_data_pt = generator.examples_to_data_dict(test_examples_pt)
    # test_data_list_pt = [np.asarray(test_data_pt['word_vec']), np.asarray(test_data_pt['pos_array']),
    #                   np.asarray(test_data_pt['event_array'])]
    # test_label_pt = np.asarray(test_data_pt['label'])

    argument_model = MaxPoolEmbeddedRoleModel(params, event_domain, word_embeddings)
    argument_model.fit(train_data_list, train_label, test_data_list, test_label)

    # TODO this is probably stricter than the ACE way of scoring, which just requires that there's an entity-mention of same offsets with same role

    predictions = argument_model.predict(test_data_list)

    # calculate the recall denominator
    number_test_args = 0
    for doc in test_docs:
        for event in doc.events:
            number_test_args += event.number_of_arguments()

    #score = evaluate_f1(predictions, test_label, event_domain.get_event_role_index('None'), num_true=number_test_args)
    #print('Arg-score1: ' + score.to_string())

    score = evaluate_arg_f1(event_domain, test_label, test_examples, predictions)
    print('Arg-score: ' + score.to_string())


    # predictions_pt = argument_model.predict(test_data_list_pt)
    # print('==== Calculate F1 for arg (using predicted triggers) ====')
    # # TODO we need to get the recall denominator correct
    # evaluate_f1(predictions_pt, test_label_pt, event_domain.get_event_role_index('None'))

    output_dir = params.get_string('output_dir')
    with open(os.path.join(output_dir, 'train_argument.score'), 'w') as f:
        f.write(score.to_string() + '\n')

    print('==== Saving Argument model ====')
    argument_model.keras_model.save(os.path.join(output_dir, 'argument.hdf'))
    with open(os.path.join(output_dir, 'argument.pickle'), u'wb') as f:
        pickle.dump(argument_model, f)

    # print('==== Loading model ====')
    # with open('role.try.pickle', u'rb') as f:
    #     model = pickle.load(f)
    #     """:type: model.cnn.EventExtractionModel"""
    #     model.load_keras_model(filename='role.try.hdf')
    #     predictions = model.predict(test_data_list)
    #     print('==== Model loading, calculating F1 ====')
    #     evaluate_f1(predictions, test_label, event_domain.get_event_role_index('None'))

def train_argument(params, word_embeddings, event_domain):
    """
    :type params: common.parameters.Parameters
    :type word_embeddings: embeddings.word_embeddings.WordEmbedding
    :type event_domain: event.event_domain.EventDomain
    """
    train_docs = prepare_docs(params.get_string('filelist.train'))
    test_docs = prepare_docs(params.get_string('filelist.dev'))

    #predicted_positive_triggers = trigger_modeling(params, train_docs, test_docs, event_domain, word_embeddings)
    argument_modeling(params, train_docs, test_docs, event_domain, word_embeddings)


def test_argument(params, event_domain):
    """
    :type params: common.parameters.Parameters
    :type event_domain: event.event_domain.EventDomain
    """
    arg_generator = EventArgumentGenerator(event_domain, params)
    trigger_generator = EventTriggerGenerator(event_domain, params)

    test_docs = prepare_docs(params.get_string('filelist.test'))

    (trigger_examples, trigger_data, trigger_data_list, trigger_label) = generate_trigger_data_feature(trigger_generator, test_docs)
    (arg_examples, arg_data, arg_data_list, arg_label) = generate_argument_data_feature(arg_generator, test_docs)

    # test_examples = generator.generate(test_docs)
    # test_data = generator.examples_to_data_dict(test_examples)
    # test_data_list = [np.asarray(test_data['word_vec']), np.asarray(test_data['pos_array']),
    #                   np.asarray(test_data['event_array'])]
    # test_label = np.asarray(test_data['label'])
    #
    # print('#test_examples=%d' % (len(test_examples)))
    # print('test_data word_vec.len=%d pos_array.len=%d event_array.len=%d label.len=%d' % (
    #     len(test_data['word_vec']), len(test_data['pos_array']), len(test_data['event_array']),
    #     len(test_data['label'])))

    output_dir = params.get_string('output_dir')

    print('==== Loading Trigger model ====')
    trigger_model = load_trigger_model(output_dir)
    trigger_predictions = trigger_model.predict(trigger_data_list)
    predicted_positive_triggers = get_predicted_positive_triggers(trigger_predictions, trigger_examples,
                                                                  event_domain.get_event_type_index('None'),
                                                                  event_domain)

    print('==== Loading Argument model ====')
    argument_model = load_argument_model(output_dir)
    argument_predictions = argument_model.predict(arg_data_list)

    score_with_gold_triggers = evaluate_arg_f1(event_domain, arg_label, arg_examples, argument_predictions)
    #score_with_gold_triggers = evaluate_f1(argument_predictions, arg_label, event_domain.get_event_role_index('None'))
    print('Arg-scores with gold-triggers: {}'.format(score_with_gold_triggers.to_string()))

    # generate arguments with predicted triggers
    (arg_examples_pt, arg_data_pt, arg_data_list_pt, arg_label_pt) = \
        generate_argument_data_feature(arg_generator, test_docs, predicted_triggers=predicted_positive_triggers)

    # decode arguments with predicted triggers
    argument_predictions_pt = argument_model.predict(arg_data_list_pt)

    # evaluate arguments with predicted triggers
    score_with_predicted_triggers = evaluate_arg_f1(event_domain, arg_label_pt, arg_examples_pt, argument_predictions_pt)
    score_with_predicted_triggers.num_true = score_with_gold_triggers.num_true
    #score_with_predicted_triggers = evaluate_f1(argument_predictions_pt, arg_label_pt,
    #                                            event_domain.get_event_role_index('None'),
    #                                            num_true=score_with_gold_triggers.num_true)
    print('Arg-scores with predicted-triggers: {}'.format(score_with_predicted_triggers.to_string()))

    with open(os.path.join(output_dir, 'test_argument.score'), 'w') as f:
        f.write('With-gold-triggers: {}\n'.format(score_with_gold_triggers.to_string()))
        f.write('With-predicted-triggers: {}\n'.format(score_with_predicted_triggers.to_string()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode')   # train_trigger, train_arg, test_trigger, test_arg
    parser.add_argument('--params')
    args = parser.parse_args()

    params = Parameters(args.params)
    params.print_params()

    # load word embeddings
    word_embeddings = WordEmbedding(params)

    event_domain = None
    # initialize a particular event domain, which stores info on the event types and event roles
    if params.get_string('domain') == 'cyber':
        event_domain = CyberDomain()
    elif params.get_string('domain') == 'ace':
        event_domain = AceDomain()

    if args.mode == 'train_trigger':
        train_trigger(params, word_embeddings, event_domain)
    elif args.mode == 'train_argument':
        train_argument(params, word_embeddings, event_domain)
    elif args.mode == 'test_trigger':
        test_trigger(params, event_domain)
    elif args.mode == 'test_argument':
        test_argument(params, event_domain)


