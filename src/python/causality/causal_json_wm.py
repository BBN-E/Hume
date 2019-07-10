"""
Extracts KBP events, ACCENT events, or generic triggers that occurs within the Arg1, Arg2 of PDTB causal relations.
Then adds these 'causal factors' annotations to the (Serif) JSON files that we produce and send to Regina.
This script also outputs log files, e.g. the top most frequent causal factors, so that we can eyeball to see which ones make sense.
"""

import os
import sys
import json
import argparse
import codecs
import glob
import re

from collections import defaultdict
from json_encoder import ComplexEncoder

from cyberlingo.common.utils import Struct
from cyberlingo.common.utils import IntPair
from cyberlingo.text.text_span import TextSpan
from cyberlingo.text.text_span import EventSpan

#from common.cluster import read_cluster_file
#from common.cluster import get_highest_scoring_cluster


event_models = Struct(KBP='KBP', ACCENT='ACCENT', GENERIC='GENERIC')



class Document(object):
    def __init__(self, docid):
        self.docid = docid
        self.relations = []
        """:type: Relation"""
        self.events = []
        """:type: Event"""
        self.causal_relations = []
        """:type CausalRelation"""

    def add_relation(self, relation):
        self.relations.append(relation)

    def add_relations(self, relations):
        self.relations.extend(relations)

    def add_event(self, event):
        self.events.append(event)

    def add_events(self, events):
        self.events.extend(events)

    def add_causal_relation(self, relation):
        self.causal_relations.append(relation)

    def to_string(self):
        ret = []
        ret.append('==== %s ====' % (self.docid))
        for relation in self.relations:
            ret.append('RELATION: %s' % (relation.to_string()))
        for event in self.events:
            ret.append('EVENT: %s' % (event.to_string()))
        return '\n'.join(ret)


class Relation(object):
    def __init__(self, label):
        self.label = label
        self.connective_text = None
        self.docid = None
        self.relation_type = None
        self.arg1_spans = []
        self.arg2_spans = []
        self.arg1_text = None
        self.arg2_text = None

    def add_arg1_span(self, span):
        """:type span: IntPair"""
        self.arg1_spans.append(span)

    def add_arg2_span(self, span):
        """:type span: IntPair"""
        self.arg2_spans.append(span)

    def to_string(self):
        return ('%s ARG1:%s ARG2:%s' % (self.label, ','.join(span.to_string() for span in self.arg1_spans), ','.join(span.to_string() for span in self.arg2_spans)))


class CausalRelation(object):
    def __init__(self, label):
        self.label = label
        self.left_factor = None
        """:type: Event"""
        self.right_factor = None
        """:type: Event"""
        self.left_text = None
        self.right_text = None

    def to_string(self):
        return ('{}\t{}\t{}\t{}'.format(self.left_factor.span.label, self.label, self.right_factor.span.label, self.left_factor.model))


class Event(object):
    def __init__(self, span):
        """:type span: cyberlingo.text.text_span.EventSpan"""
        self.span = span
        self.model = None	# one of the event_models
        self.snippet = None
 
    def to_string(self):
        return ('%s %s' % (self.model, self.span.to_string()))

def find_events_in_doc_relations(doc):
    """
    :type doc: Document
    """
    outlines = []

    kbp_events = []
    for event in doc.events:
        if event.model == event_models.KBP:
            kbp_events.append(event)

    accent_events = []
    for event in doc.events:
        if event.model == event_models.ACCENT:
            accent_events.append(event)

    generic_events = []
    for event in doc.events:
        if event.model == event_models.GENERIC:
            generic_events.append(event)

    #kbp_events = [event in doc.events if event.model is event_models.KBP]
    #accent_events = [event in doc.events if event.model == event_models.ACCENT]
    #generic_events = [event in doc.events if event.model == event_models.GENERIC]

    for relation in doc.relations:
        has_kbp = False
        has_accent = False

        arg1_events = []
        arg2_events = []

        #print('Examining relation {}'.format(relation.to_string()))

        (arg1_kbp_events, arg2_kbp_events) = find_events_in_relation_args(relation, kbp_events)
        if len(arg1_kbp_events) == 1 and len(arg2_kbp_events) == 1:
            has_kbp = True
            arg1_events.extend(arg1_kbp_events)
            arg2_events.extend(arg2_kbp_events)
            #add_event_pairs_as_causal(arg1_kbp_events, arg2_kbp_events, relation, doc)
            #outlines.append('{}\t{}\t{}'.format(arg1_kbp_events[0].span.label, relation.label, arg2_kbp_events[0].span.label))
           
        (arg1_accent_events, arg2_accent_events) = find_events_in_relation_args(relation, accent_events)
        if len(arg1_accent_events) == 1 and len(arg2_accent_events) == 1:
            has_accent = True
            arg1_events.extend(arg1_accent_events)
            arg2_events.extend(arg2_accent_events)
            #add_event_pairs_as_causal(arg1_accent_events, arg2_accent_events, relation, doc)
            #outlines.append('{}\t{}\t{}'.format(arg1_accent_events[0].span.label, relation.label, arg2_accent_events[0].span.label))

        (arg1_generic_events, arg2_generic_events) = find_events_in_relation_args(relation, generic_events)
        if has_kbp is False and has_accent is False:
            if len(arg1_generic_events) == 1 and len(arg2_generic_events) == 1:
                arg1_events.extend(arg1_generic_events)
                arg2_events.extend(arg2_generic_events)
                #add_event_pairs_as_causal(arg1_generic_events, arg2_generic_events, relation, doc)
                #outlines.append('{}\t{}\t{}'.format(arg1_generic_events[0].span.label, relation.label, arg2_generic_events[0].span.label))

        #print(' - {},{} {},{} {},{}'.format(len(arg1_kbp_events), len(arg2_kbp_events), len(arg1_accent_events), len(arg2_accent_events), len(arg1_generic_events), len(arg2_generic_events)))

        if len(arg1_events) > 0 and len(arg2_events) > 0:
            #print(' -- adding {},{} pairs as {}'.format(len(arg1_events), len(arg2_events), relation.label))
            add_event_pairs_as_causal(arg1_events, arg2_events, relation, doc)

    return outlines


def add_event_pairs_as_causal(events1, events2, relation, doc):
    """
    events1 fall within arg1 of the PDTB relation
    events2 fall within arg2 of the PDTB relation
    :type events1: list[Event]
    :type events2: list[Event]
    :type doc: Document
    """
    for e1 in events1:
        start1 = e1.span.start_char_offset()
        for e2 in events2:
            start2 = e2.span.start_char_offset()

            r = CausalRelation(relation.label)
            if start1 <= start2:
                r.left_factor = e1
                r.left_text = relation.arg1_text    
                r.right_factor = e2
                r.right_text = relation.arg2_text
            else:
                r.left_factor = e2
                r.left_text = relation.arg2_text
                r.right_factor = e1
                r.right_text = relation.arg1_text

            doc.add_causal_relation(r)

        
def find_events_in_relation_args(relation, events):
    """
    :type relation: Relation
    :type events: list[Event]
    """
    arg1_events = []
    for offset in relation.arg1_spans:
        arg1_events.extend(find_events_in_span(offset, events))

    arg2_events = []
    for offset in relation.arg2_spans:
        arg2_events.extend(find_events_in_span(offset, events))

    return (arg1_events, arg2_events)


def find_events_in_span(offset, events):
    """
    :type offset: IntPair
    :type events: list[Event]
    """
    ret = []
    for e in events:
        e_start = e.span.start_char_offset()
        e_end = e.span.end_char_offset()
        if offset.first <= e_start and e_end <= offset.second:
            ret.append(e)
    return ret


def read_pdtb_json(filename):
    doc_relations = defaultdict(list)

    with codecs.open(filename, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    for eg in json_data:
        if eg is not None:
            arg1_spans = eg['arg1_span_list']
            arg1_text = eg['arg1_text']

            arg2_spans = eg['arg2_span_list']
            arg2_text = eg['arg2_text']

            semantic_class = eg['semantic_class']

            docid = eg['docid']
            docid = re.search(r'^(.*)\.(.*)$', docid).group(1)

            r = Relation(semantic_class)
            r.connective_text = eg['connective_text']
            r.docid = docid
            r.relation_type = eg['relation_type']

            for span in arg1_spans:
                offset = IntPair(int(span[0]), int(span[1]))
                r.add_arg1_span(offset)
            for span in arg2_spans:
                offset = IntPair(int(span[0]), int(span[1]))
                r.add_arg2_span(offset)

            r.arg1_text = arg1_text
            r.arg2_text = arg2_text

            doc_relations[r.docid].append(r)

    return doc_relations


def offset_from_offsets(offset1, offset2):
    if offset1 is not None and offset2 is not None:
        c1 = min(offset1.first, offset2.first)
        c2 = max(offset1.second, offset2.second)
        return IntPair(c1, c2)
    elif offset1 is not None:
        return offset1
    elif offset2 is not None:
        return offset2
    else:
        return None


def read_serif_json(filename):
    ret = []
    
    with codecs.open(filename, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    for event in json_data['events']:	# these are KBP and GENERIC events
        start = event['anchor_start']
        end = event['anchor_end']
        event_type = event['event_type']
        text = event['anchor_text']
        span = EventSpan('dummy', IntPair(start, end), text, event_type)
        e = Event(span)
        e.snippet = event['snippet']

        if event_type.startswith('Class-'):
            e.model = event_models.GENERIC
        else:
            e.model = event_models.KBP
        ret.append(e)

    for event in json_data['accent_events']:
        event_name = event['event_name']

        args = event['participants']
        source_offset = None
        target_offset = None
        if 'Source' in args:
            source = args['Source']
            source_offset = IntPair(source['head_start_char'], source['head_end_char'])
        if 'Target' in args:
            target = args['Target']
            target_offset = IntPair(target['head_start_char'], target['head_end_char'])
        event_offset = offset_from_offsets(source_offset, target_offset)

        span = EventSpan('dummpy', event_offset, 'dummy', event_name)
        e = Event(span)
        e.model = event_models.ACCENT
        e.snippet = event['snippet']
        #ret.append(e)

    return ret


def add_learnit_relations(filepath, docs):
    with codecs.open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.strip().split('\t')
            relation_name = tokens[0]
            docid = tokens[1]
            arg1_start = int(tokens[2])
            arg1_end = int(tokens[3])
            arg2_start = int(tokens[4])
            arg2_end = int(tokens[5])

            arg1_text = re.search(r'<SLOT0>(.*?)</SLOT0>', tokens[6]).group(1)
            arg2_text = re.search(r'<SLOT1>(.*?)</SLOT1>', tokens[6]).group(1)

            if relation_name == 'causes':
                relation_name = 'cause';
            elif relation_name == 'affects':
                relation_name = 'pecondition_of';
            elif relation_name == 'occurs_before':
                relation_name = 'occurs_before'

            r = Relation(relation_name)
            #r.connective_text = eg['connective_text']
            r.docid = docid
            #r.relation_type = eg['relation_type']

            r.add_arg1_span(IntPair(arg1_start, arg1_end))
            r.add_arg2_span(IntPair(arg2_start, arg2_end))
            r.arg1_text = arg1_text
            r.arg2_text = arg2_text
            docs[docid].append(r)


# PYTHONPATH=/nfs/raid87/u15/users/ychan/repos/CauseEx/util/python:/nfs/raid87/u15/users/ychan/repos/CauseEx/util/python/json_producer2 python /nfs/raid87/u15/users/ychan/repos/CauseEx/util/python/causality/causal_json_wm.py --pdtb_json /nfs/raid87/u15/WM/datasets/starter_dataset/text/pdtb-relations.json --serif_json /nfs/raid87/u15/users/ychan/wm/starter/json --out_serif_json /nfs/raid87/u15/users/ychan/wm/starter/json_with_causal --learnit_relation /nfs/raid87/u15/WM/deliverables/20180129_CAG/wm_starter.causal_relations.txt
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdtb_json')
    parser.add_argument('--serif_json')
    #parser.add_argument('--generic_trigger')
    #parser.add_argument('--outfile')
    #parser.add_argument('--cluster_file')
    parser.add_argument('--out_serif_json')
    #parser.add_argument('--stats_file')
    parser.add_argument('--learnit_relation')
    args = parser.parse_args()

    count = 0
    pdtb_docs = read_pdtb_json(args.pdtb_json)    # docs with pdtb relations
    for key in pdtb_docs:
        count += len(pdtb_docs[key])
    print('count = {}'.format(count))

    add_learnit_relations(args.learnit_relation, pdtb_docs)
    for key in pdtb_docs:
        count += len(pdtb_docs[key])
    print('count = {}'.format(count))

    serif_docs = defaultdict(list)
    for filename in glob.glob(args.serif_json+'/*/*.json'):
        docid = re.search(r'(.*)/(.*?)\.json', filename).group(2)
        serif_docs[docid].extend(read_serif_json(filename))  # read events from each serif-json
        if (len(serif_docs) % 500)==0:
            print('Reading Serif JSON {}'.format(len(serif_docs)))


    docs = dict()
    """:type: Document"""   
    for docid in serif_docs.keys():
        doc = Document(docid)
        doc.add_events(serif_docs[docid])
        if docid in pdtb_docs:
            relations = pdtb_docs[docid]
            doc.add_relations(relations)
        docs[docid] = doc

    count_stats = defaultdict(int)
    for docid, doc in docs.items():
        find_events_in_doc_relations(doc)
        outlines = [r.to_string() for r in doc.causal_relations]
        #for line in outlines:
        #    tokens = line.split('\t')
        #    e1 = tokens[0]
        #    e2 = tokens[2]
        #    relation_type = tokens[1]
        #    model_type = tokens[3]
        #    sorted_e = sorted([e1, e2])
        #    count_stats['{}\t{}\t{}\t{}'.format(model_type, relation_type, sorted_e[0], sorted_e[1])] += 1

    #f = codecs.open(args.outfile, 'w', encoding='utf-8')
    #for k,v in sorted(count_stats.iteritems(), key=lambda (k,v): v):
    #    f.write('{}\t{}\n'.format(v, k))
    #f.close()


    # append the Serif JSON with causal relations
    print('Writing out new Serif JSON files')
    counter = 0 
    outlog = []
    for filename in glob.glob(args.serif_json+'/*/*.json'):
        docid = re.search(r'(.*)/(.*?)\.json', filename).group(2)
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            json_data = json.load(f) 

        json_data.pop('accent_events', None)

        doc = docs[docid]
        if doc is not None:
            for relation in doc.causal_relations:
                e1 = relation.left_factor
                e2 = relation.right_factor

                a1 = e1.span.label
                a2 = e2.span.label

                f1 = dict() 
                f1['head_start_char'] = e1.span.start_char_offset()
                f1['head_end_char'] = e1.span.end_char_offset()
                f1['mention_text'] = e1.span.text
                f1['event_type'] = e1.span.label
                f1['event_model'] = e1.model
                f1['context'] = relation.left_text

                f2 = dict() 
                f2['head_start_char'] = e2.span.start_char_offset()
                f2['head_end_char'] = e2.span.end_char_offset()
                f2['mention_text'] = e2.span.text
                f2['event_type'] = e2.span.label
                f2['event_model'] = e2.model
                f2['context'] = relation.right_text

                r = dict()
                r['left_mention'] = f1
                r['right_mention'] = f2

                if relation.label == 'Contingency.Cause' or relation.label == 'cause':
                    r['relation_type'] = 'causes'
                elif relation.label == 'Contingency.Condition' or relation.label == 'precondition_of':
                    r['relation_type'] = 'impacts'
                elif relation.label == 'Temporal.Asynchronous' or relation.label == 'occurs_before':
                    r['relation_type'] = 'occurs_before'
                
                if e1.snippet == e2.snippet:
                    r['snippet'] = e1.snippet
                else:
                    r['snippet'] = e1.snippet.encode('ascii','ignore') + ' ' + e2.snippet.encode('ascii','ignore')

                json_data['relations'].append(r)
                #if e1.model == event_models.GENERIC and e2.model == event_models.GENERIC:
                #    if '{}_{}_{}'.format(relation.label, a1, a2) in target_factors or '{}_{}_{}'.format(relation.label, a2, a1) in target_factors:
                #        json_data['relations'].append(r)
                #else:
                #    json_data['relations'].append(r)

                #if relation.label == 'Contingency.Cause' and f1['event_model'] == 'KBP' and f2['event_model'] == 'KBP':
                #    outlog.append('{}/{} {}/{}\t{}\t{}'.format(f1['mention_text'].encode('ascii','ignore'), f1['event_type'], f2['mention_text'].encode('ascii','ignore'), f2['event_type'], f1['context'].encode('ascii','ignore'), f2['context'].encode('ascii','ignore')))

        with codecs.open(args.out_serif_json+'/'+docid+'.json', 'w', encoding='utf-8') as o:
            o.write(json.dumps(json_data, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
            o.close()


        counter += 1
        if (counter % 100)==0:
            print(counter)

    #with open('temp.log', 'w') as f:
    #    for line in outlog:
    #        f.write(line)
    #        f.write('\n')

