
import os
import sys
import zipfile
#from pyspark import SparkContext, SparkConf
#from ctypes import *

import twokenize
import spacy
from cyberlingo.text.text_theory import Document
from cyberlingo.text.text_span import EntityMention
from cyberlingo.common.utils import IntPair

from cyberlingo.event.train_test import generate_trigger_data_feature

global spacy_en
global tagger_blog
global tagger_tweet
global tagger_news
global tagger_dw

#sys.path.append('/nfs/mercury-04/u40/ychan/spark/ner/crfsuite')
#sc.addPyFile('/nfs/mercury-04/u40/ychan/spark/ner/crfsuite/crfsuite.py')
#cdll.LoadLibrary('/nfs/mercury-04/u40/ychan/spark/ner/crfsuite/libcrfsuite-0.12.so')
#import crfsuite

class Token(object):
    """An individual word token.

    """

    # idx : starting char offset
    def __init__(self, text, idx, pos_tag=None):
        self.text = text
        self.idx = idx
        self.tag_ = pos_tag


class Decoder(object):
    #sys.path.append('/nfs/mercury-04/u40/ychan/spark/ner/crfsuite')
    #cdll.LoadLibrary('/nfs/mercury-04/u40/ychan/spark/ner/crfsuite/libcrfsuite-0.12.so')
    #import crfsuite


    # python_path: /nfs/mercury-04/u40/ychan/spark/ner/crfsuite
    # libcrfsuite_so: /nfs/mercury-04/u40/ychan/spark/ner/crfsuite/libcrfsuite-0.12.so
    # model_file: /nfs/mercury-04/u40/ychan/ner/model/twitter.cv1.model
    def __init__(self, params):
        #sys.path.append(python_path)
        #for library in libcrfsuite_so_libs:
        #    cdll.LoadLibrary(library)
        #import crfsuite as crfsuite
        #self.crfsuite = crfsuite
        import pycrfsuite as pycrfsuite
        self.pycrfsuite = pycrfsuite
        self.model_blog = params.get_string('model.blog')
        self.model_tweet = params.get_string('model.tweet')
        self.model_news = params.get_string('model.news')
        self.model_dw = params.get_string('model.dw')

        if params.get_string('resources.zip') is not None:
            if os.path.isfile(params.get_string('resources.zip')) and not os.path.isdir(params.get_string('model.dir')):
                zip_ref = zipfile.ZipFile(params.get_string('resources.zip'), 'r')
                zip_ref.extractall()
                zip_ref.close()

    def instances(self, fi):
        xseq = []
 
        for line in fi:
            fields = line.split('\t')
            item = {}
            for field in fields[1:]:
                sfield = field.encode('ascii','replace')
                p = sfield.rfind(':')
                if p == -1:
                    # Unweighted (weight=1) attribute.
                    item[sfield] = 1.0
                elif (p+1) >= len(sfield):
                    item[sfield] = 1.0
                else:
                    try:
                        weight = float(sfield[p+1:])
                        item[sfield[:p]] = weight
                    except ValueError:
                        item[sfield] = 1.0
            xseq.append(item)

        return self.pycrfsuite.ItemSequence(xseq)

    #def instances(self, fi):
    #    xseq = self.crfsuite.ItemSequence()
    # 
    #    for line in fi:
    #        # Split the line with TAB characters.
    #        fields = line.split('\t')
    #        item = self.crfsuite.Item()
    #        for field in fields[1:]:
    #            #print('field %s' % (field))
    #            sfield = field.encode('ascii','replace')
    #            #print('sfield %s' % (sfield))
    #            p = sfield.rfind(':')
    #            if p == -1:
    #                # Unweighted (weight=1) attribute.
    #                #print('field:{} type(field):{}'.format(field, type(field)))
    #                #print(type(field))
    #                #field_string = field.encode('ascii','replace')
    #                #item.append(self.crfsuite.Attribute(field_string))
    #                item.append(self.crfsuite.Attribute(sfield))
    #            elif (p+1) >= len(sfield):
    #                item.append(self.crfsuite.Attribute(sfield))
    #            else:
    #                try:
    #                    weight = float(sfield[p+1:])
    #                    item.append(self.crfsuite.Attribute(sfield[:p], weight))
    #                except ValueError:
    #                    item.append(self.crfsuite.Attribute(sfield))
    #                #print field
    #                # Weighted attribute
    #                #item.append(self.crfsuite.Attribute(sfield[:p], float(sfield[p+1:])))
    #        # Append the item to the item sequence.
    #        xseq.append(item)
    #
    #    return xseq

    # Blog , Conference , SocialMediaPosting
    def get_content_tagger(self, xseq, content_type):
        global tagger_blog
        global tagger_tweet
        global tagger_news
        global tagger_dw

        if content_type == 'Blog':
            try:
                tagger_blog.set(xseq)
            except:
                tagger_blog = self.pycrfsuite.Tagger()
                tagger_blog.open(self.model_blog)
                print('**** Loaded blog NER model %s' % (self.model_blog))
                tagger_blog.set(xseq)
            return tagger_blog
        elif content_type == 'SocialMediaPosting':
            try:
                tagger_tweet.set(xseq)
            except:
                tagger_tweet = self.pycrfsuite.Tagger()
                tagger_tweet.open(self.model_tweet)
                print('**** Loaded tweet NER model %s' % (self.model_tweet))
                tagger_tweet.set(xseq)
            return tagger_tweet
        elif content_type == 'NewsArticle':
            try:
                tagger_news.set(xseq)
            except:
                tagger_news = self.pycrfsuite.Tagger()
                tagger_news.open(self.model_news)
                print('**** Loaded news NER model %s' % (self.model_news))
                tagger_news.set(xseq)
            return tagger_news
        elif content_type == 'Post':
            try:
                tagger_dw.set(xseq)
            except:
                tagger_dw = self.pycrfsuite.Tagger()
                tagger_dw.open(self.model_dw)
                print('**** Loaded dw NER model %s' % (self.model_dw))
                tagger_dw.set(xseq)
            return tagger_dw

    def tag_seq(self, xseq, content_type):
        tagger = self.get_content_tagger(xseq, content_type)
        return tagger.tag()


def collect_predictions(content, predictions, char_offsets):
    ret = []

    i = 0
    while i < len(predictions):
        p = predictions[i]
        if p.startswith('B-'):
            label = p[2:]
            (start, end) = char_offsets[i]
            while (i+1) < len(predictions) and predictions[i+1] == 'I-'+label:
                i += 1
            end = char_offsets[i][1]

            # these are when we mix in ACE and Blog annotations. ACE tags 'ORG', Blog tags 'ORGANIZATION'
            if label == 'ORG':
                label = 'ORGANIZATION'
            if label == 'PER':
                label = 'PERSON'

            d = {}
            d['start'] = start
            d['end'] = end
            d['label'] = label
            d['text'] = content[start:end]
            d['extractor'] = 'cyberlingo'
            ret.append(d)
        i += 1

    return ret


# A line could be a paragraph consisting of multiple sentences. 
# We will get the correct definition of sentences according to whether this is blog, tweet, etc.
def get_sentences(line, content_type):
    global spacy_en

    if content_type == 'SocialMediaPosting':
        sentences = []
        start_offset = 0
        sent = []

        for token in twokenize.tokenize(line[:-1]):
            idx = line.index(token, start_offset)
            sent.append(Token(token, idx))
            start_offset = idx + len(token)

        sentences.append(sent)
        return sentences
        
    elif content_type == 'Blog' or content_type == 'NewsArticle' or content_type == 'Post':
        try:
            spacy_doc = spacy_en(line)
        except:
            spacy_en = spacy.load('en')
            print('**** Loaded spacy en')
            spacy_doc = spacy_en(line)

        return spacy_doc.sents

def decode_sentence(ner_fea, dec, content, sent, offset, content_type):
    """
    :type ner_fea: ner.ner_feature.NerFeature
    :type dec: ner.decoder.Decoder
    :type content: str
    :type offset: int
    :type content_type: str
    sent: spacy sentence
    Returns:
        list[dict()]

    content_type: 'Blog' , 'SocialMediaPosting' , 'NewsArticle' (will decide which NER feature set to use)
    """
    tokens = [t for t in sent if len(t.text) > 0]

    # a list, 1 element for each word in line
    # each element is a tab separate features, except the 1st element which is a dummy label
    word_feas = line_to_features(ner_fea, tokens, content_type) # content_type decides which NER feature set to use
    word_seq = dec.instances(word_feas)                 # of type pycrfsuite.ItemSequence
    predictions = dec.tag_seq(word_seq, content_type)   # content_type decides which NER model to load

    char_offsets = []
    for token in tokens:
        start = token.idx + offset
        end = start + len(token.text)
        char_offsets.append((start, end))

    assert (len(char_offsets) == len(predictions)), 'len(char_offsets) should match len(predictions)'

    # returns a dict with keys: start, end, label, text, extractor
    return collect_predictions(content, predictions, char_offsets)

def find(element, json):
    x = reduce(lambda d, key: d.get(key, {}), element.split("."), json)
    if any(x) is True:
        return x
    return None

# line : a json string
def line_to_predictions(ner_fea, dec, json_eg, attr, content_type, word_embeddings, trigger_generator, trigger_model, arg_generator):
    """
    :type word_embeddings: embeddings.word_embeddings.WordEmbedding
    :type trigger_generator: event.event_trigger.EventTriggerGenerator
    :type trigger_model: model.event_cnn.EventExtractionModel
    :type arg_generator: event.event_argument.EventArgumentGenerator
    """
    global spacy_en

    content = find(attr, json_eg)  # json_eg.get(attr)

    #print(content_type.encode('ascii', 'ignore'))
    #print(content.encode('ascii', 'ignore'))

    offset = 0
    all_predictions = []

    if content is not None:
        if type(content) is list:
            content = '\n'.join(content)
        for line in content.split('\n'):
            #print(offset)
            #print('[' + content_type.encode('ascii', 'ignore') + ']')
            #print('[' + line.encode('ascii', 'ignore') + ']')

            doc_ner_predictions = []
            sentences = get_sentences(line, content_type)
            if sentences is not None:
                for sent in sentences:
                    sent_predictions = decode_sentence(ner_fea, dec, content, sent, offset, content_type)
                    doc_ner_predictions.extend(sent_predictions)
                    all_predictions.extend(sent_predictions)

            if content_type == 'Post':
                doc = Document('dummy', line)
                for i, p in enumerate(doc_ner_predictions):
                    id = 'em-{}'.format(i)
                    doc.add_entity_mention(EntityMention(id, IntPair(p['start'], p['end']), p['text'], p['label']))
                doc.annotate_sentences(spacy_en, word_embeddings)

                (trigger_examples, trigger_data, trigger_data_list, trigger_label) = generate_trigger_data_feature(trigger_generator, [doc])
                trigger_predictions = trigger_model.predict(trigger_data_list)


            offset += len(line) + 1 # +1 to account for newline

    # a list of dict, one for each predicted NE mention
    if len(all_predictions) > 0:
        if not "extractions" in json_eg:
            json_eg["extractions"] = {}
        json_eg['extractions'][attr] = all_predictions

    return json_eg


# for each word in sent, return: label \tab (\tab separated list of features). If a feature is weighted, it will be like (.*):weight
def line_to_features(ner_fea, sent, content_type):
    d = ('', '', '')
    seq = [d, d]

    for token in sent:
        #start = token.idx
        #print(token.text.encode('ascii', 'ignore'))
        pos_tag = 'NN' if token.tag_ is None else token.tag_
        seq.append((ner_fea.encode(token.text), pos_tag, 'DUMMY-tag'))

    seq.append(d)
    seq.append(d)

    return ner_fea.extract_features(seq, content_type)

