from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import argparse
import codecs
import spacy

import pickle

from collections import defaultdict

import numpy as np

from cyberlingo.text.text_span import EntityMention
from cyberlingo.text.text_span import EventArgument
from cyberlingo.text.text_theory import Document
from cyberlingo.annotation.idt import process_idt_file
from cyberlingo.annotation.enote import process_enote_file
from cyberlingo.embeddings.word_embeddings import WordEmbedding
from cyberlingo.event.event_trigger import EventTriggerGenerator
from cyberlingo.event.event_argument import EventArgumentGenerator
from cyberlingo.event.event_domain import CyberDomain
import cyberlingo.common.utils as text_utils
from cyberlingo.common.parameters import Parameters
from cyberlingo.common.utils import IntPair

from cyberlingo.model.event_cnn import MaxPoolEmbeddedTriggerModel
from cyberlingo.model.event_cnn import MaxPoolEmbeddedRoleModel
from cyberlingo.model.event_cnn import evaluate_f1

from cyberlingo.event.train_test import generate_trigger_data_feature
from cyberlingo.event.train_test import generate_argument_data_feature
from cyberlingo.event.train_test import load_trigger_model
from cyberlingo.event.train_test import load_argument_model
from cyberlingo.event.train_test import get_predicted_positive_triggers

from cyberlingo.ner.ner_feature import NerFeature
from cyberlingo.ner.decoder import Decoder
from cyberlingo.ner.decoder import decode_sentence

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--params')
    parser.add_argument('--textfile')

    args = parser.parse_args()

    params = Parameters(args.params)
    params.print_params()

    # load word embeddings
    word_embeddings = WordEmbedding(params)



    with codecs.open(args.textfile, 'r', encoding='utf-8') as f:
        content = f.read()

    ner_fea = NerFeature(params)
    ner_decoder = Decoder(params)

    spacy_en = spacy.load('en')
    spacy_doc = spacy_en(content)

    ner_predictions = []
    for sent in spacy_doc.sents:
        ner_predictions.extend(decode_sentence(ner_fea, ner_decoder, content, sent, offset=0, content_type='Blog'))

    for p in ner_predictions:
        print(p)

    # create a document based on text content, add NER predictions as EntityMentions, then apply Spacy to
    # perform sentence segmentation and tokenization, and use Spacy tokens to back the EntityMentions
    doc = Document('dummy', content)
    for i, p in enumerate(ner_predictions):
        id = 'em-{}'.format(i)
        doc.add_entity_mention(EntityMention(id, IntPair(p['start'], p['end']), p['text'], p['label']))
    doc.annotate_sentences(spacy_en, word_embeddings)

    event_domain = None
    if params.get_string('domain') == 'cyber':
        # initialize a particular event domain, which stores info on the event types and event roles
        event_domain = CyberDomain()

    arg_generator = EventArgumentGenerator(event_domain, params)
    trigger_generator = EventTriggerGenerator(event_domain, params)

    (trigger_examples, trigger_data, trigger_data_list, trigger_label) = generate_trigger_data_feature(trigger_generator, [doc])

    print('==== Loading Trigger model ====')
    trigger_model = load_trigger_model(params.get_string('event_model_dir'))
    trigger_predictions = trigger_model.predict(trigger_data_list)
    predicted_positive_triggers = get_predicted_positive_triggers(trigger_predictions, trigger_examples,
                                                                  event_domain.get_event_type_index('None'),
                                                                  event_domain)

    # generate arguments with predicted triggers
    (arg_examples_pt, arg_data_pt, arg_data_list_pt, arg_label_pt) = \
        generate_argument_data_feature(arg_generator, [doc], predicted_triggers=predicted_positive_triggers)

    print('==== Loading Argument model ====')
    argument_model = load_argument_model(params.get_string('event_model_dir'))

    # decode arguments with predicted triggers
    argument_predictions_pt = argument_model.predict(arg_data_list_pt)
    pred_arg_max = np.argmax(argument_predictions_pt, axis=1)

    predicted_events = defaultdict(list)    # to collate by anchor
    for i, predicted_label in enumerate(pred_arg_max):
        if predicted_label != event_domain.get_event_role_index('None'):
            eg = arg_examples_pt[i]
            """:type: event.event_argument.EventArgumentExample"""
            predicted_role = event_domain.get_event_role_from_index(predicted_label)
            #print('{} || {} || {}'.format(predicted_role, eg.anchor.to_string(), eg.argument.to_string()))
            predicted_events[eg.anchor].append(EventArgument('dummy', eg.argument, predicted_role))

    for sent in doc.sentences:
        """:type: text.text_span.Sentence"""
        sent_start = sent.start_char_offset()
        sent_end = sent.end_char_offset()
        print(sent.text)
        for anchor in predicted_events.keys():
            """:type: text.text_span.Anchor"""
            if sent_start<=anchor.start_char_offset() and anchor.end_char_offset()<=sent_end:
                print(anchor.to_string())
                for arg in predicted_events[anchor]:
                    """:type: text.text_span.EventArgument"""
                    print('- {}'.format(arg.to_string()))

