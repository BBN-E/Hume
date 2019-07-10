import re
import os
import sys
import uuid
import operator
import rdflib
import io
from datetime import datetime
import logging

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from time_matcher import TimeMatcher
from elements.kb_value_mention import KBValueMention, KBTimeValueMention
from json_encoder import ComplexEncoder
import json, codecs

import pickle

from ontology import Ontology


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(name)s]: %(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class JSONLDSerializer:

    def __init__(self):
        pass

    def get_event_to_event_relation_name(self,relation):
        self.event_event_relation_old_to_new = {
            "Cause-Effect": "causation",
            "Precondition-Effect": "precondition",
            "Preventative-Effect": "prevention",
            "Catalyst-Effect": "catalyst",
            "MitigatingFactor-Effect": "mitigation",
            "Before-After": "temporallyPrecedes"
        }
        return self.event_event_relation_old_to_new[relation]

    def get_event_argument_role(self, arg_role):
        self.event_arg_role_old_to_new = {
            "has_actor": "actor",
            "has_active_actor": "actor",
            "has_affected_actor": "actor",
            "has_recipient":"actor",
            "located_at": "place",
            "has_origin": "place",
            "has_destination": "place",
            "has_provider":"actor",
            "involves_goods_or_property": "artifact",
            "has_instrument": "artifact",
            "time":"time",
        }
        if arg_role in self.event_arg_role_old_to_new:
            return self.event_arg_role_old_to_new[arg_role]
        else:
            raise ValueError("There's argument role type {} from event consolidator which you don't have valid mapping".format(arg_role))
            # logging.error("We're dropping role type {}".format(arg_role))
            # return None


    def get_event_text(self, kb_event_mention):
        event_text = kb_event_mention.triggering_phrase if kb_event_mention.triggering_phrase is not None else \
            kb_event_mention.trigger if kb_event_mention.trigger is not None else kb_event_mention.snippet[0]
        return event_text


    def get_ontology_concept_for_event(self, kb_event_mention, config):

        event_type = kb_event_mention.event_type
        event_text = self.get_event_text(kb_event_mention)

        groundings_with_scores = []


        for groundings_to_external_ontology in kb_event_mention.external_ontology_sources:
            logger.debug("groundings_to_external_ontology: {}".format(groundings_to_external_ontology))
            type_external,score = groundings_to_external_ontology
            groundings_with_scores.append((type_external, score))


        if len(groundings_with_scores) < 1:
            ### grounding by looking up a table
            logger.warn("Cannot find any valid ontology concept for internal ontology node {}".format(event_type))

        return groundings_with_scores



    def get_ontology_concept_for_entity(self, ins_type, ins_subtype):
        category="entity"
        if ins_type in self.config["mappings"][category]:
            ontology_concept = self.config["mappings"][category][ins_type]["default_type"]
            if ins_subtype in self.config["mappings"][category][ins_type]["sub_types"]:
                ontology_concept = self.config["mappings"][category][ins_type]["sub_types"][ins_subtype]
            return ontology_concept
        else:
            logger.warn("Cannot find any valid ontology concept for entity_type: {}, subtype: {}".format(ins_type,ins_subtype))
            ontology_concept = self.config["mappings"][category]["default_type"]
            return ontology_concept



    def serialize(self, kb, output_jsonld_file, mode):
        print "JSONLDSerializer SERIALIZE"
        self.namespace = dict()
        self.config = dict()
        self.gid = 0
        self.event_group_id_map = dict() # Maps ID from KB to better looking ID
        self.time_matcher = TimeMatcher()

        self.event_group_count = 0
        self.entity_count = 0
        self.event_count = 0
        self.text_causal_assertion_count = 0


        self.mode = mode

        if self.mode == "CauseEx":
            self.config = self.read_config(
                os.path.dirname(os.path.realpath(__file__)) + "/../config_files/config_ontology_causeex.json")
        else:
            self.config = self.read_config(
                os.path.dirname(os.path.realpath(__file__)) + "/../config_files/config_ontology_wm.json")


        self.read_namespaces()
        self.kb = kb
        self.kb_event_mention_to_kb_event = dict()
        for kb_event_id, kb_event in self.kb.evid_to_kb_event.iteritems():
            for kb_event_mention in kb_event.event_mentions:
                self.kb_event_mention_to_kb_event[kb_event_mention] = kb_event

        o = codecs.open(output_jsonld_file, 'w', encoding='utf8')

        result = dict()
        self.add_context(result)
        result["@type"] = "Corpus"

        self.add_documents_and_sentence(result)

        self.add_extractions(result)

        o.write(unicode(json.dumps(result,encoding='utf8', sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False)))
        o.close()
        info_file_path = os.path.realpath(os.path.join(output_jsonld_file,os.pardir))
        info_file_path = os.path.join(info_file_path,os.path.basename(output_jsonld_file).split(".")[0] + ".info")
        output_info_stream = codecs.open(info_file_path,'w',encoding='utf8')
        output_info_stream.write("Entity count: " + str(self.entity_count) + "\n")
        output_info_stream.write("Event count: " + str(self.event_count) + "\n")
        output_info_stream.write("Causal assertion in text count: " + str(self.text_causal_assertion_count) + "\n")
        output_info_stream.write("Event group count: "+str(self.event_group_count)+"\n")
        output_info_stream.close()

        return


    def add_documents_and_sentence(self, result):
        documents = []

        # Generate documents and sentence spans
        for docid in self.kb.docid_to_kb_document:
            kb_document = self.kb.docid_to_kb_document.get(docid)

            document = dict()
            document["@type"] = "Document"
            document["@id"] = kb_document.properties["uuid"]
            document["location"] = kb_document.properties["source"]
            if self.mode == "CauseEx":
                document["location"] = document["location"].replace("/nfs/raid87/u14/", "")
                document["@uuid"] = kb_document.properties["uuid"]

            sentences = []

            for kb_sentence in kb_document.sentences:
                sentence = dict()

                sentence["@type"] = "Sentence"
                sentence["@id"] = kb_sentence.id
                sentence["text"] = kb_sentence.text

                sentences.append(sentence)

            document["sentences"] = sentences

            documents.append(document)

        result["documents"] = documents

    def get_json_object_for_entity(self, kb_entity_id, kb_entity):
        entities = [] # each mention is an entity; this function will return a list of entities
        coreference_relations = []

        mention_idx=1
        for kb_mention in kb_entity.mentions:
            entity = dict()

            entity_string = kb_entity.canonical_name
            if kb_entity.canonical_name is not None:
                entity["canonicalName"] = kb_entity.canonical_name

            if kb_entity.properties.get("geonameid",None) is not None:
                entity['geoname_id'] = kb_entity.properties.get("geonameid",None)

            entity["@type"] = "Extraction"

            labels = ["Entity"]
            entity["labels"] = labels

            groundings = []
            ontology_type = None
            for entity_type_info_key in kb_entity.entity_type_to_confidence.keys():
                entity_type_info = entity_type_info_key.split(".")
                entity_type = entity_type_info[0]
                entity_subtype = entity_type_info[1]

                ontology_concept = self.get_ontology_concept_for_entity(entity_type,entity_subtype)


                ontology_type = ontology_concept #"/entity/" + entity_type + "/" + entity_subtype
                grounding = self.get_json_object_for_grounding(ontology_type, kb_entity.entity_type_to_confidence[entity_type_info_key])
                groundings.append(grounding)

            if ontology_type is None:
                return None
            entity["grounding"] = groundings
            entity["type"] = "concept"
            entity["subtype"] = "entity"

            provenance = self.get_json_object_for_provenance(kb_mention.document, kb_mention.start_char, kb_mention.end_char, kb_mention.sentence.id)
            entity["@id"] = kb_entity_id + "-" + str(mention_idx)
            entity["provenance"] = provenance
            entity["text"] = kb_mention.mention_text

            entities.append(entity)

            # add coreference
            if mention_idx>1:
                self.gid += 1
                coreference_relation_id = "coreference-" + str(self.gid)
                coreference_relation = self.get_json_object_for_coreference_relation(coreference_relation_id, kb_entity_id + "-1", kb_entity_id + "-" + str(mention_idx))
                coreference_relations.append(coreference_relation)
            mention_idx=mention_idx+1

        return entities, coreference_relations

    def get_json_object_for_coreference_relation(self, relation_id, entity_id1, entity_id2):

        relation_type = "coreference"

        relation = dict()
        relation["@type"] = "Extraction"

        relation["@id"] = relation_id
        labels = []
        labels.append(relation_type)
        relation["labels"] = ["DirectedRelation"]
        relation["type"] = "relation"
        relation["subtype"] = relation_type

        # add arguments
        arguments = []
        argument = dict()
        argument["@type"] = "Argument"
        argument["type"] = "anchor"
        arg_ids = dict()
        arg_ids["@id"] = entity_id1
        argument["value"] = arg_ids
        arguments.append(argument)

        argument = dict()
        argument["@type"] = "Argument"
        argument["type"] = "reference"
        arg_ids = dict()
        arg_ids["@id"] = entity_id2
        argument["value"] = arg_ids
        arguments.append(argument)
        relation["arguments"] = arguments

        return relation


    def get_json_object_for_event_group(self, kb_event_group_id, kb_event_group):
        event_group = dict()
        event_group["@type"] = "Extraction"
        event_group["@id"] = self.event_group_id_map[kb_event_group_id]
        event_group["text"] = kb_event_group_id
        event_group["canonicalName"] = kb_event_group_id
        event_group["type"] = "concept"
        event_group["subtype"] = "event"

        groundings = []
        grounding = self.get_json_object_for_grounding("/hume/event group", 0.75)
        groundings.append(grounding)
        event_group["grounding"] = groundings

        return event_group

    def get_json_object_for_unified_relation(self, relation_id, kb_event_group_id, event_id):

        relation_type = "unification"

        relation = dict()
        relation["@type"] = "Extraction"

        relation["@id"] = relation_id
        labels = []
        labels.append(relation_type)
        relation["labels"] = ["DirectedRelation"]
        relation["type"] = "relation"
        relation["subtype"] = relation_type

        # add arguments
        arguments = []
        argument = dict()
        argument["@type"] = "Argument"
        argument["type"] = "group"
        arg_ids = dict()
        arg_ids["@id"] = self.event_group_id_map[kb_event_group_id]
        argument["value"] = arg_ids
        arguments.append(argument)

        argument = dict()
        argument["@type"] = "Argument"
        argument["type"] = "member"
        arg_ids = dict()
        arg_ids["@id"] = event_id
        argument["value"] = arg_ids
        arguments.append(argument)
        relation["arguments"] = arguments

        return relation

    '''
    def get_json_object_for_entity_entity_relation(self, relid, kb_relation):
        relation = dict()
        relation["@type"] = "Event"
        relation["@id"] = relid
        relation["labels"] = ["DirectedRelation"]
        relation["type"] = "/relation/entity relation/" + kb_relation.relation_type

        # add arguments
        arguments = []
        argument = dict()
        argument["@type"] = "Argument"
        argument["type"] = "has_left_arg"
        arg_ids = dict()
        arg_ids["@id"] = kb_relation.left_argument_id
        argument["value"] = arg_ids
        arguments.append(argument)

        argument = dict()
        argument["@type"] = "Argument"
        argument["type"] = "has_right_arg"
        arg_ids = dict()
        arg_ids["@id"] = kb_relation.right_argument_id
        argument["value"] = arg_ids
        arguments.append(argument)
        relation["arguments"] = arguments

        # provenance
        kb_relation_mention = kb_relation.relation_mentions[0]
        
        left_mention = kb_relation_mention.left_mention
        right_mention = kb_relation_mention.right_mention
        relation_span_start, relation_span_end = self.get_relation_span(left_mention.start_char,
                                                                        left_mention.end_char,
                                                                        right_mention.start_char,
                                                                        right_mention.end_char)
        provenances = []
        provenance = self.get_json_object_for_provenance(kb_relation_mention.document, relation_span_start, relation_span_end, left_mention.sentence.id)
        provenances.append(provenance)
        relation["provenance"] = provenances

        return relation
    '''

    def get_json_object_for_event_event_relation(self, kb_relation):
        relation_type = kb_relation.relation_type
        kb_relation_mention = kb_relation.relation_mentions[0]
        left_mention = kb_relation_mention.left_mention
        right_mention = kb_relation_mention.right_mention
        docId = kb_relation_mention.document.id

        # print "E2E\trelation_type=" + relation_type + "\tleft_mention=" + left_mention.id + "\t" + left_mention.trigger + "\tright_mention=" + right_mention.id + "\t" + right_mention.trigger

        source_event = self.kb_event_mention_to_kb_event[left_mention].id
        target_event = self.kb_event_mention_to_kb_event[right_mention].id

        relation = dict()
        relation["@type"] = "Extraction"
        relation["@id"] = kb_relation.id
        labels = []
        labels.append(kb_relation.relation_type)
        relation["labels"] = ["DirectedRelation"]
        relation['type']="relation"
        relation_type=self.get_event_to_event_relation_name(kb_relation.relation_type)
        relation['subtype']=relation_type


        # add arguments
        arguments = []
        argument = dict()
        argument["@type"] = "Argument"
        left_pred = self.config["mappings"]["event-event-relation"][relation_type]["left_predicate"]
        argument["type"] = left_pred
        arg_ids = dict()
        arg_ids["@id"] = source_event
        argument["value"] = arg_ids
        arguments.append(argument)

        argument = dict()
        argument["@type"] = "Argument"
        right_pred = self.config["mappings"]["event-event-relation"][relation_type]["right_predicate"]
        argument["type"] = right_pred
        arg_ids = dict()
        arg_ids["@id"] = target_event
        argument["value"] = arg_ids
        arguments.append(argument)
        relation["arguments"] = arguments

        # provenance
        relation_span_start, relation_span_end = self.get_relation_span(left_mention.trigger_start,
                                                                        left_mention.trigger_end,
                                                                        right_mention.trigger_start,
                                                                        right_mention.trigger_end)
        provenances = []
        provenance = self.get_json_object_for_provenance(kb_relation_mention.document, relation_span_start, relation_span_end, left_mention.sentence.id)
        provenances.append(provenance)
        relation["provenance"] = provenances

        reln_string = self.kb_event_mention_to_kb_event[left_mention].event_mentions[0].event_type + ":" + \
                      self.kb_event_mention_to_kb_event[left_mention].event_mentions[0].trigger + "\t" + \
                      relation_type + "\t" + \
                      self.kb_event_mention_to_kb_event[right_mention].event_mentions[0].event_type + ":" + \
                      self.kb_event_mention_to_kb_event[right_mention].event_mentions[0].trigger

        return relation

    def get_relation_span(self, arg1_start, arg1_end, arg2_start, arg2_end):
        start = arg1_start if arg1_start < arg2_start else arg2_start
        end = arg1_end if arg1_end > arg2_end else arg2_end

        return start, end

    def get_causeex_ontology_concept(self, type):
        if ":" in type:
            items = type.split(":")

            prefix = items[0]
            name = items[1]

            if prefix in self.namespace:
                causeex_ontology_path = self.namespace[prefix] + name
                logger.debug("causeex ontology lookup: " + type + " -> " + causeex_ontology_path)
                return causeex_ontology_path
        elif type == "/event":
            type = "http://ontology.causeex.com/ontology/odps/Event#Event"

        return type

    def get_json_object_for_grounding(self, type, confidence):
        grounding = dict()
        grounding["@type"] = "Grounding"
        grounding["name"] = "bbn" # use the "BBN ontology" (for now, it's just a hierarchy of concepts)
        if self.mode == "CauseEx":
            type = self.get_causeex_ontology_concept(type)
        grounding["ontologyConcept"] = type
        grounding["value"] = confidence
        return grounding

    def get_json_object_for_provenance(self, kb_document, char_start, char_end, sentence_id):
        provenance = dict()
        provenance["@type"] = "Provenance"
        doc_ref = dict()
        doc_ref["@id"] = kb_document.properties["uuid"]
        provenance["document"] = doc_ref
        provenance["sentence"] = sentence_id

        position = dict()
        position["@type"] = "Interval"
        position["start"] = char_start+kb_document.properties["offset"]
        position["end"] = char_end+kb_document.properties["offset"]
        provenance["documentCharPositions"] = position

        return provenance

    def make_value_mention_as_temporal_entities(self, value_mention):
        if isinstance(value_mention, KBTimeValueMention):
            entity = dict()

            entity["canonicalName"] = value_mention.normalized_date

            entity["@type"] = "Extraction"
            self.gid+=1
            entity_id = "Time-" + str(self.gid)
            entity["@id"] = entity_id

            labels = ["Entity"]
            entity["labels"] = labels

            groundings = []
            ontology_type = "/wm/concept/time" # grounding for temporal entity
            grounding = self.get_json_object_for_grounding(ontology_type, 0.75)
            groundings.append(grounding)

            entity["grounding"] = groundings
            entity["type"] = "concept"
            entity["subtype"] = "entity" # ontology_type

            mentions = []
            mention = dict()
            provenance = self.get_json_object_for_provenance(value_mention.document, value_mention.head_start_char,
                                                             value_mention.head_end_char, value_mention.sentence.id)
            mention["provenance"] = provenance

            mention["text"] = value_mention.value_mention_text
            mentions.append(mention)

            entity["mentions"] = mentions

            if value_mention.normalized_date is not None:
                startTime, endTime = self.time_matcher.match_time(value_mention.normalized_date)
                if startTime is not None and endTime is not None:
                    try:
                        entity['timeInterval'] = [{
                            "start": startTime.strftime('%Y-%m-%dT%H:%M'),
                            "end": endTime.strftime('%Y-%m-%dT%H:%M'),
                            'duration':int((endTime-startTime).total_seconds())
                        }]
                    except ValueError:
                        pass
            return entity_id, entity
        else:
            return None, None


    def get_json_object_for_event(self, evid, kb_event):
        event = dict()
        argument_temporal_entities = []

        # event_string = ""
        event["@type"] = "Extraction"
        event["@id"] = evid

        kb_event_mention = kb_event.event_mentions[0]  # assume one event mention per event
        event_type = kb_event_mention.event_type
        docId = kb_event_mention.document.id

        # add labels
        labels = ["Event"]
        event["labels"] = labels

        event_text = self.get_event_text(kb_event_mention)

        groundings_with_scores = self.get_ontology_concept_for_event(kb_event_mention, self.config)
        # convert groundings from Hume to WM
        # groundings_with_scores = self.convert_event_groundings_into_wm_ontology(groundings_with_scores)


        groundings = []
        for (concept,score) in groundings_with_scores:
            grounding = self.get_json_object_for_grounding(concept, score)
            groundings.append(grounding)


        # add trigger
        trigger = dict()
        trigger["@type"] = "Trigger"
        trigger["text"] = event_text
        trigger["head text"] = kb_event_mention.trigger if kb_event_mention.trigger else "NA"
        event["text"] = event_text
        event["canonicalName"] = event_text

        event["grounding"] = groundings
        event["type"] = "concept"
        event["subtype"] = "event"

        if kb_event_mention.trigger is not None:
            provenances = []
            provenance = self.get_json_object_for_provenance(kb_event_mention.document, kb_event_mention.trigger_start, kb_event_mention.trigger_end, kb_event_mention.sentence.id)
            provenances.append(provenance)
            trigger["provenance"] = provenances
            event["provenance"] = provenances

        event["trigger"] = trigger

        # states
        states = []
        if kb_event_mention.properties is not None:
            for field in "tense", "modality", "genericity", "polarity", "direction_of_change":
                if field in kb_event_mention.properties:
                    value = kb_event_mention.properties[field]
                    if value not in ("Unspecified", "unavailable"):
                        state = dict()
                        state["@type"] = "State"
                        state["type"] = field
                        state["text"] = value
                        states.append(state)
        event["states"] = states

        # add arguments
        arguments = []
        for kb_arg_role in kb_event_mention.arguments:
            args_for_role = kb_event_mention.arguments[kb_arg_role]
            if type(args_for_role[0]) == list:
                args_for_role = args_for_role[0]
            for kb_argument in args_for_role:
                # convert KBP roles to new role names
                kb_arg_role_wm_ontology = self.get_event_argument_role(kb_arg_role)

                # get argument mention text
                if isinstance(kb_argument, KBValueMention):
                    mention_text = kb_argument.value_mention_text

                    if self.mode != "CauseEx":
                        # Time mention: temporal entities
                        temporal_entity_id, temporal_entity = self.make_value_mention_as_temporal_entities(kb_argument)
                        if temporal_entity_id is not None and temporal_entity is not None:
                            argument = dict()
                            argument["@type"] = "Argument"
                            argument["type"] = kb_arg_role_wm_ontology
                            arg_ids = dict()
                            arg_ids["@id"] = temporal_entity_id
                            argument["value"] = arg_ids
                    
                            arguments.append(argument)

                            argument_temporal_entities.append(temporal_entity)
                else:
                    mention_text = kb_argument.mention_text

                    if kb_argument in self.kb.kb_mention_to_entid:
                        arg_entity_id = self.kb.entid_to_kb_entity[self.kb.kb_mention_to_entid[kb_argument]]

                        argument = dict()
                        argument["@type"] = "Argument"
                        argument["type"] = kb_arg_role_wm_ontology
                        arg_ids = dict()
                        arg_ids["@id"] = arg_entity_id.id + "-1" # hack to take the first mention
                        argument["value"] = arg_ids

                        event_arg_string = ""
                        for entity_type_info_key in arg_entity_id.entity_type_to_confidence.keys():
                            entity_type_info = entity_type_info_key.split(".")
                            entity_type = entity_type_info[0]
                            entity_subtype = entity_type_info[1]
                        arguments.append(argument)
        event["arguments"] = arguments

        return event, argument_temporal_entities

    def add_extractions(self, result):
        extractions = []

        # add entities
        for entid, kb_entity in self.kb.entid_to_kb_entity.iteritems():
            entities, coreference_relations = self.get_json_object_for_entity(entid, kb_entity)
            for entity in entities:
                extractions.append(entity)
                self.entity_count += 1
            for relation in coreference_relations:
                extractions.append(relation)

        # add event groups
        for kb_event_group_id, kb_event_group in self.kb.evgroupid_to_kb_event_group.iteritems():
            if "EventUnified" in kb_event_group_id:
                continue

            jsonld_event_group_id = "EventGroup-" + str(self.event_group_count)
            self.event_group_count += 1
            self.event_group_id_map[kb_event_group_id] = jsonld_event_group_id
            
            event_group = self.get_json_object_for_event_group(kb_event_group_id, kb_event_group)
            extractions.append(event_group)

            # add event unification relationships
            for kb_event in kb_event_group.members:
                self.gid += 1
                unified_relation_id = "unification-" + str(self.gid)
                event_id = kb_event.id
                relation = self.get_json_object_for_unified_relation(unified_relation_id, kb_event_group_id, event_id)
                extractions.append(relation)

        # add events
        for evid, kb_event in self.kb.evid_to_kb_event.iteritems():
            event, argument_temporal_entities = self.get_json_object_for_event(evid, kb_event)
            if event is None:
                continue

            extractions.append(event)
            self.event_count += 1
            # add time arguments as temporal entities
            for temporal_entity in argument_temporal_entities:
                extractions.append(temporal_entity)

        # add entity-entity and event-event relations
        for relid, kb_relation in self.kb.relid_to_kb_relation.iteritems():
            # if kb_relation.argument_pair_type == "entity-entity" and self.is_good_entity_entity_relation(kb_relation):
            #    relation = self.get_json_object_for_entity_entity_relation(relid, kb_relation)
            #    extractions.append(relation)

            if kb_relation.argument_pair_type == "event-event":
                relation = self.get_json_object_for_event_event_relation(kb_relation)
                extractions.append(relation)
                self.text_causal_assertion_count += 1
        result["extractions"] = extractions

    def is_good_entity_entity_relation(self, kb_relation):
        kb_relation_mention = kb_relation.relation_mentions[0]
        return kb_relation_mention.left_mention is not None and kb_relation_mention.right_mention is not None

    def add_context(self, result):
        contexts = dict()

        prefix = "https://w3id.org/wm/cag/"
        contexts["Argument"]=prefix+"Argument"
        contexts["Corpus"]=prefix+"Corpus"
        contexts["Dependency"]=prefix+"Dependency"
        contexts["Document"]=prefix+"Document"
        contexts["Entity"]=prefix+"Entity"
        contexts["Event"]=prefix+"Event"
        contexts["Interval"]=prefix+"Interval"
        contexts["Modifier"]=prefix+"Modifier"
        contexts["Provenance"]=prefix+"Provenance"
        contexts["Sentence"]=prefix+"Sentence"
        contexts["State"]=prefix+"State"
        contexts["Trigger"]=prefix+"Trigger"
        contexts["Word"]=prefix+"Word"

        result["@context"] = contexts

    def read_config(self, filepath):
        with open(filepath) as fp:
            config = json.load(fp)
        return config

    def read_namespaces(self):
        for namespace,URI in self.config.get('namespace',{}).items():
            self.namespace[namespace] = URI



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: " + sys.argv[0] + " pickled_kb_file output_jsonld_file mode hume_to_wm_mapping"
        sys.exit(1)

    logger.setLevel(logging.DEBUG)

    pickled_kb_file,output_jsonld_file,mode = sys.argv[1:]
    with open(pickled_kb_file, "rb") as pickle_stream:
        logger.info("Loading pickle file...")
        kb = pickle.load(pickle_stream)
        logger.info("Done loading. Serializing...")
        rdf_serializer = JSONLDSerializer()
        rdf_serializer.serialize(kb, output_jsonld_file, mode)
