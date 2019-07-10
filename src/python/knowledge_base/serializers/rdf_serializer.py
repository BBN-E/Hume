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
from knowledge_base import KnowledgeBase
from shared_id_manager.shared_id_manager import SharedIDManager
from elements.structured.structured_entity import EntityData
from elements.kb_entity import KBEntity
from resolvers.structured_resolver import ascii_me
from internal_ontology.internal_ontology import InternalOntology

import pickle


class RDFSerializer:

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
        print "RDFSerializer SERIALIZE"

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
            for kb_event_id, kb_event in self.kb.evid_to_kb_event.iteritems():
                for kb_event_mention in kb_event.event_mentions:
                    self.kb_event_mention_to_kb_event[kb_event_mention] = kb_event

            self.add_triples_seed_description(seed_milestone, seed_type, seed_version)
            self.add_triples_documents_and_sentence_spans()
            self.add_triples_entities()
            self.add_triples_events()
            self.add_triples_relations()

            self.add_triples_entity_groups()
            self.add_triples_event_groups()
            self.add_triples_relation_groups()

        # start CRA integration
        elif mode == "STRUCTURED":

            # TODO move serialization steps back into this file/call
            pass
            self.serialize_structured_inputs()
            self.serialize_structured_relationships()
            # end CRA integration

        else:
            print "ERROR: Unknown mode: " + mode
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
        implicitly_whitelisted_namespace_labels = ["BBNTA1", "RDF", "RDFS"]
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
        output_identifier = time.strftime("%Y%m%d-%H%M")
        self.serialize_to_file("nt", output_nt_file, output_identifier)
        self.serialize_to_file("turtle", output_ttl_file, output_identifier)
        
    def serialize_to_file(self, serialization_format, filename, output_identifier):
        filename = "%s-%s.%s" % (filename, output_identifier, serialization_format)
        print "RDFSerializer SERIALIZING TO FILE " + filename
        self.graph.serialize(destination=filename, format=serialization_format)

        # Can we get rid of self.triples_from_cdr and import the triples
        # directly into the graph?
        if serialization_format == "nt" and len(self.triples_from_cdr) > 0:
            o = codecs.open(filename, "a", encoding='utf8')
            o.write(self.triples_from_cdr)
            o.close()

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
        return InternalOntology.camel_to_tokens(string)

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
        self.graph.add(uri_subclassof_event)
        self.graph.add(uri_label)
        self.graph.add(uri_subclassof_event)
        self.odps.add(uri_a_owl_class)
        self.odps.add(uri_comment)
        self.odps.add(uri_label)
        self.odps.add(uri_comment)

    def add_triples_entities(self):
        entity_length = len(self.kb.entid_to_kb_entity)
        count = 0
        for entid, kb_entity in self.kb.entid_to_kb_entity.iteritems():
            if count % 1000 == 0:
                print "RDFSerializer creating triples from KBEntity (" + str(count) + "/" + str(entity_length) + ")"
            count += 1
            self.create_triples_from_entity(kb_entity)

    def add_triples_entity_groups(self):
        entity_group_length = len(self.kb.entgroupid_to_kb_entity_group)
        count = 0
        for entgroupid, kb_entity_group in self.kb.entgroupid_to_kb_entity_group.iteritems():
            if count % 1000 == 0:
                print "RDFSerializer creating triples from KBEntityGroup (" + str(count) + "/" + str(entity_group_length) + ")"
            count += 1
            self.create_triples_from_entity_group(kb_entity_group)

    def add_triples_events(self):
        event_length = len(self.kb.evid_to_kb_event)
        count = 0
        for evid, kb_event in self.kb.evid_to_kb_event.iteritems():
            if count % 1000 == 0:
                print "RDFSerializer creating triples from KBEvent (" + str(count) + "/" + str(event_length) + ")"
            count += 1
            self.create_triples_from_event(kb_event)

    def add_triples_event_groups(self):
        event_group_length = len(self.kb.evgroupid_to_kb_event_group)
        count = 0
        for evgroupid, kb_event_group in self.kb.evgroupid_to_kb_event_group.iteritems():
            if count % 1000 == 0:
                print "RDFSerializer creating triples from KBEventGroup (" + str(count) + "/" + str(
                    event_group_length) + ")"
            count += 1
            self.create_triples_from_event_group(kb_event_group)

    def add_triples_relations(self):
        rel_length = len(self.kb.relid_to_kb_relation)
        count = 0
        for relid, kb_relation in self.kb.relid_to_kb_relation.iteritems():
            if count % 1000 == 0:
                print "RDFSerializer creating triples from KBRelation (" + str(count) + "/" + str(rel_length) + ")"
            count += 1
            if kb_relation.argument_pair_type == "entity-entity":
                self.create_triples_from_entity_relation(kb_relation)
            elif kb_relation.argument_pair_type == "event-event":
                self.create_triples_from_event_relation(kb_relation)

    def add_triples_relation_groups(self):
        relation_group_length = len(self.kb.relgroupid_to_kb_relation_group)
        count = 0
        for relgroupid, kb_relation_group in self.kb.relgroupid_to_kb_relation_group.iteritems():
            if count % 1000 == 0:
                print "RDFSerializer creating triples from KBRelationGroup (" + str(count) + "/" + str(
                    relation_group_length) + ")"
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
        source_entity_ontology_object = self.get_entity_ontology_object(
            self.kb.entid_to_kb_entity[kb_relation.left_argument_id])
        left_entity_id = kb_relation.left_argument_id
        target_entity_ontology_object = self.get_entity_ontology_object(
            self.kb.entid_to_kb_entity[kb_relation.right_argument_id])
        right_entity_id = kb_relation.right_argument_id
        # few cases that flip the argument
        if self.config["mappings"]["entity-relation"][kb_relation.relation_type]["reverse"]:
            tmp = source_entity_ontology_object
            source_entity_ontology_object = target_entity_ontology_object
            target_entity_ontology_object = tmp
            tmp = left_entity_id
            left_entity_id = right_entity_id
            right_entity_id = tmp

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
        if "GPE.Nation" in kb_entity.entity_type_to_confidence and "cameo_country_code" in kb_entity.properties:
            return self.namespace["CAMEOCC"]["CAMEO" + kb_entity.properties["cameo_country_code"].lower()]
        else:
            return self.namespace["BBNTA1"][kb_entity.id]

    def create_currency_rdf_double(self, decimal_value):
        # this is necessary because for some large values like 1000000000000, we would output the literal with scientific notation
        # e.g.:
        # "1e+12"^^<http://www.w3.org/2001/XMLSchema#decimal>
        # whereas we actually need:
        # "1000000000000.00"^^<http://www.w3.org/2001/XMLSchema#double>
        return Literal(format(decimal_value, '0.2f'), datatype=XSD.double)

    def create_triples_from_event_relation(self, kb_relation):
        relation_type = kb_relation.relation_type
        source_event = kb_relation.left_argument_id
        target_event = kb_relation.right_argument_id

        if "default_relationship" in self.config["mappings"]["event-causal-relation"][relation_type]:
            # this isn't really a causal relation - but it is something from which we want to create a regular relation
            # with the two events as the arguments
            [namespace_name, ontology_class] = self.config["mappings"]["event-causal-relation"][relation_type][
                "default_relationship"].split(":")
            relation_ontology_class = self.namespace[namespace_name][ontology_class]
            relation_instance_id = kb_relation.id

            if relation_type != "Before-After":
                self.text_causal_assertion_count += 1

            self.create_triples(
                "event-relation",
                [],
                var_mappings={
                    "instance": self.namespace["BBNTA1"][relation_instance_id],
                    "ontology_class": relation_ontology_class,
                    "left_arg": self.namespace["BBNTA1"][source_event],
                    "right_arg": self.namespace["BBNTA1"][target_event],
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
            left_arg = self.namespace["BBNTA1"][source_event]

            [namespace_name, ontology_class] = self.config["mappings"]["event-causal-relation"][relation_type][
                "right_predicate"].split(":")
            right_pred = self.namespace[namespace_name][ontology_class]
            right_arg = self.namespace["BBNTA1"][target_event]

            self.create_triples(
                "event-causal-relation",
                [],
                var_mappings={
                    "instance": self.namespace["BBNTA1"][relation_instance_id],
                    "ontology_class": relation_ontology_class,
                    "left_pred": left_pred,
                    "left_arg": left_arg,
                    "right_pred": right_pred,
                    "right_arg": right_arg,
                    "confidence": Literal(format(kb_relation.confidence, '0.2f'), datatype = XSD.decimal)
                }
            )

            for kb_relation_mention in kb_relation.relation_mentions:
                for kb_sentence in [kb_relation_mention.left_mention.sentence, kb_relation_mention.right_mention.sentence]:
                    self.create_triples(
                        "source-sentence",
                        [],
                        var_mappings={
                            "instance": self.namespace["BBNTA1"][relation_instance_id],
                            "sentenceSpanInstance": self.namespace["BBNTA1"][kb_sentence.id]
                        }
                    )

    def create_triples_from_entity_group(self, kb_entity_group):

        if len(kb_entity_group.members) > 1:  # don't process singletons
            # RDF URI for this entity group instance:
            entity_group_instance = self.namespace["BBNTA1"][kb_entity_group.id]
            var_mappings = {"instance": entity_group_instance}
            optional_fields = set([])

            # add canonical name
            if kb_entity_group.canonical_name is not None:
                optional_fields.add("canonical_name")
                var_mappings["canonical_name"] = Literal(kb_entity_group.canonical_name, datatype=XSD.string)

            # serialize group metadata
            self.create_triples("entity_group", optional_fields, var_mappings=var_mappings)

            # serialize group membership definitions
            for kb_entity in kb_entity_group.members:

                entity_type, entity_subtype = kb_entity.get_best_entity_type().split(".")
                namespace_name, ontology_class = self.config["mappings"]["entity"][entity_type]["sub_types"][entity_subtype].split(":")
                var_mappings["ontology_class"] = self.namespace[namespace_name][ontology_class]
                var_mappings["member"] = self.get_entity_ontology_object(kb_entity)  # may be more complex than graph lookup

                self.create_triples("entity_group-unification", [], var_mappings=var_mappings)

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
            if (entity_type in self.config["mappings"]["entity_secondary_type"] and
                entity_subtype in self.config["mappings"]["entity_secondary_type"][entity_type]):
                [namespace_name, ontology_class] = self.config["mappings"]["entity_secondary_type"][
                    entity_type][entity_subtype].split(":")
                var_mappings["secondary_ontology_class"] = self.namespace[namespace_name][ontology_class]
                optional_fields.add("additional_entity_type")

        # add canonical name
        if kb_entity.canonical_name is not None:
            optional_fields.add("canonical_name")
            var_mappings["canonical_name"] = Literal(kb_entity.canonical_name, datatype=XSD.string)

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
        self.create_triples("entity", optional_fields, var_mappings=var_mappings)

        for kb_mention in kb_entity.mentions:
            kb_document = kb_mention.document
            docId = kb_document.id

            if (kb_mention.start_char, kb_mention.end_char, docId) in self.span_and_docid_to_id:
                spanID = self.span_and_docid_to_id[(kb_mention.start_char, kb_mention.end_char, docId)]
            else:
                spanID = SharedIDManager.get_in_document_id("Span", docId)
                self.span_and_docid_to_id[(kb_mention.start_char, kb_mention.end_char, docId)] = spanID

            if (kb_mention.head_start_char, kb_mention.head_end_char, kb_mention.mention_type, docId) in self.mention_span_and_docid_to_id:
                mentionSpanID = self.mention_span_and_docid_to_id[(kb_mention.head_start_char, kb_mention.head_end_char, kb_mention.mention_type, docId)]
            else:
                mentionSpanID = SharedIDManager.get_in_document_id("MentionSpan", docId)
                self.mention_span_and_docid_to_id[(kb_mention.head_start_char, kb_mention.head_end_char, kb_mention.mention_type, docId)] = mentionSpanID

            self.create_triples(
                "span",
                [],
                var_mappings={
                    "spanInstance": self.namespace["BBNTA1"][spanID],
                    "startOffset": Literal(self.adjust_offset(kb_mention.start_char, kb_mention.document), datatype=XSD.long),
                    "textLength": Literal(kb_mention.end_char - kb_mention.start_char + 1, datatype=XSD.long),
                    "text": Literal(re.sub("\n", " ", kb_mention.mention_text), datatype=XSD.string),
                    "docInstance": self.get_causeex_docid(kb_document),
                    "sentenceInstance": self.namespace["BBNTA1"][kb_mention.sentence.id]
                }
            )
            self.create_triples(
                "entity-mention-span",
                [],
                var_mappings={
                    "mentionSpanInstance": self.namespace["BBNTA1"][mentionSpanID],
                    "startOffset": Literal(self.adjust_offset(kb_mention.head_start_char, kb_mention.document), datatype=XSD.long),
                    "textLength": Literal(kb_mention.head_end_char - kb_mention.head_start_char + 1, datatype=XSD.long),
                    "mention_text": Literal(re.sub("\n", " ", kb_mention.mention_head_text), datatype=XSD.string),
                    "mention_type": self.get_entity_mention_ontology_type_object(kb_mention.mention_type),
                    "docInstance": self.get_causeex_docid(kb_document),
                    "sentenceInstance": self.namespace["BBNTA1"][kb_mention.sentence.id],
                    "spanInstance": self.namespace["BBNTA1"][spanID],
                    "entityInstance": var_mappings["instance"]
                }
            )

    def _grounded_event_type_is_bbnta1(self, event_type_string):
        bbn_ns = str(self.config.get("namespace", {}).get("BBNTA1", "_INVALID"))
        return event_type_string.startswith(bbn_ns)

    def _event_type_is_grounded(self, event_type_string):
        evt_ns = str(self.config.get("namespace", {}).get("EVENT", "_INVALID"))
        return (event_type_string.startswith(evt_ns) 
                or self._grounded_event_type_is_bbnta1)

    def create_triples_from_event_group(self, kb_event_group):

        if len(kb_event_group.members) > 1:  # don't process singletons
            # RDF URI for this event group instance:
            event_group_instance = self.namespace["BBNTA1"][kb_event_group.id]
            var_mappings = {"instance": event_group_instance}

            # serialize group membership definitions
            for kb_event in kb_event_group.members:

                event_type = kb_event.event_type_to_confidence.keys()[0]
                
                # already grounded?
                if self._event_type_is_grounded(event_type):
                    var_mappings["ontology_class"] = URIRef(event_type)
                    
                # not already grounded.
                else:
                    if event_type in self.config["mappings"]["event"]:
                        [namespace_name, ontology_class] = self.config["mappings"]["event"][event_type].split(":")
                    else:
                        [namespace_name, ontology_class] = self.config["mappings"]["event"]["default"].split(":")
                    var_mappings["ontology_class"] = self.namespace[namespace_name][ontology_class]
                    
                var_mappings["member"] = self.namespace["BBNTA1"][kb_event.id]  # reset "member" variable each loop

                self.create_triples("event_group-unification", [], var_mappings=var_mappings)  # group unification ontologies are separate but identical

    def create_triples_from_event(self, kb_event):

        kb_document = kb_event.get_document()
        docId = kb_document.id

        event_type = kb_event.event_type_to_confidence.keys()[0]

        # already grounded?
        if self._event_type_is_grounded(event_type):
            type_assignment = URIRef(event_type)
            add_generic_genericity = type_assignment.endswith("#Factor")
            event_basename = event_type.split('/')[-1].split('#')[-1]
            event_label = self._get_event_type_label(event_basename)
            if self._grounded_event_type_is_bbnta1(event_type):
                namespace_name = "BBNTA1"
            else:
                namespace_name = "EVENT"

        # not already grounded.
        else:
            if event_type in self.config["mappings"]["event"]:
                [namespace_name, ontology_class] = self.config["mappings"]["event"][event_type].split(":")
                add_generic_genericity = (ontology_class == "Factor") # per ODP guidelines, all EVENT:Factor events should be tagged with a genericity value that is Generic
            else:
                add_generic_genericity = False
                [namespace_name, ontology_class] = self.config["mappings"]["event"]["default"].split(":")
            type_assignment = self.namespace[namespace_name][ontology_class]  # URIRef
            event_label = self._get_event_type_label(event_type)
            event_basename = event_type

        var_mappings = {
            "instance": self.namespace["BBNTA1"][kb_event.id],
            "label": Literal(re.sub("\n", " ", event_label), datatype=XSD.string),
            "ontology_class": type_assignment,
            "confidence": Literal(format(kb_event.confidence, '0.2f'), datatype = XSD.decimal),
        }
        optional_fields = []

        # hack to make sure that events with type BBNTA1:[...] also have an ODP event type
        # this indicates that we need to find a suitable ODP type to use instead
        if namespace_name == "BBNTA1":
            self.add_triples_bbn_event(type_assignment)
            
            # unclear why this is done instead of using the old function above
            second_event_type = self.namespace["EVENT"]["Event"]
            ontology_class = event_basename
            print "WARNING: Adding second event type %s to an event mapped to type %s" % (str(second_event_type), str(self.namespace[namespace_name][ontology_class]))
            optional_fields.append("extra_event_type")
            var_mappings["extra_ontology_class"] = second_event_type

        if add_generic_genericity:
             optional_fields.append("genericity")
             var_mappings["genericity"] = self.namespace["EVENT"]["Generic"]
        if kb_event.properties is not None:
            event_property_fields = ["tense", "modality", "polarity"]
            if not add_generic_genericity:
                event_property_fields.append("genericity")
            for field in event_property_fields:
                if field in kb_event.properties:
                    value = kb_event.properties[field]
                    if value not in (
                            "Unspecified", "unavailable", "Specific", 
                            "Positive", "Asserted", "historical", "current"):
                        optional_fields.append(field)
                        var_mappings[field] = self.config["mappings"]["event-property"][
                            kb_event.properties[field]]

        # TODO: fix this hack
        # I believe this section is deprecated, based on the contents of the yaml.  @criley
        # triples here: Boolean-is_supply_adequate?, generic_instance_for_artifact, ODP_type_of_artifact
        # 'Shortage': (False, self.namespace["BBNTA1"].generic_artifact, '?'),
        supply_map = {'FuelShortage': (0, self.namespace["BBNTA1"].generic_fuel,
                                       self.namespace["EVENTARTIFACT"].Fuel),
                      'WaterShortage': (0, self.namespace["BBNTA1"].generic_water,
                                        self.namespace["EVENTARTIFACT"].Water),
                      'FoodShortage': (0, self.namespace["BBNTA1"].generic_food,
                                       self.namespace["EVENTARTIFACT"].Food),
                      'CommunicationServicesAvailable': (1, self.namespace["BBNTA1"].generic_communication_services,
                                                         self.namespace["EVENTARTIFACT"].CommunicationsServices),
                      'CommunicationServicesNotAvailable': (0, self.namespace["BBNTA1"].generic_communication_services,
                                                            self.namespace["EVENTARTIFACT"].CommunicationsServices),
                      'SchoolsOrTrainingAvailable': (1, self.namespace["BBNTA1"].generic_schools_or_training,
                                                     self.namespace["EVENTARTIFACT"].SchoolsOrTraining),
                      'SchoolsOrTrainingNotAvailable': (0, self.namespace["BBNTA1"].generic_schools_or_training,
                                                        self.namespace["EVENTARTIFACT"].SchoolsOrTraining),
                      'ServicesAvailable': (1, self.namespace["BBNTA1"].generic_services,
                                            self.namespace["EVENTARTIFACT"].Services),
                      'ServicesNotAvailable': (0, self.namespace["BBNTA1"].generic_services,
                                               self.namespace["EVENTARTIFACT"].Services),
                      'ElectricPowerAvailable': (1, self.namespace["BBNTA1"].generic_electricity,
                                                 self.namespace["EVENTARTIFACT"].ElectricityOrPowerAndHeat),
                      'ElectricPowerNotAvailable': (0, self.namespace["BBNTA1"].generic_electricity,
                                                    self.namespace["EVENTARTIFACT"].ElectricityOrPowerAndHeat),
                      'HospitalAvailable': (1, self.namespace["BBNTA1"].generic_hospital,
                                            self.namespace["CCO"].Hospital),
                      'HospitalNotAvailable': (0, self.namespace["BBNTA1"].generic_hospital,
                                               self.namespace["CCO"].Hospital),
                      'Human.Healthcare': (1, self.namespace["BBNTA1"].generic_healthcare_services,
                                           self.namespace["EVENTARTIFACT"].HealthcareServices),
                      'ShelterAvailable': (1, self.namespace["BBNTA1"].generic_shelter,
                                           self.namespace["EVENTARTIFACT"].ShelterOrHousing),
                      'ShelterNotAvailable': (0, self.namespace["BBNTA1"].generic_shelter,
                                              self.namespace["EVENTARTIFACT"].ShelterOrHousing),
                      # TODO add event:SpecificTypeOfArtifact paradigm here
                      'FishingResourcesPresent': (1, self.namespace["BBNTA1"].generic_fisheries,
                                                  self.namespace["EVENTARTIFACT"].LandResources),
                      }

        if event_basename in supply_map:
            if supply_map[event_basename][0]:  # Adequate supply
                optional_fields.append("event_adequate_supply_artifact")
            else:  # Shortage
                optional_fields.append("event_shortage_artifact")
            var_mappings["generic_artifact_instance"] = supply_map[event_basename][1]
            var_mappings["artifact_type"] = supply_map[event_basename][2]

        for kb_event_mention in kb_event.event_mentions:
            
            # create a span and link it to the event
            # prefer to use the trigger, but use the snippet if there is no trigger
            if kb_event_mention.trigger is not None:
                event_span_text = kb_event_mention.trigger
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
                    "startOffset": Literal(self.adjust_offset(event_span_start, kb_event_mention.document), datatype=XSD.long),
                    "textLength": Literal(event_span_end - event_span_start + 1,
                                          datatype=XSD.long),
                    "text": Literal(re.sub("\n", " ", event_span_text), datatype=XSD.string),
                    "docInstance": self.get_causeex_docid(kb_document),
                    "sentenceInstance": self.namespace["BBNTA1"][kb_event_mention.sentence.id],
                    "instance": self.namespace["BBNTA1"][kb_event.id]
                }

            span_optional_fields = []
            span_optional_fields.append("instance")

            trigger_words = None
            if kb_event_mention.triggering_phrase:
                trigger_words = kb_event_mention.triggering_phrase
            elif kb_event_mention.trigger:
                trigger_words = kb_event_mention.trigger
            elif kb_event_mention.proposition_infos and len(kb_event_mention.proposition_infos) > 0:
                trigger_words = kb_event_mention.proposition_infos[0][0]
            if trigger_words:
                span_var_mappings["triggerWords"] =  Literal(trigger_words, datatype=XSD.string)
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

            if kb_event_mention.has_topic is not None:
                # How does this work in an event_mention -> event context?
                topic_event_id = self.kb_event_mention_to_kb_event[kb_event_mention.has_topic].id
                var_mappings["topic_event_instance"] = self.namespace["BBNTA1"][topic_event_id]
                optional_fields.append("event_topic")

            self.event_count += 1
            self.create_triples(
                "event",
                optional_fields,
                var_mappings=var_mappings
            )

            # for debug
            '''
            if event_basename == "Affiliation":
                print "args (Person/Entity/Position/Time) for Affiliation event mention %s" % kb_event_mention.id
                for kb_arg_role in [kar for kar in kb_event_mention.arguments if kar in ("Person", "Entity", "Position", "Time")]:
                    entid_and_mention_text = list()
                    for kb_argument in kb_event_mention.arguments[kb_arg_role]:
                        if isinstance(kb_argument, KBValueMention):
                            mention_text = kb_argument.value_mention_text
                            entid = "VALUEMENTION-ID-%s" % ascii_me(re.sub("\s", "_", kb_argument.value_mention_text))
                        else:
                            mention_text = kb_argument.mention_text
                            entid = self.kb.kb_mention_to_entid[kb_argument]
                        entid_and_mention_text.append((entid, mention_text))
                    print "%s: %s" % (kb_arg_role, str(entid_and_mention_text))
            '''

            # See if we can infer an affiiliation relationship based on the event type and the arguments
            # Note: this is similar to how to create AffiliationDetails for entity-entity relations
            # TODO: Also do this for the "Marriage" / "Wedding", and other "affiliation-like" event types?
            if event_basename == "Affiliation" and "Person" in kb_event_mention.arguments:

                var_mappings_for_affiliation = {}
                optional_fields = []

                has_affiliation_relationship = "has_affiliation"
                var_mappings_for_affiliation["relationship"] = self.namespace["ACTOR"][has_affiliation_relationship]

                [namespace_name, ontology_class] = self.config["mappings"]["entity-relation-arg-details"][has_affiliation_relationship]["concept_details"].split(":")
                var_mappings_for_affiliation["arg_details_concept"] = self.namespace[namespace_name][ontology_class]
                [namespace_name, ontology_class] = self.config["mappings"]["entity-relation-arg-details"][has_affiliation_relationship]["predicate"].split(":")
                concept_predicate = self.namespace[namespace_name][ontology_class]

                if "Time" in kb_event_mention.arguments:
                    time_arguments = kb_event_mention.arguments["Time"]

                    # TODO: Handle multiple time arguments
                    # assert len(kb_event_mention.arguments["Time"]) == 1 # not a valid assertion
                    time_arguments = [time_arguments[0]]

                    optional_fields.append("arg_instance_time")
                    var_mappings_for_affiliation["time"] = Literal(re.sub("\n", " ", kb_event_mention.arguments["Time"][0].value_mention_text), datatype=XSD.string)

                if not ("Entity" in kb_event_mention.arguments or "Position" in kb_event_mention.arguments):
                    print "WARNING: Affiliation event mention %s has no Entity or Position arguments" % kb_event_mention.id
                else:
                    if "Position" in kb_event_mention.arguments:
                        position_arguments = kb_event_mention.arguments["Position"]
                        if len(position_arguments) > 1:
                            print "WARNING: Affiliation event mention %s has more than one Position argument" % kb_event_mention.id
                            position_arguments = [position_arguments[0]]
                        position_argument = position_arguments[0]
                        optional_fields.append("arg_instance_position_or_role")
                        position_argument_text = re.sub("\n", " ", position_argument.value_mention_text)
                        var_mappings_for_affiliation["position_or_role"] = Literal(position_argument_text, datatype=XSD.string)
                    else:
                        position_argument_text = None

                    for person_argument in kb_event_mention.arguments["Person"]:
                        person_entity_id = self.kb.kb_mention_to_entid[person_argument]
                        var_mappings_for_affiliation["left_arg"] = self.namespace["BBNTA1"][person_entity_id]
                        optional_fields.append("left-sentence")
                        var_mappings_for_affiliation["left_sentence_id"] = self.namespace["BBNTA1"][person_argument.sentence.id]
                        assert person_argument.sentence.id == kb_event_mention.sentence.id
                        if "Entity" in kb_event_mention.arguments:
                            for entity_argument in kb_event_mention.arguments["Entity"]:
                                optional_fields.append("arg_instance_predicate")
                                entity_entity_id = self.kb.kb_mention_to_entid[entity_argument]
                                var_mappings_for_affiliation["pred"] = concept_predicate
                                var_mappings_for_affiliation["arg_entity_instance"] = self.namespace["BBNTA1"][entity_entity_id]
                                optional_fields.append("right-sentence")
                                var_mappings_for_affiliation["right_sentence_id"] = self.namespace["BBNTA1"][entity_argument.sentence.id]
                                assert entity_argument.sentence.id == kb_event_mention.sentence.id

                                if position_argument_text is not None:
                                    event_affiliation_identifier = "EventAffiliation-%s-%s-%s" % (person_entity_id, entity_entity_id, ascii_me(re.sub("[\s\"`]", "_", position_argument_text)))
                                else:
                                    event_affiliation_identifier = "EventAffiliation-%s-%s" % (person_entity_id, entity_entity_id)
                                var_mappings_for_affiliation["arg_instance"] = self.namespace["BBNTA1"][event_affiliation_identifier]
                                self.create_triples("entity-relation-arg-details", optional_fields, var_mappings = var_mappings_for_affiliation)
                        else: # just use the position argument
                                event_affiliation_identifier = "EventAffiliation-%s-%s" % (person_entity_id, ascii_me(re.sub("[\s\"`]", "_", position_argument_text)))
                                var_mappings_for_affiliation["arg_instance"] = self.namespace["BBNTA1"][event_affiliation_identifier]
                                self.create_triples("entity-relation-arg-details", optional_fields, var_mappings = var_mappings_for_affiliation)


        for kb_arg_role in kb_event.arguments:
            args_for_role = kb_event.arguments[kb_arg_role]
            if kb_arg_role == "Time" or kb_arg_role == "has_time":
                args_for_role = [args_for_role[0]] # TODO: Remove this hack and implement an intelligent way to combine multiple conflicting time arguments
            for kb_argument in args_for_role:
                # There are two methods for representing arguments:
                # 1) Mentions directly reference the argument as a literal (this uses the event-arg template), i.e.:
                #   <event> <gconcept#earliest_possible_start_time> "2014-01-01T00:00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime>
                # 2) Mentions reference the argument through an intermediary object (this uses the event-arg-instance template), i.e.:
                #   <event> <gconcept#associated_monetary_amount> <http://graph.causeex.com/bbn#MONETARY-2267>
                #   <http://graph.causeex.com/bbn#MONETARY-2267> <type> <...>
                #   <http://graph.causeex.com/bbn#MONETARY-2267> <amount_text> <...>
                argument_attached_thru_instance = False
                instance_argument_as_entity = None

                # get argument mention text
                if isinstance(kb_argument, KBValueMention):
                    mention_text = kb_argument.value_mention_text
                elif isinstance(kb_argument, KBEntity):
                    mention_text = kb_argument.canonical_name
                else:
                    if kb_argument is None:
                        continue
                    else:
                        print ("Not entity nor valueMention: " + str(kb_argument))
                        sys.exit(-1)

                if kb_arg_role == "Money":  # create money object, but don't attach it to the event yet
                    argument_attached_thru_instance = True
                    optional_fields = []

                    arg_instance = self.namespace["BBNTA1"]["MONETARY-" + kb_argument.id]
                    var_mappings["moninstance"] = arg_instance
                    var_mappings["amount_text"] = Literal(mention_text, datatype=RDFS.Literal)

                    if kb_argument.currency_amount is not None:
                        var_mappings["money_amount"] = self.create_currency_rdf_double(kb_argument.currency_amount)
                        optional_fields.append("money-numeric-amount")
                    if kb_argument.currency_type is not None:
                        currencies_not_found_in_cco = {'DjiboutiFranc', 'SomaliaShilling'}  # TODO a bit hacky?
                        if kb_argument.currency_type in currencies_not_found_in_cco:
                            currency_namespace = "GCONCEPT"
                        else:
                            currency_namespace = "CCO"
                        var_mappings["currency_type"] = self.namespace[currency_namespace][kb_argument.currency_type]
                        optional_fields.append("money-numeric-currency-type")
                    if kb_argument.currency_minimum is not None:
                        var_mappings["smallest_possible_amount"] = self.create_currency_rdf_double(kb_argument.currency_minimum)
                        optional_fields.append("money-numeric-smallest-possible-amount")
                    if kb_argument.currency_maximum is not None:
                        var_mappings["largest_possible_amount"] = self.create_currency_rdf_double(kb_argument.currency_maximum)
                        optional_fields.append("money-numeric-largest-possible-amount")

                    self.create_triples(
                        "value-money",
                        optional_fields,
                        var_mappings=var_mappings
                    )
                elif kb_arg_role == "Crime": # create crime object, but don't attach it to the event yet
                    argument_attached_thru_instance = True
                    optional_fields = []

                    arg_instance = self.namespace["BBNTA1"]["CRIME-" + kb_argument.id]
                    var_mappings["crimeinstance"] = arg_instance
                    var_mappings["crime_text"] = Literal(mention_text, datatype=RDFS.Literal)

                    self.create_triples(
                        "value-crime",
                        optional_fields,
                        var_mappings=var_mappings
                    )
                elif kb_arg_role == "Time" or kb_arg_role == "time" or kb_arg_role == "has_time": # attach time triples to event TODO: fix this role to just one spelling
                    kb_arg_role == "Time"
                    argument_attached_thru_instance = False
                    optional_fields = []

                    time_text = Literal(re.sub("\n", " ", mention_text), datatype=XSD.string)
                    var_mappings["time_text"] = time_text
                    optional_fields.append("time_text")

                    if kb_argument.normalized_date is not None:
                        startTime, endTime = self.time_matcher.match_time(kb_argument.normalized_date)
                        if startTime is not None and endTime is not None:
                            var_mappings["earliest_possible_start_time"] = Literal(
                                startTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                            #var_mappings["earliest_possible_end_time"] = Literal(
                            #    startTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                            #var_mappings["latest_possible_start_time"] = Literal(
                            #    endTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                            var_mappings["latest_possible_end_time"] = Literal(
                                endTime.replace(microsecond=0).isoformat(), datatype=XSD.dateTime)
                            #optional_fields.append("time_quadriple")
                            optional_fields.append("time_tuple")
                    self.create_triples(
                        "event-arg",
                        optional_fields,
                        var_mappings
                    )
                elif isinstance(kb_argument, KBValueMention): # Handle other types of value mentions; just attach their mention_text to the event using the appropriate predicate
                    argument_attached_thru_instance = False
                    optional_fields = ["value-mention"]

                    var_mappings["instance"] = self.namespace["BBNTA1"][kb_event.id]
                    if event_basename in self.config["mappings"]["event-role"]["byEventType"]:
                        [namespace_name, ontology_class] = self.config["mappings"]["event-role"]["byEventType"][event_basename][kb_arg_role]["default"].split(":")
                    else:
                        [namespace_name, ontology_class] = self.config["mappings"]["event-role"]["default"][kb_arg_role]["default"].split(":")
                    var_mappings["pred"] = self.namespace[namespace_name][ontology_class]
                    var_mappings["mention_text"] = Literal(mention_text, datatype=RDFS.Literal)

                    self.create_triples(
                        "event-arg",
                        optional_fields,
                        var_mappings
                    )

                elif kb_argument in self.kb.entid_to_kb_entity:
                    argument_attached_thru_instance = True
                    instance_argument_as_entity = self.kb.entid_to_kb_entity[kb_argument]

                    arg_instance = self.get_entity_ontology_object(instance_argument_as_entity)

                if argument_attached_thru_instance:
                    # create triples for argument
                    # get a predicate from event role
                    if event_basename in self.config["mappings"]["event-role"]["byEventType"]:
                        predicate_mappings = self.config["mappings"]["event-role"]["byEventType"][event_basename][kb_arg_role]
                    else:
                        predicate_mappings = self.config["mappings"]["event-role"]["default"][kb_arg_role]
                    if instance_argument_as_entity is not None:
                        # argument will be linked in RDF directly as the entity, rather than an intermediate object
                        ace_entity_type_with_subtype = instance_argument_as_entity.get_best_entity_type()
                        ace_entity_type = ace_entity_type_with_subtype.split(".")[0]
                        if ace_entity_type_with_subtype in predicate_mappings or ace_entity_type in predicate_mappings:
                            # there is a listed override for the predicate for the entity type
                            if ace_entity_type_with_subtype in predicate_mappings:
                                 # look at the more specific type first
                                [namespace_name, ontology_class] = predicate_mappings[ace_entity_type_with_subtype].split(":")
                            else:
                                [namespace_name, ontology_class] = predicate_mappings[ace_entity_type].split(":")
                        else:
                            # there is no listed override for the entity type, so just use the default predicate
                            [namespace_name, ontology_class] = predicate_mappings["default"].split(":")
                    else:
                        # argument will be linked in RDF as an intermediate object, so just use the default predicate
                        [namespace_name, ontology_class] = predicate_mappings["default"].split(":")
                    mpred = self.namespace[namespace_name][ontology_class]
                    event_instance = self.namespace["BBNTA1"][kb_event.id]

                    # Discard triples that violate domain/range constraints
                    if not self.check_subclass_rules(
                            event_instance, mpred, arg_instance):
                        #print('dropping: {}, {}, {}'.format(event_instance, mpred, arg_instance))
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

    def add_triples_seed_description(self, seed_milestone, seed_type, seed_version):
        self.create_triples(
            "seed",
            [],
            var_mappings={
                "instance": self.namespace["BBNTA1"]["Seed-" + datetime.now().strftime("%Y%m%d")],
                "seed_milestone": Literal(seed_milestone, datatype=XSD.string),
                "seed_type": Literal(seed_type, datatype=XSD.string),
                "seed_version": Literal(seed_version, datatype=XSD.string)
            }
        )

    def add_triples_documents_and_sentence_spans(self):
        # Generate documents and sentence spans
        seen_uuids = set()
        for docid in self.kb.docid_to_kb_document:
            kb_document = self.kb.docid_to_kb_document.get(docid)
            document_properties = kb_document.properties

            var_mappings = {
                "instance": self.get_causeex_docid(kb_document),
                "credibility": Literal(document_properties["credibility"], datatype=XSD.float)
            }

            optional_fields = []
            self.create_triples("documents", optional_fields, var_mappings=var_mappings)

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
                        "sentenceTextValue": Literal(re.sub("\n", " ", kb_sentence.text), datatype=XSD.string)
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
                        print "Skipping metadata triple from " + kb_document.id + " due to differing number of brackets"
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
            print "RDFSerializer creating triples from StructuredInput (" + \
                  str(input_count) + "/" + str(inputs_length) + ")"
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
                print "RDFSerializer creating triples from " \
                      "StructuredRelationship (" + \
                      str(count) + "/" + str(num_relationships) + ")"
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
        if len(missed_failures) > 0:
            print 'Discarded triples with bad domain/range which were mistakenly added:'
        for k in sorted(missed_failures.keys()):
            print missed_failures[k], k


# Typically, we don't run from the command line, we use this class as 
# part of kb_constructor.py run. But if we've run the KBPickleSerializer
# on a KB, we can run the serilization process starting with that 
# pickled KB here.
if __name__ == "__main__":
    if len(sys.argv) != 8:
        print "Usage: " + sys.argv[0] + " mode pickled_kb_file seed_milestone seed_type seed_version output_ttl_file output_nt_file"
        sys.exit(1)

    mode,seed_milestone, seed_type, seed_version, pickled_kb_file, output_ttl_file, output_nt_file = sys.argv[1:]
    with open(pickled_kb_file, "rb") as pickle_stream:
        print "Loading pickle file..."
        kb = pickle.load(pickle_stream)
        print "Done loading. Serializing..."
        rdf_serializer = RDFSerializer()
        rdf_serializer.serialize(kb, mode,seed_milestone, seed_type, seed_version,output_ttl_file, output_nt_file)
        print('Dropped triples for the following subclassing constraints:')
        for k in sorted(rdf_serializer.integrity_counts.keys()):
            print(rdf_serializer.integrity_counts[k], '\t', k)
        print(sum(rdf_serializer.integrity_counts.values()), '\t', 'Total')

