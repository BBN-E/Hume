import re
import json
import io
import os
import sys
import string
import uuid
import operator
import codecs
import rdflib
import ntpath
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, XSD, RDFS
import logging
from rdflib.namespace import DC, FOAF
import copy
import pprint
import time
from datetime import datetime
from collections import defaultdict
from datetime import date
from datetime import timedelta
from calendar import monthrange
import uuid
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..","elements","structured"))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))
from internal_ontology import utility as ontology_utils
from knowledge_base import KnowledgeBase
from shared_id_manager.shared_id_manager import SharedIDManager
from elements.structured.structured_entity import EntityData
from elements.kb_entity import KBEntity
from elements.kb_mention import KBMention
from elements.kb_group import KBEntityGroup
from elements.kb_relation import KBRelation
from elements.kb_value_mention import KBValueMention,KBTimeValueMention,KBMoneyValueMention
from resolvers.structured_resolver import ascii_me

import pickle


logger = logging.getLogger(__name__)

def get_marked_up_string_for_event(kb_event):
    marked_up_starting_points_to_cnt = dict()
    marked_up_ending_points_to_cnt = dict()
    kb_sentence = None
    for kb_event_mention in kb_event.event_mentions:
        if kb_sentence is None:
            kb_sentence = kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence == kb_event_mention.sentence
        start_char_off = kb_event_mention.trigger_start-kb_sentence.start_offset
        end_char_off = kb_event_mention.trigger_end-kb_sentence.start_offset
        marked_up_starting_points_to_cnt[start_char_off] = marked_up_starting_points_to_cnt.get(start_char_off,0)+1
        marked_up_ending_points_to_cnt[end_char_off] = marked_up_ending_points_to_cnt.get(end_char_off,0)+1

    ret = ""
    for c_idx,c in enumerate(kb_sentence.original_text):
        s = ""
        for _ in range(marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "[[" + s
        s = s + c
        for _ in range(marked_up_ending_points_to_cnt.get(c_idx,0)):
            s = s + "]]"
        ret = ret + s
    return ret

# def get_marked_up_string_for_event_event_relation(kb_relation,left_kb_event,right_kb_event):
#     relation_type = kb_relation.relation_type
#     left_marked_up_starting_points_to_cnt = dict()
#     left_marked_up_ending_points_to_cnt = dict()
#     right_marked_up_starting_points_to_cnt = dict()
#     right_marked_up_ending_points_to_cnt = dict()
#     kb_sentence = None
#     left_trigger = None
#     right_trigger = None
#     for left_kb_event_mention in left_kb_event.event_mentions:
#         if kb_sentence is None:
#             kb_sentence = left_kb_event_mention.sentence
#         else:
#             # Only within sentence event please
#             assert kb_sentence == left_kb_event_mention.sentence
#         start_char_off = left_kb_event_mention.trigger_start-kb_sentence.start_offset
#         end_char_off = left_kb_event_mention.trigger_end-kb_sentence.start_offset
#         left_marked_up_starting_points_to_cnt[start_char_off] = left_marked_up_starting_points_to_cnt.get(start_char_off,0)+1
#         left_marked_up_ending_points_to_cnt[end_char_off] = left_marked_up_ending_points_to_cnt.get(end_char_off,0)+1
#         left_trigger = left_kb_event_mention.trigger
#     for right_kb_event_mention in right_kb_event.event_mentions:
#         if kb_sentence is None:
#             kb_sentence = right_kb_event_mention.sentence
#         else:
#             # Only within sentence event please
#             assert kb_sentence == right_kb_event_mention.sentence
#         start_char_off = right_kb_event_mention.trigger_start-kb_sentence.start_offset
#         end_char_off = right_kb_event_mention.trigger_end-kb_sentence.start_offset
#         right_marked_up_starting_points_to_cnt[start_char_off] = right_marked_up_starting_points_to_cnt.get(start_char_off,0)+1
#         right_marked_up_ending_points_to_cnt[end_char_off] = right_marked_up_ending_points_to_cnt.get(end_char_off,0)+1
#         right_trigger = right_kb_event_mention.trigger
#     ret = ""
#     for c_idx,c in enumerate(kb_sentence.original_text):
#         s = ""
#         for _ in range(left_marked_up_starting_points_to_cnt.get(c_idx,0)):
#             s = "[[" + s
#         for _ in range(right_marked_up_starting_points_to_cnt.get(c_idx,0)):
#             s = "[[" + s
#         s = s + c
#         for _ in range(left_marked_up_ending_points_to_cnt.get(c_idx,0)):
#             s = s + "]]"
#         for _ in range(right_marked_up_ending_points_to_cnt.get(c_idx,0)):
#             s = s + "]]"
#         ret = ret + s
#     return "left: {} , right: {} , sentence: {}".format(left_trigger,right_trigger,ret)

def get_marked_up_string_for_event_event_relation(kb_relation,left_kb_event,right_kb_event):

    kb_sentence = None
    left_trigger = None
    right_trigger = None
    for left_kb_event_mention in left_kb_event.event_mentions:
        if kb_sentence is None:
            kb_sentence = left_kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence == left_kb_event_mention.sentence
        start_char_off = left_kb_event_mention.trigger_start-kb_sentence.start_offset
        end_char_off = left_kb_event_mention.trigger_end-kb_sentence.start_offset
        left_trigger = left_kb_event_mention.trigger_original_text
    for right_kb_event_mention in right_kb_event.event_mentions:
        if kb_sentence is None:
            kb_sentence = right_kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence == right_kb_event_mention.sentence
        start_char_off = right_kb_event_mention.trigger_start-kb_sentence.start_offset
        end_char_off = right_kb_event_mention.trigger_end-kb_sentence.start_offset
        right_trigger = right_kb_event_mention.trigger_original_text
    return "Cue: '{}' Cause/Prevent: '{}' Effect: '{}'".format(kb_relation.trigger_text,left_trigger,right_trigger)

def get_marked_up_mention(kb_mention):
    kb_sentence = kb_mention.sentence
    start_char_off = kb_mention.start_char - kb_sentence.start_offset
    end_char_off = kb_mention.end_char - kb_sentence.start_offset
    marked_up_starting_points_to_cnt = dict()
    marked_up_ending_points_to_cnt = dict()
    marked_up_starting_points_to_cnt[start_char_off] = marked_up_starting_points_to_cnt.get(start_char_off, 0) + 1
    marked_up_ending_points_to_cnt[end_char_off] = marked_up_ending_points_to_cnt.get(end_char_off, 0) + 1

    ret = ""
    for c_idx,c in enumerate(kb_sentence.original_text):
        s = ""
        for _ in range(marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "[[" + s
        s = s + c
        for _ in range(marked_up_ending_points_to_cnt.get(c_idx,0)):
            s = s + "]]"
        ret = ret + s
    return ret

class RDFSerializer:

    def get_info_kb_entity_str(self, kb_entity):
        assert isinstance(kb_entity,KBEntity)
        s = ""
        buf = list()
        if kb_entity.is_referred_in_kb:
            s = "Entity id:{} Type:{} canonical_name:{} ".format(kb_entity.id,kb_entity.get_best_entity_type(),kb_entity.canonical_name)
            for kb_entity_mention in kb_entity.mentions:
                s_tmp = self.get_info_kb_mention_str(kb_entity_mention)
                if len(s_tmp) > 0:
                    buf.append(s_tmp)
        return s + "\n".join(buf)


    def get_info_kb_relation_str(self, kb_relation):
        assert isinstance(kb_relation,KBRelation)
        buf = list()
        if kb_relation.argument_pair_type == "entity-entity":
            left_kb_entity = self.kb.entid_to_kb_entity[kb_relation.left_argument_id]
            right_kb_entity = self.kb.entid_to_kb_entity[kb_relation.right_argument_id]
            if left_kb_entity.is_referred_in_kb and right_kb_entity.is_referred_in_kb:
                buf.append("Entity-Entity-Relation id:{} type:{}".format(kb_relation.id,kb_relation.relation_type))
                buf.append("LEFT")
                buf.append(self.get_info_kb_entity_str(left_kb_entity))
                buf.append("RIGHT")
                buf.append(self.get_info_kb_entity_str(right_kb_entity))
            

        elif kb_relation.argument_pair_type == "event-event":
            source_events = self.kb_event_to_rdf_event_ids[self.kb.evid_to_kb_event[kb_relation.left_argument_id]]
            target_events = self.kb_event_to_rdf_event_ids[self.kb.evid_to_kb_event[kb_relation.right_argument_id]]
            local_id_cnt = 0

            src_kb_event = self.kb.evid_to_kb_event[kb_relation.left_argument_id]
            tar_kb_event = self.kb.evid_to_kb_event[kb_relation.right_argument_id]
            for source_event in source_events:
                for target_event in target_events:
                    relation_instance_id = kb_relation.id
                    eer_id = "{}-{}".format(relation_instance_id,local_id_cnt)
                    buf.append("Event-Event-Relation id: {} type: {}".format(eer_id,kb_relation.relation_type))
                    buf.append("Sentence:{}".format(get_marked_up_string_for_event_event_relation(kb_relation,src_kb_event,tar_kb_event)).replace("\n"," "))
                    buf.append("LEFT")
                    buf.append(self.get_info_kb_event_mention_str(src_kb_event,source_event))
                    buf.append("RIGHT")
                    buf.append(self.get_info_kb_event_mention_str(tar_kb_event,target_event))
                    local_id_cnt += 1
        return "\n".join(buf)

    def get_info_kb_entity_group_str(self, kb_entity_group, entity_type):
        assert isinstance(kb_entity_group,KBEntityGroup)
        s = ""
        buf = list()
        if kb_entity_group.is_referred_in_kb:
            s = "EntityGroup id:{} canonical_name:{} type:{}".format(kb_entity_group.id,kb_entity_group.canonical_name,entity_type)
            for kb_entity in kb_entity_group.members:
                s_tmp = self.get_info_kb_entity_str(kb_entity)
                if len(s_tmp) > 0:
                    buf.append(s_tmp)
        return s + "\n".join(buf)


    def get_info_kb_mention_str(self, kb_mention):
        assert isinstance(kb_mention,KBMention)
        s = ""
        if kb_mention.is_referred_in_kb:
            kb_entity = self.kb_mention_to_kb_entity[kb_mention]
            s = "EntityMention id:{} {}:{}".format(kb_mention.id, kb_mention.entity_type,
                                               get_marked_up_mention(kb_mention).replace("\n", " "))
        return s

    def get_info_kb_value_mention_str(self, kb_value_mention):
        assert isinstance(kb_value_mention,KBValueMention)
        return "ValueMention id:{} type:{} text:{}".format(kb_value_mention.id,type(kb_value_mention),kb_value_mention.value_mention_text)

    def get_info_kb_event_mention_str(self, kb_event,rdf_type_caring):
        buf = list()
        for kb_event_mention in kb_event.event_mentions:
            for event_type,confidence in kb_event_mention.external_ontology_sources:
                event_instance_id = self.get_event_instance_id(kb_event, event_type)
                if rdf_type_caring == event_instance_id :
                    event_instance_id = self.get_event_instance_id(kb_event,event_type)
                    bs = "EventMention id:{} type:{}".format(event_instance_id,event_type)
                    bs += "\nSentence: {}".format(get_marked_up_string_for_event(kb_event).replace("\n"," "))
                    for kb_causal_factor in kb_event_mention.causal_factors:
                        bs += "\nICM: {}".format(kb_causal_factor.factor_class)
                    for kb_arg_role,args in kb_event_mention.arguments.items():
                        for arg,score in args:
                            if isinstance(arg,KBMention):
                                bs += "\n{}: {}".format(kb_arg_role, self.get_info_kb_mention_str(arg))
                            elif isinstance(arg,KBValueMention):
                                bs += "\n{}: {}".format(kb_arg_role, self.get_info_kb_value_mention_str(arg))
                    buf.append(bs)
        return "\n".join(buf)

    def __init__(self):
        logging.basicConfig()
        self.graph = Graph()
        self.triples_from_cdr = ""
        self.namespace = dict()
        self.whitelist = []
        self.config = dict()

        self.entity_count = 0
        self.event_count = 0
        self.text_causal_assertion_count = 0

        self.integrity_counts = defaultdict(int)

        self.structured_input_file_count = 0
        self.structured_worksheet_count = 0
        self.structured_time_series_count = 0
        self.structured_entity_count = 0
        self.structured_event_count = 0
        self.structured_relationship_count = 0

        self.span_and_docid_to_id = {}  # map from (start, end, docid) triples to the corresponding ids
        self.mention_span_and_docid_to_id = {}  # map from (start, end, mention_type, docid) tuple to the corresponding ids

        # Keep track of which entities we already outputted a latitute, 
        # longitude for. This is a little weird, but I think a single 
        # country entity ID can have multiple lat/longs due to the vagaries 
        # of actor matching and the fact that we use a single country 
        # entity ID across all documents.
        self.lat_long_output = set() 

        self.kb = None

    def _load_odps(self,ontology_turtle_folder, odps=None):  # TODO parameterize this
        self.odps = Graph()
        self.rules = {}
        if odps is None:
            # odps = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "..", "..", "ontology", "190206")
            odps = ontology_turtle_folder
        for filename in os.listdir(odps):
            file_path = os.path.join(odps, filename)
            if filename.endswith('.ttl'):
                self.odps.parse(file_path, format='turtle')
        if 'subclass.rules' in os.listdir(odps):
            with open(os.path.join(odps, 'subclass.rules'), 'r') as f:
                self.rules = json.load(f)


    def serialize(self, kb, mode,ontology_turtle_folder,
                  seed_milestone, seed_type, seed_version,
                  output_ttl_file, output_nt_file):
        print("RDFSerializer SERIALIZE")

        ### Constructor area
        self._load_odps(ontology_turtle_folder)
        ### End Constructor area

        config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "config_files", "config_ontology.json")
        self.config = self.read_config(config_file)

        output_info_stream = open(output_nt_file + ".info", 'w')

        self.read_namespaces()
        self.read_whitelist()
        self.kb = kb
        self.add_triples_bbn_ontology()

        if mode == "UNSTRUCTURED":

            global TimeMatcher
            from time_matcher import TimeMatcher
            self.time_matcher = TimeMatcher()
            global KBMention
            from elements.kb_mention import KBMention
            global KBValueMention, KBTimeValueMention, KBMoneyValueMention
            from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention

            self.kb_event_mention_to_kb_event = dict()
            for kb_event_id, kb_event in self.kb.evid_to_kb_event.items():
                for kb_event_mention in kb_event.event_mentions:
                    self.kb_event_mention_to_kb_event[kb_event_mention] = kb_event
            self.kb_mention_to_kb_entity = dict()
            for kb_entity_id, kb_entity in self.kb.entid_to_kb_entity.items():
                for kb_mention in kb_entity.mentions:
                    self.kb_mention_to_kb_entity[kb_mention] = kb_entity

            self.kb_entity_to_kb_entity_group = dict()
            self.actor_id_to_kb_entity_group = dict()
            for entgroupid, kb_entity_group in self.kb.entgroupid_to_kb_entity_group.items():
                for kb_entity in kb_entity_group.members:
                    self.kb_entity_to_kb_entity_group[kb_entity] = kb_entity_group
                if kb_entity_group.actor_id is not None:
                    self.actor_id_to_kb_entity_group[kb_entity_group.actor_id] = kb_entity_group

            self.kb_event_to_rdf_event_ids = dict()

            self.entity_group_in_has_actor = set()
            self.entity_in_has_actor = set()
            for kb_event_id,kb_event in self.kb.evid_to_kb_event.items():
                for kb_event_mention in kb_event.event_mentions:
                    # Task 1. Identify entity and entity group that link to has_actor
                    for kb_arg_role,args in kb_event_mention.arguments.items():
                        for arg,score in args:
                            if kb_arg_role in {"has_actor","has_active_actor","has_affected_actor"} and isinstance(arg,KBMention):
                                kb_entity = self.kb_mention_to_kb_entity[arg]
                                kb_entity_group = self.kb_entity_to_kb_entity_group[kb_entity]
                                self.entity_group_in_has_actor.add(kb_entity_group)
                                self.entity_in_has_actor.add(kb_entity)
                    # Task 2. Add generic event type if an event only have ICM type no event type

                    # Task 3. Calculate event ids in rdf space
                    for event_type, confidence in kb_event_mention.external_ontology_sources:
                        event_instance_id = self.get_event_instance_id(kb_event, event_type)
                        self.kb_event_to_rdf_event_ids.setdefault(kb_event, set()).add(event_instance_id)



            # self.kb_document_to_kb_sent_offset_to_kb_sent_map = dict()
            # for doc_id,kb_document in self.kb.docid_to_kb_document:
            #     for kb_sentence in kb_document.sentences:
            #         sent_start = kb_sentence.start_offset
            #         sent_end = kb_sentence.end_offset
            #         self.kb_document_to_kb_sent_offset_to_kb_sent_map.setdefault(kb_document,dict())[(sent_start,sent_end)] = kb_sentence

            self.add_triples_documents_and_sentence_spans()
            self.add_triples_entities()
            self.add_triples_events()
            self.add_triples_relations()

            self.add_triples_entity_groups()
            self.add_triples_event_groups()
            self.add_triples_relation_groups()

            time_completed = datetime.utcnow()  # set to now
            author = "BBN"
            self.add_triples_seed_description(author, seed_milestone, seed_type, seed_version, time_completed)

        # start CRA integration
        elif mode == "STRUCTURED":

            # TODO move serialization steps back into this file/call
            pass
            self.serialize_structured_inputs()
            self.serialize_structured_relationships()
            # end CRA integration

        else:
            print("ERROR: Unknown mode: " + mode)
            sys.exit(1)

        self.discard_subclass_failures()
        self.validate_against_whitelist()
        
        if mode == "UNSTRUCTURED":
            output_info_stream.write("Entity count: " + str(self.entity_count) + "\n")
            output_info_stream.write("Event count: " + str(self.event_count) + "\n")
            output_info_stream.write("Causal assertion in text count: " + str(self.text_causal_assertion_count) + "\n")

        if mode == "STRUCTURED":
            output_info_stream.write("Structured input file count: " + str(self.structured_input_file_count) + "\n")
            output_info_stream.write("Structured worksheet count: " + str(self.structured_worksheet_count) + "\n")
            output_info_stream.write("Structured time series count: " + str(self.structured_time_series_count) + "\n")
            output_info_stream.write("Structured entity count: " + str(self.structured_entity_count) + "\n")
            output_info_stream.write("Structured event count: " + str(self.structured_event_count) + "\n")
            output_info_stream.write("Structured relationship count: " + str(self.structured_relationship_count) + "\n")

        output_info_stream.close()

        self.save_to_file(output_ttl_file, output_nt_file)

        return

    def validate_against_whitelist(self):
        non_whitelisted_rdf_object_to_count = dict()
        implicitly_whitelisted_namespace_labels = ["BBNTA1", "RDF", "RDFS", "DOCSOURCE"]
        implicitly_whitelisted_namespace_strings = [str(self.namespace[namespace_label]) for namespace_label in implicitly_whitelisted_namespace_labels]
        for subject, predicate, object in self.graph:
            for triple_item in (subject, predicate, object):
                if type(triple_item) is rdflib.term.URIRef: # as opposed to rdflib.term.Literal
                    triple_item_str = str(triple_item)
                    implicitly_whitelisted = False
                    for namespace_string in implicitly_whitelisted_namespace_strings:
                        if triple_item_str.startswith(namespace_string):
                            implicitly_whitelisted = True
                            break
                    if implicitly_whitelisted:
                        continue
                    if triple_item_str not in self.whitelist:
                        if triple_item_str not in non_whitelisted_rdf_object_to_count:
                            non_whitelisted_rdf_object_to_count[triple_item_str] = 0
                        non_whitelisted_rdf_object_to_count[triple_item_str] = non_whitelisted_rdf_object_to_count[triple_item_str] + 1
        for rdf_object_and_count in sorted(non_whitelisted_rdf_object_to_count.items(), key=operator.itemgetter(1), reverse=True):
            count = rdf_object_and_count[1]
            rdf_object = rdf_object_and_count[0]
            print("WARNING non-whitelisted rdf object %s (%d occurences)" % (rdf_object, count))

    def save_to_file(self, output_ttl_file, output_nt_file):
        self.serialize_to_file("nt", output_nt_file)
        self.serialize_to_file("turtle", output_ttl_file)
        
    def serialize_to_file(self, serialization_format, filename):
        filename = "%s.%s" % (filename, serialization_format)
        print("RDFSerializer SERIALIZING TO FILE " + filename)


        # Can we get rid of self.triples_from_cdr and import the triples
        # directly into the graph?
        with open(filename,'wb') as wfp:
            self.graph.serialize(destination=wfp, format=serialization_format)
            if serialization_format == "nt" and len(self.triples_from_cdr) > 0:
                wfp.write(self.triples_from_cdr.encode("utf-8"))


    # TODO: Automatically add this type of information 
    #       whenever we come across an entity of a BBN type
    def add_triples_bbn_ontology(self):
        self.add_subtype("Pipeline", "CCO:Artifact")
    def add_subtype(self, bbn_class_name, ontology_type):
        [namespace, ontology_class] = ontology_type.split(':')
        self.graph.add(
            (self.namespace['BBNTA1'][bbn_class_name], 
             self.namespace['RDFS']['subClassOf'],
             self.namespace[namespace][ontology_class]))
        self.graph.add(
            (self.namespace['BBNTA1'][bbn_class_name], 
             self.namespace['RDF']['type'],
             self.namespace['OWL']['Class']))
    ##############

    def _get_event_type_label(self, string):
        resolve_tokens = ontology_utils.TokenizationMode.CAMELCASE([string])
        return u" ".join(resolve_tokens)

    def add_triples_bbn_event(self, uri):
        uri_a_owl_class = (uri,
                           self.namespace['RDF']['type'],
                           self.namespace['OWL']['Class'])
        uri_subclassof_event = (uri,
                                self.namespace['RDFS']['subClassOf'],
                                self.namespace['EVENT']['Event'])
        base_name = uri.split('/')[-1].split('#')[-1]
        label = self._get_event_type_label(base_name)
        uri_label = (uri, 
                     self.namespace['RDFS']['label'], 
                     Literal(base_name))
        comment = u' '.join([u'BBN TA1 event class', label])
        uri_comment = (uri, 
                       self.namespace['RDFS']['comment'],
                       Literal(comment))
        self.graph.add(uri_a_owl_class)
        self.graph.add(uri_comment)
        self.graph.add(uri_label)
        self.graph.add(uri_subclassof_event)
        self.odps.add(uri_a_owl_class)
        self.odps.add(uri_comment)
        self.odps.add(uri_label)
        self.odps.add(uri_subclassof_event)

    def add_triples_entities(self):
        entity_length = len(self.kb.entid_to_kb_entity)
        count = 0
        for entid, kb_entity in self.kb.entid_to_kb_entity.items():
            if count % 1000 == 0:
                print("RDFSerializer creating triples from KBEntity (" + str(count) + "/" + str(entity_length) + ")")
            count += 1
            if kb_entity.is_referred_in_kb:
                self.create_triples_from_entity(kb_entity)
            else:
                print("SKIPPING Entity {}".format(entid))

    def add_triples_entity_groups(self):
        entity_group_length = len(self.kb.entgroupid_to_kb_entity_group)
        count = 0
        for entgroupid, kb_entity_group in self.kb.entgroupid_to_kb_entity_group.items():
            if count % 1000 == 0:
                print("RDFSerializer creating triples from KBEntityGroup (" + str(count) + "/" + str(entity_group_length) + ")")
            count += 1
            if kb_entity_group.is_referred_in_kb:
                self.create_triples_from_entity_group(kb_entity_group)
            else:
                print("SKIPPING EntityGroup {}".format(entgroupid))

    def add_triples_events(self):
        event_length = len(self.kb.evid_to_kb_event)
        count = 0
        for evid, kb_event in self.kb.evid_to_kb_event.items():
            if count % 1000 == 0:
                print("RDFSerializer creating triples from KBEvent (" + str(count) + "/" + str(event_length) + ")")
            count += 1
            self.create_triples_from_event(kb_event)

    def add_triples_event_groups(self):
        event_group_length = len(self.kb.evgroupid_to_kb_event_group)
        count = 0
        for evgroupid, kb_event_group in self.kb.evgroupid_to_kb_event_group.items():
            if count % 1000 == 0:
                print("RDFSerializer creating triples from KBEventGroup (" + str(count) + "/" + str(
                    event_group_length) + ")")
            count += 1
            self.create_triples_from_event_group(kb_event_group)

    def add_triples_relations(self):
        rel_length = len(self.kb.relid_to_kb_relation)
        count = 0
        for relid, kb_relation in self.kb.relid_to_kb_relation.items():
            if count % 1000 == 0:
                print("RDFSerializer creating triples from KBRelation (" + str(count) + "/" + str(rel_length) + ")")
            count += 1
            if kb_relation.argument_pair_type == "entity-entity":
                left_entity = self.kb.entid_to_kb_entity[kb_relation.left_argument_id]
                right_entity = self.kb.entid_to_kb_entity[kb_relation.right_argument_id]
                if left_entity.is_referred_in_kb is False or right_entity.is_referred_in_kb is False:
                    print("SKIPPING entity entity relation {}".format(relid))
                else:
                    self.create_triples_from_entity_relation(kb_relation)
            elif kb_relation.argument_pair_type == "event-event":
                self.create_triples_from_event_relation(kb_relation)

    def add_triples_relation_groups(self):
        relation_group_length = len(self.kb.relgroupid_to_kb_relation_group)
        count = 0
        for relgroupid, kb_relation_group in self.kb.relgroupid_to_kb_relation_group.items():
            if count % 1000 == 0:
                print("RDFSerializer creating triples from KBRelationGroup (" + str(count) + "/" + str(
                    relation_group_length) + ")")
            count += 1

            self.create_triples_from_relation_group(kb_relation_group)

    def create_triples_from_relation_group(self, kb_relation_group):

        if len(kb_relation_group.members) > 1:  # don't process singletons
            # RDF URI for this relation group instance:
            relation_group_instance = self.namespace["BBNTA1"][kb_relation_group.id]
            var_mappings = {"instance": relation_group_instance}

            # serialize group membership definitions
            for kb_relation in kb_relation_group.members:

                if kb_relation.argument_pair_type == "event-event":  # do not process entity-entity relations
                    relation_mapping = self.config["mappings"]["event-causal-relation"][kb_relation.relation_type]
                    [namespace_name, ontology_class] = relation_mapping.get("default_relationship",
                                                                            relation_mapping.get("default_type")).split(":")
                    var_mappings["relationship"] = self.namespace[namespace_name][ontology_class]
                    raise ValueError("kb_relation id is not usable now.")
                    var_mappings["member"] = self.namespace["BBNTA1"][kb_relation.id]

                    self.create_triples("relation_group-unification", [], var_mappings=var_mappings)  # group unification ontologies are separate but identical

    def _get_supers(self, iri):
        supers = set(self.odps.transitive_objects(iri, RDFS.subClassOf))
        for super in list(supers)[:]:
            unions = self.odps.objects(super, self.namespace['OWL'].unionOf)
            for union_node in unions:
                members = self.odps.transitive_objects(union_node, URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#rest'))
                for member_node in members:
                    member_class = self.odps.value(subject=member_node, predicate=URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#first'))
                    if member_class is None:
                        continue
                    member_supers = self.odps.transitive_objects(member_class, RDFS.subClassOf)
                    for member_super in member_supers:
                        supers.add(member_super)
        return list(supers)

    def has_valid_subclass(self, candidate_uris, valid_superclasses):
        for uri in candidate_uris:
            supers = self._get_supers(uri)
            supers = [str(super) for super in supers]
            if any([super in supers for super in valid_superclasses]):
                return True
        return False

    def check_subclass_rules(self, subj, pred, obj):
        if str(pred) in self.rules:
            if "domain" in self.rules[str(pred)]:
                subj_types = list(self.odps.objects(subj, RDF.type))
                subj_types.extend(self.graph.objects(subj, RDF.type))
                valid_supers = list(self.rules[str(pred)]["domain"])

                if not self.has_valid_subclass(subj_types, valid_supers):
                    #print subj
                    #print 's --', [list(self.odps.transitive_objects(uri, RDFS.subClassOf)) for uri in subj_types], valid_supers
                    self.integrity_counts['{}: domain'.format(pred)] += 1
                    return False
            if "range" in self.rules[str(pred)]:
                obj_types = list(self.odps.objects(obj, RDF.type))
                obj_types.extend(self.graph.objects(obj, RDF.type))
                valid_supers = list(self.rules[str(pred)]["range"])
                if not self.has_valid_subclass(obj_types, valid_supers):
                    #print obj, '(', obj_types, ')'
                    #print 'o --', [list(self.odps.transitive_objects(uri, RDFS.subClassOf)) for uri in obj_types], valid_supers
                    self.integrity_counts['{}: range'.format(pred)] += 1
                    return False
        return True

    def create_triples_from_entity_relation(self, kb_relation):
        source_entity = self.kb.entid_to_kb_entity[kb_relation.left_argument_id]
        left_entity_id = kb_relation.left_argument_id
        target_entity = self.kb.entid_to_kb_entity[kb_relation.right_argument_id]
        right_entity_id = kb_relation.right_argument_id

        # few cases that flip the argument
        if self.config["mappings"]["entity-relation"][kb_relation.relation_type]["reverse"]:
            tmp = source_entity
            source_entity = target_entity
            target_entity = tmp
            tmp = left_entity_id
            left_entity_id = right_entity_id
            right_entity_id = tmp

        source_entity_ontology_object = self.get_entity_ontology_object(
            source_entity)
        target_entity_ontology_object = self.get_entity_ontology_object(
            target_entity)

        # Use entity group object instead of entity object
        if self.config["mappings"]["entity-relation"][kb_relation.relation_type]["use_group_for_source"]:
            source_entity_ontology_object = self.get_entity_group_ontology_object(
                self.kb_entity_to_kb_entity_group[source_entity])

        [namespace_name, ontology_class] = self.config["mappings"]["entity-relation"][kb_relation.relation_type][
            "type"].split(":")
        relationship = self.namespace[namespace_name][ontology_class]

        # represent *Details such as actor:AffiliationDetails
        if "has_affiliation" in relationship:
            [namespace_name, ontology_class] = \
            self.config["mappings"]["entity-relation-arg-details"]["has_affiliation"]["concept_details"].split(":")
            concept_details = self.namespace[namespace_name][ontology_class]
            [namespace_name, ontology_class] = \
            self.config["mappings"]["entity-relation-arg-details"]["has_affiliation"]["predicate"].split(":")
            pred = self.namespace[namespace_name][ontology_class]

            if not self.check_subclass_rules(source_entity_ontology_object,
                                             pred,
                                             target_entity_ontology_object):
                #print('dropping: {}, {}, {}'.format(source_entity_ontology_object, pred, target_entity_ontology_object))
                return

            var_mappings = {
                "left_arg": source_entity_ontology_object,
                "arg_instance": self.namespace["BBNTA1"]["Affiliation-%s-to-%s" % (left_entity_id, right_entity_id)],
                "arg_details_concept": concept_details,
                "relationship": relationship
            }

            optional_fields = []

            optional_fields.append("arg_instance_predicate")
            var_mappings["arg_entity_instance"] = target_entity_ontology_object
            var_mappings["pred"] = pred

            # add sentence(s) as provenances for this affiliaton intance
            kb_relation_mention = kb_relation.relation_mentions[0]  # assuming only one
            if kb_relation_mention.left_mention is not None:
                var_mappings["left_sentence_id"] = self.namespace["BBNTA1"][
                    kb_relation_mention.left_mention.sentence.id]
                optional_fields.append("left-sentence")
            if kb_relation_mention.right_mention is not None:
                var_mappings["right_sentence_id"] = self.namespace["BBNTA1"][
                    kb_relation_mention.right_mention.sentence.id]
                optional_fields.append("right-sentence")

            logger.debug(self.get_info_kb_relation_str(kb_relation))
            self.create_triples(
                "entity-relation-arg-details",
                optional_fields,
                var_mappings=var_mappings
            )
        else:
            if not self.check_subclass_rules(source_entity_ontology_object,
                                             relationship,
                                             target_entity_ontology_object):
                #print('dropping: {}, {}, {}'.format(source_entity_ontology_object, relationship, target_entity_ontology_object))
                return

            logger.debug(self.get_info_kb_relation_str(kb_relation))
            self.create_triples(
                "entity-relation",
                [],
                var_mappings={
                    "left_arg": source_entity_ontology_object,
                    "right_arg": target_entity_ontology_object,
                    "relationship": relationship
                }
            )

    def get_entity_ontology_object(self, kb_entity):
        return self.namespace["BBNTA1"][kb_entity.id]

    def get_entity_group_ontology_object(self,kb_entity_group):
        is_cameo_country, entity_group_id = kb_entity_group.get_cameo_code_or_id()
        if is_cameo_country is True:
            return self.namespace["CAMEOCC"]["CAMEO" + entity_group_id.lower()]
        else:
            return self.namespace["BBNTA1"][entity_group_id]

    def create_currency_rdf_double(self, decimal_value):
        # this is necessary because for some large values like 1000000000000, we would output the literal with scientific notation
        # e.g.:
        # "1e+12"^^<http://www.w3.org/2001/XMLSchema#decimal>
        # whereas we actually need:
        # "1000000000000.00"^^<http://www.w3.org/2001/XMLSchema#double>
        return Literal(format(decimal_value, '0.2f'), datatype=XSD.double)

    def create_triples_from_event_relation(self, kb_relation):
        relation_type = kb_relation.relation_type
        source_events = self.kb_event_to_rdf_event_ids[self.kb.evid_to_kb_event[kb_relation.left_argument_id]]
        target_events = self.kb_event_to_rdf_event_ids[self.kb.evid_to_kb_event[kb_relation.right_argument_id]]

        if "default_relationship" in self.config["mappings"]["event-causal-relation"][relation_type]:
            # this isn't really a causal relation - but it is something from which we want to create a regular relation
            # with the two events as the arguments
            [namespace_name, ontology_class] = self.config["mappings"]["event-causal-relation"][relation_type][
                "default_relationship"].split(":")
            relation_ontology_class = self.namespace[namespace_name][ontology_class]
            relation_instance_id = kb_relation.id

            if relation_type != "Before-After":
                self.text_causal_assertion_count += 1

            for source_event in source_events:
                for target_event in target_events:
                    logger.debug(self.get_info_kb_relation_str(kb_relation))
                    self.create_triples(
                        "event-relation",
                        [],
                        var_mappings={
                            "left_arg": source_event,
                            "right_arg": target_event,
                            "relationship": self.namespace[namespace_name][ontology_class]
                        }
                    )
        else:
            # is an bona fide causal relation
            self.text_causal_assertion_count += 1
            [namespace_name, ontology_class] = self.config["mappings"]["event-causal-relation"][relation_type][
                "default_type"].split(":")
            relation_ontology_class = self.namespace[namespace_name][ontology_class]
            relation_instance_id = kb_relation.id

            [namespace_name, ontology_class] = self.config["mappings"]["event-causal-relation"][relation_type][
                "left_predicate"].split(":")
            left_pred = self.namespace[namespace_name][ontology_class]
            [namespace_name, ontology_class] = self.config["mappings"]["event-causal-relation"][relation_type][
                "right_predicate"].split(":")
            right_pred = self.namespace[namespace_name][ontology_class]

            local_id_cnt = 0

            eer_marked_up_string = get_marked_up_string_for_event_event_relation(kb_relation,self.kb.evid_to_kb_event[kb_relation.left_argument_id],self.kb.evid_to_kb_event[kb_relation.right_argument_id])

            for source_event in source_events:
                for target_event in target_events:
                    left_arg = source_event
                    right_arg = target_event
                    logger.debug(self.get_info_kb_relation_str(kb_relation))
                    self.create_triples(
                        "event-causal-relation",
                        [],
                        var_mappings={
                            "instance": self.namespace["BBNTA1"]["{}-{}".format(relation_instance_id,local_id_cnt)],
                            "ontology_class": relation_ontology_class,
                            "left_pred": left_pred,
                            "left_arg": left_arg,
                            "right_pred": right_pred,
                            "right_arg": right_arg,
                            "confidence": Literal(format(kb_relation.confidence, '0.2f'), datatype=XSD.decimal),
                            "strength": Literal(1, datatype=XSD.decimal),
                            "eer_marked_up_string": Literal(re.sub("\n", " ", eer_marked_up_string),
                                                            datatype=XSD.string),
                            "polarity": self.config["mappings"]["general-concepts-property"][kb_relation.polarity]
                        }
                    )

                    for kb_relation_mention in kb_relation.relation_mentions:

                        for kb_sentence in [kb_relation_mention.left_mention.sentence,
                                            kb_relation_mention.right_mention.sentence]:
                            self.create_triples(
                                "source-sentence",
                                [],
                                var_mappings={
                                    "instance": self.namespace["BBNTA1"]["{}-{}".format(relation_instance_id,local_id_cnt)],
                                    "sentenceSpanInstance": self.namespace["BBNTA1"][kb_sentence.id],
                                    "docInstance": self.get_causeex_docid(kb_relation_mention.document)
                                }
                            )

                    local_id_cnt += 1







    def create_triples_from_entity_group(self,kb_entity_group):
        entity_group_instance = self.get_entity_group_ontology_object(kb_entity_group)
        is_cameo_country, entity_group_id = kb_entity_group.get_cameo_code_or_id()

        var_mappings = {
            "instance": entity_group_instance
        }
        optional_fields = set()
        # add canonical name
        
        if kb_entity_group.canonical_name is not None:
            optional_fields.add("canonical_name")
            var_mappings["canonical_name"] = Literal(kb_entity_group.canonical_name.replace("\t"," ").replace("\n"," "), datatype=XSD.string)
        else:
            entity_canonical_name = self.get_canonical_name_from_entity(kb_entity_group.members[0])
            if entity_canonical_name is not None:
                optional_fields.add("canonical_name")
                var_mappings["canonical_name"] = Literal(entity_canonical_name.replace("\t"," ").replace("\n"," "), datatype=XSD.string)

        entity_type = None
        for kb_entity in kb_entity_group.members:
            if kb_entity.is_referred_in_kb is False:
                continue
            entity_instance = self.get_entity_ontology_object(kb_entity)

            entity_type, entity_subtype = kb_entity.get_best_entity_type().split(".")

            # find an ontological type
            [namespace_name, ontology_class] = self.config["mappings"]["entity"][entity_type]["sub_types"][
                entity_subtype].split(":")
            var_mappings["ontology_class"] = self.namespace[namespace_name][ontology_class]
            optional_fields.add("entity_type")

            if entity_type in ("LOC", "FAC", "GPE"):
                optional_fields.add("entity_type_location")

            # find secondary type

            if kb_entity_group in self.entity_group_in_has_actor:
                var_mappings["secondary_ontology_class"] = self.namespace["EVENT"]["Actor"]
                optional_fields.add("additional_entity_type")
            else:
                if (entity_type in self.config["mappings"]["entity_secondary_type"] and
                        entity_subtype in self.config["mappings"]["entity_secondary_type"][entity_type]):
                    [namespace_name, ontology_class] = self.config["mappings"]["entity_secondary_type"][
                        entity_type][entity_subtype].split(":")
                    var_mappings["secondary_ontology_class"] = self.namespace[namespace_name][ontology_class]
                    optional_fields.add("additional_entity_type")

            # add canonical name
            if kb_entity.canonical_name is not None and "canonical_name" not in optional_fields:
                optional_fields.add("canonical_name")
                var_mappings["canonical_name"] = Literal(kb_entity.canonical_name.replace("\t"," ").replace("\n"," "), datatype=XSD.string)

            # add longitude and latitude
            if entity_group_instance not in self.lat_long_output:
                if "latitude" in kb_entity.properties:
                    optional_fields.add("latitude")
                    var_mappings["latitude"] = Literal(kb_entity.properties["latitude"], datatype=XSD.decimal)
                    self.lat_long_output.add(entity_group_instance)
                if "longitude" in kb_entity.properties:
                    optional_fields.add("longitude")
                    var_mappings["longitude"] = Literal(kb_entity.properties["longitude"], datatype=XSD.decimal)
                    self.lat_long_output.add(entity_group_instance)

            # add citizenship country code
            if "citizenship_cameo_country_code" in kb_entity.properties:
                cameo_country_code = "CAMEO" + kb_entity.properties["citizenship_cameo_country_code"].lower()
                var_mappings["citizenship_details_instance"] = self.namespace["BBNTA1"][
                    "CITIZENSHIPDETAILS-" + cameo_country_code]
                var_mappings["cameo_country_code"] = self.namespace["CAMEOCC"][cameo_country_code]
                optional_fields.add("citizenship")

            # add ethnicity
            if "ethnicity" in kb_entity.properties:
                ethnicity = kb_entity.properties["ethnicity"]
                var_mappings["ethnicity_details_instance"] = self.namespace["BBNTA1"][
                    "ETHNICITY-DETAILS-" + ethnicity]
                var_mappings["ethnicity"] = self.namespace["ACTOR"][ethnicity]
                optional_fields.add("ethnicity")
            
            # Create unify edge
            self.create_triples("entity-group-unification",[],var_mappings={
                "instance":entity_group_instance,
                "entity_instance":entity_instance
            })

        # when kb_entity_group is a geoname and we could determine its country
        if "geonames_country_code" in kb_entity_group.properties and is_cameo_country == False:
            geoname_country_code = kb_entity_group.properties["geonames_country_code"]
            var_mappings["geoname_country_cameo_code"] = self.namespace["CAMEOCC"]["CAMEO" + geoname_country_code.lower()]
            optional_fields.add("geoname_country")

        # When kb_entity_group is a component of another entity_group
        if "component_of_actor_ids" in kb_entity_group.properties:
            for containing_actor_id in kb_entity_group.properties["component_of_actor_ids"]:
                if containing_actor_id in self.actor_id_to_kb_entity_group:
                    containing_entity_group = self.actor_id_to_kb_entity_group[containing_actor_id]
                    var_mappings["containing_entity_group"] = self.get_entity_group_ontology_object(containing_entity_group)
                    optional_fields.add("component_of")

        logger.debug(self.get_info_kb_entity_group_str(kb_entity_group, entity_type))
        self.create_triples("entity-group", optional_fields, var_mappings=var_mappings)

        # CAMEO affiliation from AWAKE, use AffiliationDetails structure
        if "awake_affiliated_cameo_code" in kb_entity_group.properties:
            awake_affiliated_cameo_code = kb_entity_group.properties["awake_affiliated_cameo_code"]
            var_mappings = {
                "left_arg": entity_group_instance,
                "arg_instance": self.namespace["BBNTA1"]["Affiliation-%s-to-%s" % (kb_entity_group.id, awake_affiliated_cameo_code)],
                "arg_details_concept": self.namespace["ACTOR"]["AffiliationDetails"],
                "relationship": self.namespace["ACTOR"]["has_affiliation"],
                "pred": self.namespace["ACTOR"]["related_affiliation"],
                "arg_entity_instance": self.namespace["CAMEOCC"]["CAMEO" + awake_affiliated_cameo_code.lower()]
                }
            optional_fields = ["arg_instance_predicate"]
            self.create_triples(
                "entity-relation-arg-details",
                optional_fields,
                var_mappings=var_mappings
            )

    def create_triples_from_entity(self, kb_entity):
        entity_instance = self.get_entity_ontology_object(kb_entity)
        var_mappings = {
            "instance": entity_instance
        }
        optional_fields = set()
        if not str(entity_instance).startswith(self.namespace["CAMEOCC"]):
            entity_type, entity_subtype = kb_entity.get_best_entity_type().split(".")

            # find an ontological type
            [namespace_name, ontology_class] = self.config["mappings"]["entity"][entity_type]["sub_types"][
                entity_subtype].split(":")
            var_mappings["ontology_class"] = self.namespace[namespace_name][ontology_class]
            optional_fields.add("entity_type")

            if entity_type in ("LOC", "FAC", "GPE"):
                optional_fields.add("entity_type_location")

            # find secondary type
            if kb_entity in self.entity_in_has_actor:
                var_mappings["secondary_ontology_class"] = self.namespace["EVENT"]["Actor"]
                optional_fields.add("additional_entity_type")
            else:
                if (entity_type in self.config["mappings"]["entity_secondary_type"] and
                        entity_subtype in self.config["mappings"]["entity_secondary_type"][entity_type]):
                    [namespace_name, ontology_class] = self.config["mappings"]["entity_secondary_type"][
                        entity_type][entity_subtype].split(":")
                    var_mappings["secondary_ontology_class"] = self.namespace[namespace_name][ontology_class]
                    optional_fields.add("additional_entity_type")

        # add canonical name
        canonical_label = self.get_canonical_name_from_entity(kb_entity)
        if canonical_label is not None:
            optional_fields.add("canonical_name")
            var_mappings["canonical_name"] = Literal(canonical_label.replace("\t"," ").replace("\n"," "), datatype=XSD.string)

        # add longitude and latitude
        if entity_instance not in self.lat_long_output:
            if "latitude" in kb_entity.properties:
                optional_fields.add("latitude")
                var_mappings["latitude"] = Literal(kb_entity.properties["latitude"], datatype=XSD.decimal)
                self.lat_long_output.add(entity_instance)
            if "longitude" in kb_entity.properties:
                optional_fields.add("longitude")
                var_mappings["longitude"] = Literal(kb_entity.properties["longitude"], datatype=XSD.decimal)
                self.lat_long_output.add(entity_instance)

        # add citizenship country code
        if "citizenship_cameo_country_code" in kb_entity.properties:
            cameo_country_code = "CAMEO" + kb_entity.properties["citizenship_cameo_country_code"].lower()
            var_mappings["citizenship_details_instance"] = self.namespace["BBNTA1"][
                "CITIZENSHIPDETAILS-" + cameo_country_code]
            var_mappings["cameo_country_code"] = self.namespace["CAMEOCC"][cameo_country_code]
            optional_fields.add("citizenship")

        # add ethnicity
        if "ethnicity" in kb_entity.properties:
            ethnicity = kb_entity.properties["ethnicity"]
            var_mappings["ethnicity_details_instance"] = self.namespace["BBNTA1"][
                "ETHNICITY-DETAILS-" + ethnicity]
            var_mappings["ethnicity"] = self.namespace["ACTOR"][ethnicity]
            optional_fields.add("ethnicity")

        self.entity_count += 1
        logger.debug(self.get_info_kb_entity_str(kb_entity))
        self.create_triples("entity", optional_fields, var_mappings=var_mappings)

        for kb_mention in kb_entity.mentions:
            if kb_mention.is_referred_in_kb is False:
                print("SKIPPING entity mention {}".format(kb_mention.id))
                continue
            kb_document = kb_mention.document
            docId = kb_document.id

            if (kb_mention.start_char, kb_mention.end_char, docId) in self.span_and_docid_to_id:
                spanID = self.span_and_docid_to_id[(kb_mention.start_char, kb_mention.end_char, docId)]
            else:
                spanID = SharedIDManager.get_in_document_id("Span", docId)
                self.span_and_docid_to_id[(kb_mention.start_char, kb_mention.end_char, docId)] = spanID

            mention_span_start = kb_mention.head_start_char
            mention_span_end = kb_mention.head_end_char
            mention_span_text = kb_mention.mention_original_head_text

            # For non-names, use full text for mention span
            if kb_mention.mention_type != "name" and kb_mention.mention_text.count(" ") < 10:
                mention_span_start = kb_mention.start_char
                mention_span_end = kb_mention.end_char
                mention_span_text = kb_mention.mention_original_text
            
            if (mention_span_start, mention_span_end, kb_mention.mention_type, docId) in self.mention_span_and_docid_to_id:
                mentionSpanID = self.mention_span_and_docid_to_id[(mention_span_start, mention_span_end, kb_mention.mention_type, docId)]
            else:
                mentionSpanID = SharedIDManager.get_in_document_id("MentionSpan", docId)
                self.mention_span_and_docid_to_id[(mention_span_start, mention_span_end, kb_mention.mention_type, docId)] = mentionSpanID

            self.create_triples(
                "span",
                [],
                var_mappings={
                    "spanInstance": self.namespace["BBNTA1"][spanID],
                    "startOffset": Literal(self.adjust_offset(kb_mention.start_char, kb_mention.document), datatype=XSD.long),
                    "textLength": Literal(kb_mention.end_char - kb_mention.start_char + 1, datatype=XSD.long),
                    "text": Literal(re.sub("\n", " ", kb_mention.mention_original_text), datatype=XSD.string),
                    "docInstance": self.get_causeex_docid(kb_document),
                    "sentenceInstance": self.namespace["BBNTA1"][kb_mention.sentence.id]
                }
            )
            logger.debug(self.get_info_kb_mention_str(kb_mention))
            self.create_triples(
                "entity-mention-span",
                [],
                var_mappings={
                    "mentionSpanInstance": self.namespace["BBNTA1"][mentionSpanID],
                    "startOffset": Literal(self.adjust_offset(mention_span_start, kb_mention.document), datatype=XSD.long),
                    "textLength": Literal(mention_span_end - mention_span_start + 1, datatype=XSD.long),
                    "mention_text": Literal(re.sub("\n", " ", mention_span_text), datatype=XSD.string),
                    "mention_type": self.get_entity_mention_ontology_type_object(kb_mention.mention_type),
                    "docInstance": self.get_causeex_docid(kb_document),
                    "sentenceInstance": self.namespace["BBNTA1"][kb_mention.sentence.id],
                    "spanInstance": self.namespace["BBNTA1"][spanID],
                    "entityInstance": entity_instance
                }
            )
    

    def _grounded_event_type_is_bbnta1(self, event_type_string):
        bbn_ns = str(self.config.get("namespace", {}).get("BBNTA1", "_INVALID"))
        return event_type_string.startswith(bbn_ns)


    def create_triples_from_event_group(self, kb_event_group):

        if len(kb_event_group.members) > 1:  # don't process singletons
            # RDF URI for this event group instance:
            event_group_instance = self.namespace["BBNTA1"][kb_event_group.id]
            var_mappings = {"instance": event_group_instance}

            self.create_triples("event_group-unification", [],
                                var_mappings=var_mappings)  # group unification ontologies are separate but identical

            # serialize group membership definitions
            for kb_event in kb_event_group.members:
                for rdf_event_ids in self.kb_event_to_rdf_event_ids[kb_event]:
                    event_type = list(kb_event.event_type_to_confidence.keys())[0]

                    var_mappings["ontology_class"] = URIRef(event_type)

                    var_mappings["member"] = rdf_event_ids  # reset "member" variable each loop
                    self.create_triples("event_group-unification-unify", [],
                                        var_mappings=var_mappings)  # group unification ontologies are separate but identical


    def create_triples_for_event_grounding(self,instance_id,event_type,confidence):
        type_assignment = URIRef(event_type)
        event_basename = event_type.split('/')[-1].split('#')[-1]
        var_mappings = {
            "instance": instance_id,
            "label": Literal(re.sub("\n", " ", event_type), datatype=XSD.string),
            "ontology_class": type_assignment,
            "confidence": Literal(format(confidence, '0.2f'), datatype = XSD.decimal),
        }
        optional_fields = []
        if self._grounded_event_type_is_bbnta1(event_type):
            # hack to make sure that events with type BBNTA1:[...] also have an ODP event type
            # this indicates that we need to find a suitable ODP type to use instead
            self.add_triples_bbn_event(type_assignment)
            # unclear why this is done instead of using the old function above
            second_event_type = self.namespace["EVENT"]["Event"]
            ontology_class = event_basename
            print("WARNING: Adding second event type %s to an event mapped to type %s" % (
            str(second_event_type), str(self.namespace["BBNTA1"][ontology_class])))
            optional_fields.append("extra_event_type")
            var_mappings["extra_ontology_class"] = second_event_type
        self.create_triples(
            "event-grounding",
            optional_fields,
            var_mappings=var_mappings
        )

    def create_triples_for_icm_factor_grounding(self,instance_id,kb_causal_factor):
        icm_factor_type = kb_causal_factor.factor_class
        relevance = kb_causal_factor.relevance
        trend = kb_causal_factor.trend
        magnitude = kb_causal_factor.magnitude
        factor_id = kb_causal_factor.id
        self.create_triples("icm-factor-grounding",[],var_mappings={
            "instance":instance_id,
            "factor_id":self.namespace["BBNTA1"][factor_id],
            "magnitude":Literal(format(magnitude, '0.2f'), datatype = XSD.decimal),
            "factor_type":URIRef(icm_factor_type),
            "relevance":Literal(format(relevance, '0.2f'), datatype = XSD.decimal),
            "trend": self.config["mappings"]["icm-property"][trend]
        })

    def create_triples_for_event_arg_time(self,kb_event,event_type,kb_event_mention,role_type,args_for_role):
        kb_document = kb_event.get_document()
        document_date = None
        if "date_created" in kb_document.properties and kb_document.properties["date_created"] != "UNKNOWN":
            document_date = kb_document.properties["date_created"]
        for kb_argument,score in args_for_role:
            assert isinstance(kb_argument, KBValueMention)
            mention_text = kb_argument.value_mention_original_text
            optional_fields = []
            time_text = Literal(re.sub("\n", " ", mention_text), datatype=XSD.string)
            var_mappings = {
                "instance":self.get_event_instance_id(kb_event,event_type)
            }
            var_mappings["time_text"] = time_text
            optional_fields.append("time_text")

            if kb_argument.normalized_date is not None:
                earliestStartTime, earliestEndTime, latestStartTime, latestEndTime\
                    = self.time_matcher.match_time(kb_argument.normalized_date, kb_argument.value_mention_text, document_date)

                if earliestStartTime is not None:
                    var_mappings["earliest_possible_start_time"] = Literal(
                        earliestStartTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                    optional_fields.append("earliest_start_time")

                if earliestEndTime is not None:
                    var_mappings["earliest_possible_end_time"] = Literal(
                        earliestEndTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                    optional_fields.append("earliest_end_time")

                if latestStartTime is not None:
                    var_mappings["latest_possible_start_time"] = Literal(
                        latestStartTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                    optional_fields.append("latest_start_time")

                if latestEndTime is not None:
                    var_mappings["latest_possible_end_time"] = Literal(
                        latestEndTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                    optional_fields.append("latest_end_time")

            logger.debug(self.get_info_kb_value_mention_str(kb_argument))
            self.create_triples(
                "event-arg",
                optional_fields,
                var_mappings
            )
    def create_triples_for_event_arg_location(self,kb_event,event_type,kb_event_mention,role_type,args_for_role):

        predicate_mappings = self.config["mappings"]["event-role"]["default"][role_type]
        [namespace_name, ontology_class] = predicate_mappings["default"].split(":")
        mpred = self.namespace[namespace_name][ontology_class]

        shrinked_event_type = event_type.split("#")[-1]

        for role_idx,(kb_argument,score) in enumerate(args_for_role):
            kb_entity = self.kb_mention_to_kb_entity[kb_argument]
            arg_instance = self.get_entity_ontology_object(kb_entity)
            self.create_triples(
                "event-arg-location-with-location-details",
                [],
                {
                    "instance":self.get_event_instance_id(kb_event,event_type),
                    "entity_instance":arg_instance,
                    "location_details_id":self.namespace["BBNTA1"]["LocationDetails-{}-{}-{}-{}".format(kb_event.id,shrinked_event_type,role_type,role_idx)],
                    "confidence":Literal(format(score, '0.2f'), datatype = XSD.decimal),
                    "pred": mpred
                }
            )

    def create_triples_for_event_arg_other(self,kb_event,event_type,kb_event_mention,role_type,args_for_role):
        predicate_mappings = self.config["mappings"]["event-role"]["default"][role_type]

        for kb_argument,score in args_for_role:
            if isinstance(kb_argument,KBMention):
                instance_argument_as_entity = self.kb_mention_to_kb_entity[kb_argument]
                arg_instance = self.get_entity_ontology_object(instance_argument_as_entity)

                if instance_argument_as_entity is not None:
                    # argument will be linked in RDF directly as the entity, rather than an intermediate object
                    ace_entity_type_with_subtype = instance_argument_as_entity.get_best_entity_type()
                    ace_entity_type = ace_entity_type_with_subtype.split(".")[0]
                    if ace_entity_type_with_subtype in predicate_mappings or ace_entity_type in predicate_mappings:
                        # there is a listed override for the predicate for the entity type
                        if ace_entity_type_with_subtype in predicate_mappings:
                            # look at the more specific type first
                            [namespace_name, ontology_class] = predicate_mappings[
                                ace_entity_type_with_subtype].split(":")
                        else:
                            [namespace_name, ontology_class] = predicate_mappings[ace_entity_type].split(":")
                    else:
                        # there is no listed override for the entity type, so just use the default predicate
                        [namespace_name, ontology_class] = predicate_mappings["default"].split(":")
                else:
                    # argument will be linked in RDF as an intermediate object, so just use the default predicate
                    [namespace_name, ontology_class] = predicate_mappings["default"].split(":")
                mpred = self.namespace[namespace_name][ontology_class]
                event_instance = self.get_event_instance_id(kb_event,event_type)

                # Discard triples that violate domain/range constraints
                if not self.check_subclass_rules(
                        event_instance, mpred, arg_instance):
                    print('dropping: {}, {}, {}'.format(event_instance, mpred, arg_instance))
                    continue

                # create a triple for argument attachment
                self.create_triples(
                    "event-arg-instance",
                    [],
                    var_mappings={
                        "instance": event_instance,
                        "pred": mpred,
                        "arg_instance": arg_instance
                    }
                )
            elif isinstance(kb_argument,KBValueMention):
                # Looking for original implementation here
                # http://e-gitlab.bbn.com/text-group/Hume/blob/R2020_04_22/src/python/knowledge_base/serializers/rdf_serializer.py#L985
                # It was not handeled. Skipping
                print("DROPPING {} {} {}".format(kb_event_mention.trigger, role_type, kb_argument.value_mention_text))

            else:
                raise NotImplemented("Unhandeled argument type {}".format(type(kb_argument)))

    def get_event_instance_id(self,kb_event,event_type):
        shrinked_event_type = event_type.split("#")[-1]
        return self.namespace["BBNTA1"]["{}-{}".format(kb_event.id,shrinked_event_type)]



    def create_triples_from_event(self, kb_event):

        kb_document = kb_event.get_document()
        docId = kb_document.id



        for kb_event_mention in kb_event.event_mentions:
            # Handle span
            # create a span and link it to the event
            # prefer to use the trigger, but use the snippet if there is no trigger
            if kb_event_mention.trigger is not None:
                event_span_text = kb_event_mention.trigger_original_text
                event_span_start = kb_event_mention.trigger_start
                event_span_end = kb_event_mention.trigger_end
            else:
                snippet = kb_event_mention.snippet
                event_span_text = snippet[0]
                event_span_start = snippet[1]
                event_span_end = snippet[2]

            if (event_span_start, event_span_end, docId) in self.span_and_docid_to_id:
                spanID = self.span_and_docid_to_id[(event_span_start, event_span_end, docId)]
            else:
                spanID = SharedIDManager.get_in_document_id("Span", docId)
                self.span_and_docid_to_id[(event_span_start, event_span_end, docId)] = spanID

            span_var_mappings = {
                "spanInstance": self.namespace["BBNTA1"][spanID],
                "startOffset": Literal(self.adjust_offset(event_span_start, kb_event_mention.document),
                                       datatype=XSD.long),
                "textLength": Literal(event_span_end - event_span_start + 1,
                                      datatype=XSD.long),
                "text": Literal(re.sub("\n", " ", event_span_text), datatype=XSD.string),
                "docInstance": self.get_causeex_docid(kb_document),
                "sentenceInstance": self.namespace["BBNTA1"][kb_event_mention.sentence.id],
            }

            span_optional_fields = []

            trigger_words = None
            if kb_event_mention.trigger_original_text:
                trigger_words = kb_event_mention.trigger_original_text
            elif kb_event_mention.triggering_phrase:
                trigger_words = kb_event_mention.triggering_phrase
            elif kb_event_mention.trigger:
                trigger_words = kb_event_mention.trigger
            elif kb_event_mention.proposition_infos and len(kb_event_mention.proposition_infos) > 0:
                trigger_words = kb_event_mention.proposition_infos[0][0]
            if trigger_words:
                span_var_mappings["triggerWords"] = Literal(trigger_words.replace("\t"," ").replace("\n"," "), datatype=XSD.string)
                span_optional_fields.append("trigger_words")

            if "pattern_id" in kb_event_mention.properties:
                span_var_mappings["pattern_id"] = Literal(re.sub("\n", " ", kb_event_mention.properties["pattern_id"]),
                                                          datatype=XSD.string)
                span_optional_fields.append("pattern_id")

            self.create_triples(
                "span",
                span_optional_fields,
                var_mappings=span_var_mappings
            )

            # Handle event type
            for event_type,confidence in kb_event_mention.external_ontology_sources:
                add_generic_genericity = False
                type_assignment = URIRef(event_type)
                add_generic_genericity = (add_generic_genericity or type_assignment.endswith("#Factor"))
                event_instance_id = self.get_event_instance_id(kb_event,event_type)
                self.create_triples_for_event_grounding(event_instance_id,event_type,kb_event_mention.event_confidence)

                # Handle ICM factor type
                for kb_causal_factor in kb_event_mention.causal_factors:
                    self.create_triples_for_icm_factor_grounding(event_instance_id,kb_causal_factor)

                marked_up_sentence = get_marked_up_string_for_event(kb_event)
                var_mappings = {
                    "instance": event_instance_id,
                    "marked_sentence":Literal(re.sub("\n", " ", marked_up_sentence), datatype=XSD.string),
                    "spanInstance":self.namespace["BBNTA1"][spanID],
                    "docInstance":self.get_causeex_docid(kb_document)
                }
                optional_fields = []

                if add_generic_genericity:
                     optional_fields.append("genericity")
                     var_mappings["genericity"] = self.namespace["EVENT"]["Generic"]
                if kb_event.properties is not None:
                    event_property_fields = ["tense", "modality"]
                    if not add_generic_genericity:
                        event_property_fields.append("genericity")
                    for field in event_property_fields:
                        if field in kb_event.properties:
                            value = kb_event.properties[field]
                            if value not in (
                                    "Unspecified", "unavailable"):
                                optional_fields.append(field)
                                var_mappings[field] = self.config["mappings"]["event-property"][
                                    kb_event.properties[field]]
                    field = "polarity"
                    value = kb_event.properties[field]
                    optional_fields.append(field)
                    var_mappings[field] = self.config["mappings"]["general-concepts-property"][value]
                field = "trend"
                value = kb_event_mention.properties["direction_of_change"]
                optional_fields.append(field)
                var_mappings[field] = self.config["mappings"]["icm-property"][value]

                if kb_event_mention.has_topic is not None:
                    # How does this work in an event_mention -> event context?
                    # topic_event_id = self.kb_event_mention_to_kb_event[kb_event_mention.has_topic].id
                    for rdf_event_id in self.kb_event_to_rdf_event_ids[self.kb.evid_to_kb_event]:
                        self.create_triples(
                            "event_topic",
                            [],
                            var_mappings={
                                "instance":event_instance_id,
                                "topic_event_instance":rdf_event_id
                            }
                        )
                self.event_count += 1
                self.create_triples(
                    "event",
                    optional_fields,
                    var_mappings=var_mappings
                )
                for kb_arg_role in kb_event_mention.arguments:
                    args_for_role = kb_event_mention.arguments[kb_arg_role]
                    if kb_arg_role in {"has_time","has_start_time","has_end_time"}:
                        args_for_role = [args_for_role[0]] # TODO: Remove this hack and implement an intelligent way to combine multiple conflicting time arguments
                        self.create_triples_for_event_arg_time(kb_event,event_type,kb_event_mention,kb_arg_role,args_for_role)
                    elif kb_arg_role in {"has_location","has_origin_location","has_destination_location","has_intermediate_location"}:
                        self.create_triples_for_event_arg_location(kb_event,event_type,kb_event_mention,kb_arg_role,args_for_role)
                    else:
                        self.create_triples_for_event_arg_other(kb_event,event_type,kb_event_mention,kb_arg_role,args_for_role)



    def get_entity_mention_ontology_type_object(self, kb_mention_type):
        mention_type_mappings = {
            "desc": "NOM",
            "name": "NAM",
            "pron": "PRO",
            "nest": "NAM",
            "none": "NOM",
            "part": "NOM",
            "appo": "NOM",
            "list": "NOM"
        }
        if kb_mention_type in mention_type_mappings:
            return self.namespace["DATAPROV"][mention_type_mappings[kb_mention_type]]
        else:
            # default
            return self.namespace["DATAPROV"]["NOM"]

    def read_file_lines(self, filepath):
        with open(filepath) as fp:
            lines = fp.readlines()
        lines = [line.rstrip() for line in lines] # strip trailing line endings
        lines = [line for line in lines if len(line) > 0] # filter out empty lines
        return lines

    def read_config(self, filepath):
        with open(filepath) as fp:
            config = json.load(fp)
        return config

    def read_namespaces(self):
        for namespace, URI in self.config.get('namespace', {}).items():
            self.namespace[namespace] = Namespace(URI)

    def read_whitelist(self):
        whitelists_dirpath = os.path.dirname(os.path.realpath(__file__)) + "/../data_files/WhiteLists"
        self.whitelist = []
        for whitelists_file in os.listdir(whitelists_dirpath):
            self.whitelist.extend(self.read_file_lines(whitelists_dirpath + "/" + whitelists_file))

    def add_triples_seed_description(self, author, seed_milestone, seed_type, seed_version, time_completed):
        self.create_triples(
            "seed",
            [],
            var_mappings={
                "author": Literal(author.replace("\t"," ").replace("\n"," "), datatype=XSD.string),
                "instance": self.namespace["BBNTA1"]["Seed-" + datetime.now().strftime("%Y%m%d")],
                "seed_milestone": Literal(seed_milestone, datatype=XSD.string),
                "seed_type": Literal(seed_type, datatype=XSD.string),
                "seed_version": Literal(seed_version, datatype=XSD.string),
                "time_completed": Literal(time_completed, datatype=XSD.dateTime)
            }
        )

    def add_triples_documents_and_sentence_spans(self):
        # Generate documents and sentence spans
        seen_uuids = set()
        for docid in self.kb.docid_to_kb_document:
            kb_document = self.kb.docid_to_kb_document.get(docid)

            for kb_sentence in kb_document.sentences:
                sentenceId = kb_sentence.id
                self.create_triples(
                    "document-sentence",
                    [],
                    var_mappings={
                        "docInstance": self.get_causeex_docid(kb_document),
                        "sentenceInstance": self.namespace["BBNTA1"][sentenceId],
                        "sentenceCharOffset": Literal(self.adjust_offset(kb_sentence.start_offset, kb_document), datatype=XSD.long),
                        "sentenceCharLength": Literal(kb_sentence.end_offset - kb_sentence.start_offset + 1,
                                                      datatype=XSD.long),
                        "sentenceTextValue": Literal(re.sub("\n", " ", kb_sentence.original_text), datatype=XSD.string)
                    }
                )

            # Get original document triples from cdr file
            # How can we import triples from cdr into self.graph?

            # Multiple docs in the KB may correspond to a single 
            # CauseEx doc/UUID, so make sure we only output
            # the metadata once
            if kb_document.properties["uuid"] in seen_uuids:
                continue
            seen_uuids.add(kb_document.properties["uuid"])

            document_properties = kb_document.properties
            var_mappings = {
                "instance": self.get_causeex_docid(kb_document),
                "credibility": Literal(document_properties["credibility"], datatype=XSD.float)
            }

            optional_fields = []
            self.create_triples("documents", optional_fields, var_mappings=var_mappings)

            original_cdr_file = document_properties["source"]
            if os.path.exists(original_cdr_file):
                cdr_stream = codecs.open(original_cdr_file, 'r', encoding='utf8')
                contents = cdr_stream.read()
                cdr_stream.close()
                json_obj = json.loads(contents)
                triples_string = json_obj["extracted_ntriples"]
                individual_lines = triples_string.split("\n")
                for line in individual_lines:
                    line = line.replace("http://www.ontologyrepository.com/CommonCoreOntologies/WebPage>", "http://ontology.causeex.com/ontology/odps/Event#WebPage>") 
                    line = line.replace("DataProvenance#description>", "GeneralConcepts#description>") 
                    # Sanity check on triples from cdr
                    if line.count(">") != line.count("<"):
                        print("Skipping metadata triple from " + kb_document.id + " due to differing number of brackets")
                        continue
                    self.triples_from_cdr += line
                    self.triples_from_cdr += "\n"

    def create_triples(self, triples_type, optional_fields, var_mappings=None, triples_domain="template"):
        # "VAR" is a special namespace name indicating that we should use the RDF object in the given mappings (likely a literal)
        #   rather than constructing an RDF object using the namespace name and non-mapped value name, as would normally
        #   be done.
        if var_mappings is None:
            var_mappings = dict()

        for tripple_mapping in self.config[triples_domain][triples_type]["default"]:
            self.add_single_triple_to_graph(tripple_mapping, var_mappings)

        if "optional" in self.config[triples_domain][triples_type]:
            for field, tripple_mapping_list in self.config[triples_domain][triples_type]["optional"].items():
                if field in optional_fields:
                    for tripple_mapping in tripple_mapping_list:
                        self.add_single_triple_to_graph(tripple_mapping, var_mappings)

    def add_single_triple_to_graph(self, tripple_mapping, var_mappings):
        [subject_namespace_name, subject_value_name] = tripple_mapping["s"].split(":")
        if (subject_namespace_name == "VAR"):
            msubj = var_mappings[subject_value_name]
        else:
            msubj = self.namespace[subject_namespace_name][subject_value_name]
        [predicate_namespace_name, predicate_value_name] = tripple_mapping["p"].split(":")
        if (predicate_namespace_name == "VAR"):
            mpred = var_mappings[predicate_value_name]
        else:
            mpred = self.namespace[predicate_namespace_name][predicate_value_name]
        [object_namespace_name, object_value_name] = tripple_mapping["o"].split(":")
        if (object_namespace_name == "VAR"):
            mobj = var_mappings[object_value_name]
            # look up namespace and value_name one level deeper
            if mobj.count(':') == 1:  # timex expressions will contain ":"
                [namespace_name, value_name] = mobj.split(":")
                if namespace_name in self.namespace:
                    mobj = self.namespace[namespace_name][value_name]
        else:
            mobj = self.namespace[object_namespace_name][object_value_name]
        
        self.graph.add((msubj, mpred, mobj))

    def adjust_offset(self, sgm_offset, kb_document):
        return sgm_offset + kb_document.properties["offset"]
    
    def get_causeex_docid(self, kb_document):
        return self.namespace["DOCSOURCE"][kb_document.properties["uuid"]]

    # START Modifications by @criley/BBN 2018
    # START Additions by Charles River Analytics 2018
    # Process the "inputs" section of self.structured_kb
    def serialize_structured_inputs(self):

        def build_one_location(location_obj):
            """:type location_obj: EntityData"""
            if not location_obj:
                return
            elif location_obj.mar_entity_type is not None:
                self.build_mar_entity(location_obj.get_uri(),
                                      location_obj.mar_entity_type)
            else:
                if not location_obj.is_country:
                    self.build_location(location_obj.get_uri(),
                                        location_obj.label)

        # This'll make output easier to understand
        for name, uri in self.namespace.items():
            self.graph.bind(name, uri)

        inputs_length = len(self.kb.structured_documents)

        for input_count, input_document in \
                enumerate(self.kb.structured_documents):
            print("RDFSerializer creating triples from StructuredInput (" + \
                  str(input_count) + "/" + str(inputs_length) + ")")
            self.structured_input_file_count += 1

            for worksheet in input_document.sheets:
                self.structured_worksheet_count += 1

                for series in worksheet.time_series:
                    build_one_location(series.location)

                    # todo repeat this task everywhere entities appear
                    series.location.serialize(self.graph)

                    self.structured_time_series_count += 1

                for entity in worksheet.entities:
                    build_one_location(entity)
                    self.structured_entity_count += 1

                for event in worksheet.events:
                    build_one_location(event.event_location)
                    self.structured_event_count += 1

            input_document.serialize(self.graph)

    @staticmethod
    def check_tags_for_val(value, coltag, rowtag):
        if value in coltag:
            return coltag[value]
        elif value in rowtag:
            return rowtag[value]
        else:
            return None

    # Process the "relationships" section of self.structured_kb
    def serialize_structured_relationships(self):

        num_relationships = len(self.kb.structured_relationships)
        if num_relationships == 0:
            return

        for count, causal_relation in enumerate(
                self.kb.structured_relationships):
            if count % 1000 == 0:
                print("RDFSerializer creating triples from " \
                      "StructuredRelationship (" + \
                      str(count) + "/" + str(num_relationships) + ")")
            self.structured_relationship_count += 1
            # write to graph
            causal_relation.serialize(self.graph)

    def build_location(self, location_uri, label):
        var_mappings = {
            "instance": location_uri,
            "label": Literal(label, datatype=XSD.string)
        }
        self.create_triples("extracted_location",
                            optional_fields=[], var_mappings=var_mappings)

    # TODO maybe remove this hack?
    def build_mar_entity(self, entity_uri, entity_type):
        var_mappings = {
            "instance": entity_uri,
            "location_type": URIRef(entity_type)
        }
        self.create_triples("extracted_MAR_location",
                            optional_fields=[], var_mappings=var_mappings)

    # FINISH Additions by Charles River Analytics 2018
    # FINISH Modifications by @criley/BBN 2018

    # Run some SPARQL queries over the graph to verify things worked as intended
    # The SPARQL queries here come from https://git.causeex.com/ontology/
    # ontology/blob/master/docs/Queries/IntegrityCheckQueries.md
    def verify_graph(self):
        print("Running verification SPARQL queries")

        # Bind required namespaces
        self.graph.bind('owl', 'http://www.w3.org/2002/07/owl#')
        self.graph.bind('actor', 'http://ontology.causeex.com/ontology/odps/Actor#')
        self.graph.bind('meas', 'http://ontology.causeex.com/ontology/odps/TimeSeriesAndMeasurements#')

        # ObjectProperty references that are not URLs
        print("    ObjectProperty references that are not URLs")
        results = self.graph.query("""select ?s ?p ?o where { ?s ?p ?o . ?p a owl:ObjectProperty . FILTER (!isIRI(?o))}""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # DatatypeProperty references that are URLs
        print("    DatatypeProperty references that are URLs")
        results = self.graph.query("""select ?s ?p ?o where { ?s ?p ?o . ?p a owl:DatatypeProperty . FILTER isIRI(?o)}""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Individuals classified as types that are not defined
        print("    Individuals classified as types that are not defined")
        results = self.graph.query("""select (COUNT(*) as ?count) ?type where { ?s a ?type . FILTER (!regex(str(?type), '/owl#')) . FILTER (!regex(str(?type), 'rdf-s')) . FILTER NOT EXISTS { ?type a owl:Class } } GROUP BY ?type""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "subject" individuals with only 1 type, 1 class referenced in the predicate's domain
        print("    S-P-O query for subject individuals with only 1 type, 1 class referenced in the predicate's domain")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?sClass ?domainClass where { ?s ?p ?o . FILTER ( ?p != rdf:type && ?p != rdfs:subClassOf ) . ?p rdfs:domain ?domainClass . FILTER (!isBlank(?domainClass)) . ?s a ?sClass . MINUS { ?s ?p ?o . ?s a ?sClass . ?s a ?anotherSClass . FILTER ( ?anotherSClass != ?sClass ) } . MINUS { ?s ?p ?o . ?p rdfs:domain ?domainClass . ?s a ?sClass . OPTIONAL { ?sClass rdfs:subClassOf ?sSuperClass } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf ?sSuper2Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper3Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper4Class } . FILTER ( ?sClass = ?domainClass || ?sSuperClass = ?domainClass || ?sSuper2Class = ?domainClass || ?sSuper3Class = ?domainClass || ?sSuper4Class = ?domainClass ) } } GROUP BY ?p ?sClass ?domainClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "subject" individuals with multiple types, 1 class referenced in the predicate's domain
        print("    S-P-O query for subject individuals with multiple types, 1 class referenced in the predicate's domain")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?sClass ?domainClass where { ?s ?p ?o . filter ( ?p != rdf:type && ?p != rdfs:subClassOf ) . ?p rdfs:domain ?domainClass . filter (!isBlank(?domainClass)) . ?s a ?sClass . ?s a ?anotherSClass . filter ( ?anotherSClass != ?sClass ) . MINUS { ?s ?p ?o . ?p rdfs:domain ?domainClass . ?s a ?sClass . ?s a ?anotherSClass1 . filter ( ?anotherSClass1 != ?sClass ) . OPTIONAL { ?sClass rdfs:subClassOf ?sSuperClass } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf ?sSuper2Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper3Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper4Class } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf ?anotherSSuperClass } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf/rdfs:subClassOf ?anotherSSuper2Class } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherSSuper3Class } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherSSuper4Class } . filter ( ?sClass = ?domainClass || ?anotherSClass1 = ?domainClass || ?sSuperClass = ?domainClass || ?anotherSSuperClass = ?domainClass || ?sSuper2Class = ?domainClass || ?anotherSSuper2Class = ?domainClass || ?sSuper3Class = ?domainClass || ?anotherSSuper3Class = ?domainClass || ?sSuper4Class = ?domainClass || ?anotherSSuper4Class = ?domainClass ) } } GROUP BY ?p ?sClass ?domainClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "subject" individuals with only 1 type, and a union of classes referenced in the predicate's domain
        print("    S-P-O query for subject individuals with only 1 type, and a union of classes referenced in the predicate's domain")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?sClass ?domainClass where { ?s ?p ?o . filter ( ?p != rdf:type && ?p != rdfs:subClassOf ) . ?p rdfs:domain ?blankNode . filter isBlank(?blankNode) . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?domainClass . ?s a ?sClass . MINUS { ?s ?p ?o . ?s a ?sClass . ?s a ?anotherSClass . filter ( ?anotherSClass != ?sClass ) } . MINUS { ?s ?p ?o . ?s a ?sClass . ?p rdfs:domain ?blankNode . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?domainClass . ?list rdf:rest*/rdf:first ?anotherDomainClass . filter ( ?anotherDomainClass != ?domainClass ) . OPTIONAL { ?sClass rdfs:subClassOf ?sSuperClass } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf ?sSuper2Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper3Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper4Class } . filter ( ?sClass = ?domainClass || ?sClass = ?anotherDomainClass || ?sSuperClass = ?domainClass || ?sSuperClass = ?anotherDomainClass || ?sSuper2Class = ?domainClass || ?sSuper2Class = ?anotherDomainClass || ?sSuper3Class = ?domainClass || ?sSuper3Class = ?anotherDomainClass || ?sSuper4Class = ?domainClass || ?sSuper4Class = ?anotherDomainClass ) } } GROUP BY ?p ?sClass ?domainClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "subject" individuals with multiple types, and a union of classes referenced in the predicate's domain
        print("    S-P-O query for subject individuals with multiple types, and a union of classes referenced in the predicate's domain")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?sClass ?domainClass where { ?s ?p ?o . filter ( ?p != rdf:type && ?p != rdfs:subClassOf ) . ?p rdfs:domain ?blankNode . filter isBlank(?blankNode) . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?domainClass . ?s a ?sClass . ?s a ?anotherSClass . filter ( ?anotherSClass != ?sClass ) . MINUS { ?s ?p ?o . ?s a ?sClass . ?s a ?anotherSClass1 . filter ( ?anotherSClass1 != ?sClass ) . ?p rdfs:domain ?blankNode . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?domainClass . ?list rdf:rest*/rdf:first ?anotherDomainClass . filter ( ?anotherDomainClass != ?domainClass ) . OPTIONAL { ?sClass rdfs:subClassOf ?sSuperClass } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf ?sSuper2Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper3Class } . OPTIONAL { ?sClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?sSuper4Class } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf ?anotherSSuperClass } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf/rdfs:subClassOf ?anotherSSuper2Class } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherSSuper3Class } . OPTIONAL { ?anotherSClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherSSuper4Class } . filter ( ?sClass = ?domainClass || ?sClass = ?anotherDomainClass || ?anotherSClass1 = ?domainClass || ?anotherSClass1 = ?anotherDomainClass || ?sSuperClass = ?domainClass || ?sSuperClass = ?anotherDomainClass || ?anotherSSuperClass = ?domainClass || ?anotherSSuperClass = ?anotherDomainClass || ?sSuper2Class = ?domainClass || ?sSuper2Class = ?anotherDomainClass || ?anotherSSuper2Class = ?domainClass || ?anotherSSuper2Class = ?anotherDomainClass || ?sSuper3Class = ?domainClass || ?sSuper3Class = ?anotherDomainClass || ?anotherSSuper3Class = ?domainClass || ?anotherSSuper3Class = ?anotherDomainClass || ?sSuper4Class = ?domainClass || ?sSuper4Class = ?anotherDomainClass || ?anotherSSuper4Class = ?domainClass || ?anotherSSuper4Class = ?anotherDomainClass ) } } GROUP BY ?p ?sClass ?domainClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "object" individuals with only 1 type, 1 class referenced in the predicate's range
        print("    S-P-O query for object individuals with only 1 type, 1 class referenced in the predicate's range")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?oClass ?rangeClass where { ?s ?p ?o . ?p a owl:ObjectProperty . ?p rdfs:range ?rangeClass . filter (!isBlank(?rangeClass)) . ?o a ?oClass . MINUS { ?s ?p ?o . ?p a owl:ObjectProperty . ?o a ?oClass . ?o a ?anotherOClass . filter ( ?anotherOClass != ?oClass ) } . MINUS { ?s ?p ?o . ?p a owl:ObjectProperty . ?p rdfs:range ?rangeClass . ?o a ?oClass . OPTIONAL { ?oClass rdfs:subClassOf ?oSuperClass } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf ?oSuper2Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper3Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper4Class } . filter ( ?oClass = ?rangeClass || ?oSuperClass = ?rangeClass || ?oSuper2Class = ?rangeClass || ?oSuper3Class = ?rangeClass || ?oSuper4Class = ?rangeClass ) } } GROUP BY ?p ?oClass ?rangeClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "object" individuals with multiple types, 1 class referenced in the predicate's range
        print("    S-P-O query for object individuals with multiple types, 1 class referenced in the predicate's range")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?oClass ?rangeClass where { ?s ?p ?o . ?p a owl:ObjectProperty . filter ( (?p != actor:related_country_code) && (!regex(str(?o), 'CAMEO') ) ) . ?p rdfs:range ?rangeClass . filter (!isBlank(?rangeClass)) . ?o a ?oClass . ?o a ?anotherOClass . filter ( ?anotherOClass != ?oClass ) . MINUS { ?s ?p ?o . ?p a owl:ObjectProperty . ?p rdfs:range ?rangeClass . filter ( (?p != actor:related_country_code) && (!regex(str(?o), 'CAMEO') ) ) . ?o a ?oClass . ?o a ?anotherOClass1 . filter ( ?anotherOClass1 != ?oClass ) . OPTIONAL { ?oClass rdfs:subClassOf ?oSuperClass } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf ?oSuper2Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper3Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper4Class } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf ?anotherOSuperClass } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf/rdfs:subClassOf ?anotherOSuper2Class } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherOSuper3Class } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherOSuper4Class } . filter ( ?oClass = ?rangeClass || ?anotherOClass1 = ?rangeClass || ?oSuperClass = ?rangeClass || ?anotherOSuperClass = ?rangeClass || ?oSuper2Class = ?rangeClass || ?anotherOSuper2Class = ?rangeClass || ?oSuper3Class = ?rangeClass || ?anotherOSuper3Class = ?rangeClass || ?oSuper4Class = ?rangeClass || ?anotherOSuper4Class = ?rangeClass ) } } GROUP BY ?p ?oClass ?rangeClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "object" individuals with only 1 type, and a union of classes referenced in the predicate's range
        print("    S-P-O query for object individuals with only 1 type, and a union of classes referenced in the predicate's range")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?oClass ?rangeClass where { ?s ?p ?o . ?p a owl:ObjectProperty . ?p rdfs:range ?blankNode . filter isBlank(?blankNode) . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?rangeClass . ?o a ?oClass . MINUS { ?s ?p ?o . ?p a owl:ObjectProperty . ?o a ?oClass . ?o a ?anotherOClass . filter ( ?anotherOClass != ?oClass ) } . MINUS { ?s ?p ?o . ?p a owl:ObjectProperty . ?o a ?oClass . ?p rdfs:range ?blankNode . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?rangeClass . ?list rdf:rest*/rdf:first ?anotherRangeClass . filter ( ?anotherRangeClass != ?rangeClass ) . OPTIONAL { ?oClass rdfs:subClassOf ?oSuperClass } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf ?oSuper2Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper3Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper4Class } . filter ( ?oClass = ?rangeClass || ?oClass = ?anotherRangeClass || ?oSuperClass = ?rangeClass || ?oSuperClass = ?anotherRangeClass || ?oSuper2Class = ?rangeClass || ?oSuper2Class = ?anotherRangeClass || ?oSuper3Class = ?rangeClass || ?oSuper3Class = ?anotherRangeClass || ?oSuper4Class = ?rangeClass || ?oSuper4Class = ?anotherRangeClass ) } } GROUP BY ?p ?oClass ?rangeClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Subject-Predicate-Object query for "object" individuals with multiple types, and a union of classes referenced in the predicate's range
        print("    S-P-O query for object individuals with multiple types, and a union of classes referenced in the predicate's range")
        results = self.graph.query("""select (COUNT(*) as ?count) ?p ?oClass ?rangeClass where { ?s ?p ?o . ?p a owl:ObjectProperty . ?p rdfs:range ?blankNode . filter isBlank(?blankNode) . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?rangeClass . ?o a ?oClass . ?o a ?anotherOClass . filter ( ?anotherOClass != ?oClass ) . MINUS { ?s ?p ?o . ?o a ?oClass . ?o a ?anotherOClass1 . filter ( ?anotherOClass1 != ?oClass ) . ?p rdfs:range ?blankNode . ?blankNode owl:unionOf ?list . ?list rdf:rest*/rdf:first ?rangeClass . ?list rdf:rest*/rdf:first ?anotherRangeClass . filter ( ?anotherRangeClass != ?rangeClass ) . OPTIONAL { ?oClass rdfs:subClassOf ?oSuperClass } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf ?oSuper2Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper3Class } . OPTIONAL { ?oClass rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?oSuper4Class } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf ?anotherOSuperClass } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf/rdfs:subClassOf ?anotherOSuper2Class } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherOSuper3Class } . OPTIONAL { ?anotherOClass1 rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf/rdfs:subClassOf ?anotherOSuper4Class } . filter ( ?oClass = ?rangeClass || ?oClass = ?anotherRangeClass || ?anotherOClass1 = ?rangeClass || ?anotherOClass1 = ?anotherRangeClass || ?oSuperClass = ?rangeClass || ?oSuperClass = ?anotherRangeClass || ?anotherOSuperClass = ?rangeClass || ?anotherOSuperClass = ?anotherRangeClass || ?oSuper2Class = ?rangeClass || ?oSuper2Class = ?anotherRangeClass || ?anotherOSuper2Class = ?rangeClass || ?anotherOSuper2Class = ?anotherRangeClass || ?oSuper3Class = ?rangeClass || ?oSuper3Class = ?anotherRangeClass || ?anotherOSuper3Class = ?rangeClass || ?anotherOSuper3Class = ?anotherRangeClass || ?oSuper4Class = ?rangeClass || ?oSuper4Class = ?anotherRangeClass || ?anotherOSuper4Class = ?rangeClass || ?anotherOSuper4Class = ?anotherRangeClass ) } } GROUP BY ?p ?oClass ?rangeClass""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Individuals that are classified by other individuals or by undefined types
        print("    Individuals that are classified by other individuals or by undefined types")
        results = self.graph.query("""select (COUNT(*) as ?count) ?s ?type where { ?s a ?type . FILTER (!regex(str(?type), '/owl#')) . FILTER (!regex(str(?type), 'rdf-s')) . FILTER NOT EXISTS { ?type a owl:Class } } GROUP BY ?s ?type""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Individuals that are ReportedProperties that do not have a ReportedPropertyType
        print("    Individuals that are ReportedProperties that do not have a ReportedPropertyType")
        results = self.graph.query("""select (COUNT(distinct ?s) as ?count) where { { { ?s a meas:ReportedProperty } UNION { ?s a ?type . ?type rdfs:subClassOf+ meas:ReportedProperty } } FILTER NOT EXISTS { ?s meas:has_property_type ?pt } }""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Individuals that are ReportedValues that do not have a backing ReportedProperty
        print("    Individuals that are ReportedValues that do not have a backing ReportedProperty")
        results = self.graph.query("""select (COUNT(distinct ?s) as ?count) where { ?s a meas:ReportedValue . MINUS { { ?ts a meas:TimeSeries . ?ts meas:has_reported_value ?s . ?ts meas:defined_by ?rp } UNION { ?s meas:defined_by ?rp } } }""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Individuals that are ReportedValues that do not have a timestamp
        print("    Individuals that are ReportedValues that do not have a timestamp")
        results = self.graph.query("""select (COUNT(distinct ?s) as ?count) where { ?s a meas:ReportedValue . MINUS { ?s a meas:ReportedValue . ?s ?p ?o . filter regex(str(?p), '_time') } }""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

        # Individuals that are ReportedValues that do not have a value
        print("    Individuals that are ReportedValues that do not have a value")
        results = self.graph.query("""select (COUNT(distinct ?s) as ?count) where { ?s a meas:ReportedValue . MINUS { ?s a meas:ReportedValue . ?s ?p ?o . filter regex(str(?p), '_value') } }""")
        resultCount = len(results)
        print("        %s results returned" % resultCount)

    def discard_subclass_failures(self):
        missed_failures = defaultdict(int)
        for predicate in self.rules:
            for s, p, o in self.graph.triples((None, URIRef(predicate), None)):
                if not self.check_subclass_rules(s, p, o):
                    self.graph.remove((s, p, o))
                    missed_failures[predicate] += 1
                    print ("REMOVE: {}\t{}\t{}".format(s, p, o))
        if len(missed_failures) > 0:
            print('Discarded triples with bad domain/range which were mistakenly added:')
        for k in sorted(missed_failures.keys()):
            print(missed_failures[k], k)

    def get_canonical_name_from_entity(self, kb_entity):
        if "canonical_mention" in kb_entity.properties:
            canonical_mention = kb_entity.properties["canonical_mention"]
            if canonical_mention.mention_type == "name":
                return canonical_mention.mention_original_head_text
            else:
                return canonical_mention.mention_original_text
        return None

# Typically, we don't run from the command line, we use this class as 
# part of kb_constructor.py run. But if we've run the KBPickleSerializer
# on a KB, we can run the serilization process starting with that 
# pickled KB here.
if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("Usage: " + sys.argv[0] + " mode pickled_kb_file seed_milestone seed_type seed_version output_ttl_file output_nt_file")
        sys.exit(1)

    mode,seed_milestone, seed_type, seed_version, pickled_kb_file, output_ttl_file, output_nt_file = sys.argv[1:]
    with open(pickled_kb_file, "rb") as pickle_stream:
        print("Loading pickle file...")
        kb = pickle.load(pickle_stream)
        print("Done loading. Serializing...")
        rdf_serializer = RDFSerializer()
        rdf_serializer.serialize(kb, mode,seed_milestone, seed_type, seed_version,output_ttl_file, output_nt_file)
        print('Dropped triples for the following subclassing constraints:')
        for k in sorted(rdf_serializer.integrity_counts.keys()):
            print(rdf_serializer.integrity_counts[k], '\t', k)
        print(sum(rdf_serializer.integrity_counts.values()), '\t', 'Total')

