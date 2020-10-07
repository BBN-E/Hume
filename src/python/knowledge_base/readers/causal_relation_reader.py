import sys, os, re, codecs, json, glob

from collections import defaultdict

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir, "..", ".."))
from cyberlingo.common.utils import Struct
from cyberlingo.common.utils import IntPair
from cyberlingo.text.text_span import TextSpan
from cyberlingo.text.text_span import EventSpan

from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from shared_id_manager.shared_id_manager import SharedIDManager

# Code copied and modified from causal_json.py

class CausalRelationReader:
    
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
            self.sentence = None
            self.pattern = None
            self.confidence = None
            self.model = None	# whether this is from PDTB, Serif-patterns, or LearnIt
    
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
            self.model = None
            self.pattern = None
            self.confidence = None
    
        def to_string(self):
            return ('{}\t{}\t{}\t{}'.format(self.left_factor.span.label, self.label, self.right_factor.span.label, self.left_factor.model))
    
    class Event(object):
        def __init__(self, span, kb_event, kb_event_mention):
            """:type span: cyberlingo.text.text_span.EventSpan"""
            self.span = span
            self.model = None	# one of the event_models
            self.snippet = None
            self.docid = None
            self.kb_event = kb_event
            self.kb_event_mention = kb_event_mention
    
        def to_string(self):
            return ('%s %s' % (self.model, self.span.to_string()))

    # DEBUGGING function
    def print_accent_event_match(self, relation_arg1_text, relation_arg2_text, kb_event_mention, index):
        self.debug_out.write(kb_event_mention.sentence.text + "\n")
        self.debug_out.write("Relation args: " + relation_arg1_text + " " + relation_arg2_text + "\n")
        self.debug_out.write("ACCENT Event: " + kb_event_mention.event_type + " (" + str(index) + ")\n")
        if "Source" in kb_event_mention.arguments:
            self.debug_out.write("Source: " + kb_event_mention.arguments["Source"][0].mention_text + "\n")
        if "Target" in kb_event_mention.arguments:
            self.debug_out.write("Target: " + kb_event_mention.arguments["Target"][0].mention_text + "\n")
        self.debug_out.write("---------------------------------------\n\n")
        
    def find_events_in_doc_relations(self, doc):
        """
        :type doc: Document
        """
        
        kbp_events = []
        accent_events = []
        for event in doc.events:
            if event.model == self.event_models.KBP:
                kbp_events.append(event)
            if event.model == self.event_models.ACCENT:
                accent_events.append(event)

        # Serif/LearnIt causal relations -- look for exact matches
        for relation in doc.relations:
            if relation.model != self.causal_models.LEARNIT and relation.model != self.causal_models.SERIF:
                continue
            
            arg1_events = []
            arg2_events = []

            # Look for ACCENT events that match the relation arguments
            (arg1_accent_events, arg2_accent_events) = self.find_exact_match_events_in_relation_args_accent(relation, accent_events)

            # Look for KBP events that match the relation arguments
            (arg1_kbp_events, arg2_kbp_events) = self.find_exact_match_events_in_relation_args_kbp(relation, kbp_events)

            if len(arg1_accent_events) == 0 and len(arg1_kbp_events) == 0:
                continue
            if len(arg2_accent_events) == 0 and len(arg2_kbp_events) == 0:
                continue

            # Use ACCENT events if found, otherwise use KBP events
            if len(arg1_accent_events) > 0:
                arg1_events.extend(arg1_accent_events)
            else:
                arg1_events.extend(arg1_kbp_events)

            if len(arg2_accent_events) > 0:
                arg2_events.extend(arg2_accent_events)
            else:
                arg2_events.extend(arg2_kbp_events)
                
            if len(arg1_events) > 0 and len(arg2_events) > 0:
                self.add_event_pairs_as_causal(arg1_events, arg2_events, relation, doc)

        # PDTB causal relation -- look for single events that
        # contained within PDTB arguments
        for relation in doc.relations:
            if relation.model != self.causal_models.PDTB:
                continue

            arg1_events = []
            arg2_events = []
            
            # Look for ACCENT events that match the relation arguments
            (arg1_accent_events, arg2_accent_events) = self.find_events_in_relation_args(relation, accent_events)

            # Look for KBP events that match the relation arguments
            (arg1_kbp_events, arg2_kbp_events) = self.find_events_in_relation_args(relation, kbp_events)

            if len(arg1_accent_events) == 0 and len(arg1_kbp_events) == 0:
                continue
            if len(arg2_accent_events) == 0 and len(arg2_kbp_events) == 0:
                continue

            # Use single ACCENT event if found, otherwise use single KBP event
            if len(arg1_accent_events) == 1:
                arg1_events.extend(arg1_accent_events)
            elif len(arg1_kbp_events) == 1:
                arg1_events.extend(arg1_kbp_events)

            if len(arg2_accent_events) == 1:
                arg2_events.extend(arg2_accent_events)
            elif len(arg2_kbp_events) == 1:
                arg2_events.extend(arg2_kbp_events)
                
            if len(arg1_events) > 0 and len(arg2_events) > 0:
                self.add_event_pairs_as_causal(arg1_events, arg2_events, relation, doc)

            
    def add_event_pairs_as_causal(self, events1, events2, relation, doc):
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

                r = self.CausalRelation(relation.label)
                #if start1 <= start2:
                r.left_factor = e1
                r.left_text = relation.arg1_text    
                r.right_factor = e2
                r.right_text = relation.arg2_text
                r.model = relation.model
                r.pattern = relation.pattern
                r.confidence = relation.confidence
                #else:
                #    r.left_factor = e2
                #    r.left_text = relation.arg2_text
                #    r.right_factor = e1
                #    r.right_text = relation.arg1_text

                doc.add_causal_relation(r)
    
    def find_exact_match_events_in_relation_args_accent(self, relation, accent_events):
        arg1_events = []
        for offset in relation.arg1_spans:
            arg1_events.extend(self.find_exact_match_in_propositions(offset, accent_events))

        arg2_events = []
        for offset in relation.arg2_spans:
            arg2_events.extend(self.find_exact_match_in_propositions(offset, accent_events))

        return (arg1_events, arg2_events)

    def find_exact_match_in_propositions(self, offset, events):
        ret = []
        for e in events:
            if len(e.kb_event_mention.proposition_infos) == 0:
                continue
            # First prop_info is typically (not always) the "best" proposition
            # of the event for relation purposes. Matching any prop_info would
            # increase recall, but decrease precision.
            prop_info = e.kb_event_mention.proposition_infos[0] # (head_word, start_offset, end_offset,)
            if offset.first == prop_info[1] and offset.second == prop_info[2]:
                ret.append(e)
        return ret
                
    def find_exact_match_events_in_relation_args_kbp(self, relation, kbp_events):
        """
        :type relation: Relation
        :type kbp_events: list[Event]
        """
        arg1_events = []
        for offset in relation.arg1_spans:
            arg1_events.extend(self.find_exact_match_events_in_span(offset, kbp_events))

        arg2_events = []
        for offset in relation.arg2_spans:
            arg2_events.extend(self.find_exact_match_events_in_span(offset, kbp_events))

        return (arg1_events, arg2_events)

    def find_exact_match_events_in_span(self, offset, events):
        """
        :type offset: IntPair
        :type events: list[Event]
        """
        ret = []
        for e in events:
            e_start = e.span.start_char_offset()
            e_end = e.span.end_char_offset()
            if offset.first == e_start and e_end == offset.second:
                ret.append(e)
        return ret

    def find_events_in_relation_args(self, relation, events):
        """
        :type relation: Relation
        :type events: list[Event]
        """
        arg1_events = []
        for offset in relation.arg1_spans:
            arg1_events.extend(self.find_events_in_span(offset, events))
    
        arg2_events = []
        for offset in relation.arg2_spans:
            arg2_events.extend(self.find_events_in_span(offset, events))
    
        return (arg1_events, arg2_events)

    def find_events_in_span(self, offset, events):
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
        
    def read_causal_relation_json(self, filename, causal_model, flip_args_enabled=False):
        doc_relations = defaultdict(list)
    
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
            except ValueError as ve:
                print("While loading: " + filename)
                print(str(ve))
                sys.exit(1)
                
        for eg in json_data:
            if eg is not None:
    
                semantic_class = eg['semantic_class']
                r = self.Relation(semantic_class)
                flip_args = False
                if 'connective_text' in eg:
                    r.connective_text = eg['connective_text']
                    if flip_args_enabled and r.connective_text.lower() in ("after", "as", "as long as", "because", "insofar as", "now that", "once", "since", "when", "when and if"):
                        flip_args = True

                if 'prob' in eg:
                    r.confidence = float(eg['prob'])

                r.pattern = eg.get('learnit_pattern')
                
                arg1_spans = eg['arg1_span_list']
                arg1_text = eg['arg1_text']
    
                arg2_spans = eg['arg2_span_list']
                arg2_text = eg['arg2_text']
    
                if flip_args:
                    tmp = arg1_spans
                    arg1_spans = arg2_spans
                    arg2_spans = tmp
                    tmp = arg1_text
                    arg1_text = arg2_text
                    arg2_text = tmp
    
                docid = eg['docid']
                if '.' in docid:
                    docid = re.search(r'^(.*)\.(.*)$', docid).group(1)
    
                r.model = causal_model
    
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
    
                if 'cause_sentence' in eg:
                    r.sentence = eg['cause_sentence']
    
                doc_relations[r.docid].append(r)
    
        return doc_relations
    
    def offset_from_offsets(self, offset1, offset2):
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
    
    def add_learnit_causal_relations(self, filepath, docs):
        relations = self.read_causal_relation_json(filepath, self.causal_models.LEARNIT)
        for docid in relations:
            docs[docid].extend(relations[docid])
    
    def add_serif_causal_relations(self, filedir, docs):
        for filepath in glob.glob(filedir+'/*.json'):
            relations = self.read_causal_relation_json(filepath, self.causal_models.SERIF)
            for docid in relations:
                docs[docid].extend(relations[docid])
                
    def __init__(self):
        self.event_models = Struct(KBP='KBP', ACCENT='ACCENT', GENERIC='GENERIC')
        self.causal_models = Struct(PDTB='PDTB', SERIF='SERIF', LEARNIT='LEARNIT')
        # Used in debugging function
        #self.debug_out = codecs.open("/nfs/raid66/u14/users/azamania/temp/accent_event_relations.txt", 'w', encoding='utf8')

    def read(self, kb, serif_causal_relation, learnit_causal_relation, extra_causal_relation):
        print("CausalRelationReader START")
        count = 0
        #docid_to_relation_list = self.read_causal_relation_json(pdtb_json, self.causal_models.PDTB, flip_args_enabled=True)    # docs with pdtb relations
        #for key in docid_to_relation_list:
        #    count += len(docid_to_relation_list[key])
        #print('count = {}'.format(count))

        docid_to_relation_list = defaultdict(list)

        print("CausalRelationReader READ CAUSAL RELATIONS")
        self.add_serif_causal_relations(serif_causal_relation, docid_to_relation_list)
        self.add_learnit_causal_relations(learnit_causal_relation, docid_to_relation_list)
        if extra_causal_relation != "NA":
            self.add_learnit_causal_relations(extra_causal_relation, docid_to_relation_list)
        
        count = 0
        for key in docid_to_relation_list:
            count += len(docid_to_relation_list[key])
            
        # Build Document objects (Document object is a nested class above)
        docid_to_document = dict()
        print("CausalRelationReader READ EVENTS")
        for kb_event in kb.evid_to_kb_event.values():
            model = None
            
            if kb_event.event_mentions[0].model == "ACCENT":
                model = self.event_models.ACCENT
            elif kb_event.event_mentions[0].model == "KBP":
                model = self.event_models.KBP
            else: 
                continue
                
            for kb_event_mention in kb_event.event_mentions:
                event_type = kb_event_mention.event_type
                event_offset = None
                if kb_event_mention.trigger_start is not None and kb_event_mention.trigger_end is not None:
                    start = kb_event_mention.trigger_start
                    end = kb_event_mention.trigger_end
                    event_offset = IntPair(start, end)
                else:
                    source_offset = None
                    target_offset = None
                    if 'Source' in kb_event_mention.arguments:
                        source = kb_event_mention.arguments['Source']
                        source_offset = IntPair(source[0].head_start_char, source[0].head_end_char)
                    if 'Target' in kb_event_mention.arguments:
                        target = kb_event_mention.arguments['Target']
                        target_offset = IntPair(target[0].head_start_char, target[0].head_end_char)
                    event_offset = self.offset_from_offsets(source_offset, target_offset)
                text = kb_event_mention.trigger
                if text is None:
                    text = "dummy"
                snippet = kb_event_mention.snippet
                docid = kb_event_mention.document.id

                # Create local objects
                if docid not in docid_to_document:
                    docid_to_document[docid] = self.Document(docid)
                
                #print kb_event.id
                #print "Creating event span from " + str(event_offset.first) + " " + str(event_offset.second)
                
                span = EventSpan('dummy', event_offset, text, event_type)
                e = self.Event(span, kb_event, kb_event_mention)
                e.model = model
                e.snippet = snippet
                e.docid = docid
                docid_to_document[docid].add_event(e)

        print("CausalRelationReader ADD RELATIONS TO DOCUMENTS")
        """:type: Document"""   
        for docid, doc in docid_to_document.iteritems():
            if docid in docid_to_relation_list:
                relations = docid_to_relation_list[docid]
                doc.add_relations(relations)

        count_stats = defaultdict(int)
        for docid, doc in docid_to_document.iteritems():
            kb_document = kb.docid_to_kb_document[docid]
            self.find_events_in_doc_relations(doc)
            for relation in doc.causal_relations:
                                        
                # e1 and e2 are Event objects above
                e1 = relation.left_factor
                e2 = relation.right_factor

                snippet = None

                # Map to standard type names
                relation_type = relation.label
                if relation.label == "cause" or relation.label == "Contingency.Cause":
                    relation_type = "Cause-Effect"
                elif relation.label == "Contingency.Condition" or relation.label == "precondition_of":
                    relation_type = "Precondition-Effect"
                elif relation.label == "Temporal.Asynchronous" or relation.label == "occurs_before":
                    relation_type = "Before-After"
                elif relation.label == "catalyst_effect":
                    relation_type = "Catalyst-Effect"
                elif relation.label == "cause_effect":
                    relation_type = "Cause-Effect"
                elif relation.label == "mitigating_factor_effect":
                    relation_type = "MitigatingFactor-Effect"
                elif relation.label == "precondition_effect":
                    relation_type = "Precondition-Effect"
                elif relation.label == "preventative_effect":
                    relation_type = "Preventative-Effect"
                
                left_id = e1.kb_event.id
                right_id = e2.kb_event.id
                relation_id = SharedIDManager.get_in_document_id("Relation", docid)
                relation_mention_id = SharedIDManager.get_in_document_id("RelationMention", docid)

                #print("reln: " + relation_type + ", " + left_id + ", " + right_id)

                kb_relation = KBRelation(relation_id, "event-event", relation_type, left_id, right_id)

                e1_start = int(e1.snippet[1])
                e1_end = int(e1.snippet[2])
                e2_start = int(e2.snippet[1])
                e2_end = int(e2.snippet[2])
                    
                if e1_start == e2_start and e1_end == e2_end:
                    snippet = e1.snippet
                else:
                    combined_snippet = [None, None, None]
                    
                    # Combine snippets into one, these should be adjacent sentences
                    if e1_start < e2_start:
                        combined_snippet[0] = e1.snippet[0] + " " + e2.snippet[0]
                        combined_snippet[1] = e1_start
                    else:
                        combined_snippet[0] = e2.snippet[0] + " " + e1.snippet[0]
                        combined_snippet[1] = e2_start
                    if e1_end > e2_end:
                        combined_snippet[2] = e1_end
                    else:
                        combined_snippet[2] = e2_end
                    snippet = combined_snippet

                kb_relation_mention = KBRelationMention(relation_mention_id, e1.kb_event_mention, e2.kb_event_mention, snippet, kb_document)
                kb_relation_mention.properties["model"] = relation.model
                if relation.pattern is not None:
                    kb_relation_mention.properties["pattern"] = relation.pattern
                if relation.confidence is not None:
                    kb_relation_mention.properties["extraction_confidence"] = relation.confidence
                
                kb_relation.add_relation_mention(kb_relation_mention)
                kb.add_relation(kb_relation)
    
        #self.debug_out.close()
