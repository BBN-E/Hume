import sys

import logging
import os

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

from serializers.time_matcher import TimeMatcher
from elements.kb_value_mention import KBValueMention, KBTimeValueMention
from elements.kb_mention import KBMention
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(name)s]: %(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def span_id_generator(provenance, span_type):
    start, end = provenance["documentCharPositions"]["start"], provenance["documentCharPositions"]["end"]
    doc_uuid = provenance["document"]["@id"]
    return "{}#{}#{}#{}".format(doc_uuid, span_type, start, end)


class JSONLDSerializer:

    def __init__(self):
        pass

    def get_event_to_event_relation_name(self, relation):
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
            "has_actor": "has_actor",
            "has_active_actor": "has_active_actor",
            "has_affected_actor": "has_affected_actor",
            "has_location": "has_location",
            "has_origin_location": "has_origin_location",
            "has_destination_location": "has_destination_location",
            "has_intermediate_location": "has_intermediate_location",
            "has_time": "has_time",
            "has_theme": "has_theme",
            "has_property": "has_property",
            "has_start_time": "has_start_time",
            "has_end_time": "has_end_time",
            "has_duration": "has_duration",
            "has_artifact": "has_artifact",
            # "time": "has_time",
            # "located_at": "has_location",
            # "involves_goods_or_property": "has_artifact",
            # "has_recipient":"actor",
            # "has_origin": "origin",
            # "has_destination": "destination",
            # "has_provider":"actor",
            # "involves_goods_or_property": "artifact",
            # "has_instrument": "artifact",
            # "time": "time",

        }
        if arg_role in self.event_arg_role_old_to_new:
            return self.event_arg_role_old_to_new[arg_role]
        else:
            raise ValueError(
                "There's argument role type {} from event consolidator which you don't have valid mapping".format(
                    arg_role))
            # logging.error("We're dropping role type {}".format(arg_role))
            # return None

    def get_event_text(self, kb_event_mention):
        event_text = kb_event_mention.triggering_phrase if kb_event_mention.triggering_phrase is not None else \
            kb_event_mention.trigger if kb_event_mention.trigger is not None else kb_event_mention.snippet[0]
        return event_text

    def get_ontology_concept_for_event(self, kb_event_mention):

        groundings_with_scores = []

        # for groundings_to_external_ontology in kb_event_mention.external_ontology_sources:
        #     logger.debug("groundings_to_external_ontology: {}".format(groundings_to_external_ontology))
        #     type_external,score = groundings_to_external_ontology
        #     groundings_with_scores.append((type_external, score))
        for cf_type in kb_event_mention.causal_factors:
            groundings_with_scores.append((cf_type.factor_class, cf_type.relevance))

        if len(groundings_with_scores) < 1:
            ### grounding by looking up a table
            logger.warning("Cannot find any valid ontology concept for internal ontology node {}".format(None))

        return groundings_with_scores

    def _get_ontology_concept_for_category(self, ins_type, ins_subtype, category):
        if self.use_compositional_ontology:
            category = "{}-compositional".format(category)
            logger.info("Using the compositional {} ontology".format(category))
        if ins_type in self.config["mappings"][category]:
            ontology_concept = self.config["mappings"][category][ins_type]["default_type"]
            if ins_subtype in self.config["mappings"][category][ins_type]["sub_types"]:
                ontology_concept = self.config["mappings"][category][ins_type]["sub_types"][ins_subtype]
            return ontology_concept
        else:
            logger.warning("Cannot find any valid ontology concept for {}: {}, subtype: {}".format(category, ins_type,
                                                                                                   ins_subtype))
            ontology_concept = self.config["mappings"][category]["default_type"]
            return ontology_concept

    def get_ontology_concept_for_entity(self, ins_type, ins_subtype):
        category = "entity"
        return self._get_ontology_concept_for_category(ins_type, ins_subtype, category)

    def get_ontology_concept_for_property(self, ins_type, ins_subtype):
        category = "property"
        return self._get_ontology_concept_for_category(ins_type, ins_subtype, category)

    def serialize(self, kb, output_dir, mode, use_compositional_ontology, wm_external_ontology_hash,
                  regrounding_mode):
        print("JSONLDSerializer SERIALIZE")
        os.makedirs(output_dir, exist_ok=True)
        self.wm_external_ontology_hash = wm_external_ontology_hash
        self.kb_mention_to_serialized_entity_id = dict()
        self.namespace = dict()
        self.config = dict()

        self.event_group_id_map = dict()  # Maps ID from KB to better looking ID
        self.time_matcher = TimeMatcher()

        self.event_group_count = 0
        self.entity_count = 0
        self.event_count = 0
        self.text_causal_assertion_count = 0

        self.use_compositional_ontology = use_compositional_ontology == "true"
        self.mode = mode
        self.regrounding_mode = True if regrounding_mode.lower() == "true" else False

        if self.mode == "CauseEx":
            self.config = self.read_config(
                os.path.dirname(os.path.realpath(__file__)) + "/../config_files/config_ontology_causeex.json")
        else:
            self.config = self.read_config(
                os.path.dirname(os.path.realpath(__file__)) + "/../config_files/config_ontology_wm.json")

        self.read_namespaces()
        self.kb = kb
        doc_uuid_to_json_ld = dict()

        self.add_extractions(doc_uuid_to_json_ld)

        for doc_uuid, json_ld_en in doc_uuid_to_json_ld.items():
            self.add_context(json_ld_en)
            self.add_ontology_meta(json_ld_en)
            json_ld_dir = os.path.join(output_dir, doc_uuid)
            os.makedirs(json_ld_dir, exist_ok=True)
            with open(os.path.join(json_ld_dir, "{}.json-ld".format(doc_uuid)), 'w') as wfp:
                json.dump(json_ld_en, wfp, indent=4, sort_keys=True, ensure_ascii=False)

        info_file_path = os.path.join(output_dir, "output.info")
        with open(info_file_path, 'w') as output_info_stream:
            output_info_stream.write("Entity count: " + str(self.entity_count) + "\n")
            output_info_stream.write("Event count: " + str(self.event_count) + "\n")
            output_info_stream.write("Causal assertion in text count: " + str(self.text_causal_assertion_count) + "\n")
            output_info_stream.write("Event group count: " + str(self.event_group_count) + "\n")

        return

    def add_documents_and_sentence(self, doc_id_to_json_ld):
        doc_uuid_to_doc_en = dict()

        # Generate documents and sentence spans
        for docid in self.kb.docid_to_kb_document:
            kb_document = self.kb.docid_to_kb_document.get(docid)
            doc_en = doc_uuid_to_doc_en.setdefault(kb_document.properties["uuid"], dict())
            doc_en["@type"] = "Document"
            doc_en["@id"] = kb_document.properties["uuid"]

            if self.regrounding_mode is False:
                sentences = doc_en.setdefault("sentences", list())
                for kb_sentence in kb_document.sentences:
                    sentence = dict()
                    provenance = self.get_json_object_for_provenance(kb_document, kb_sentence.start_offset,
                                                                     kb_sentence.end_offset, kb_sentence)
                    sentence["@type"] = "Sentence"
                    sentence["@id"] = provenance['sentence']
                    sentence["text"] = kb_sentence.original_text

                    sentences.append(sentence)
        for doc_uuid, doc_en in doc_uuid_to_doc_en.items():
            doc_id_to_json_ld.setdefault(doc_uuid, dict())['documents'] = [doc_en]
            doc_id_to_json_ld.setdefault(doc_uuid, dict())['extractions'] = []

    def get_count_objects_for_mention(self, kb_mention, entity_id):
        numeric_dict = kb_mention.properties['numeric']
        unit = "Absolute"
        if "time_interval" in numeric_dict.keys():
            if "month" in numeric_dict['time_interval']:
                unit = "Monthly"
            elif "daily" in numeric_dict['time_interval']:
                unit = "Daily"
            elif "weekly" in numeric_dict['time_interval']:
                unit = "Weekly"
        value = 1
        modifier = "NoModifier"
        if "approximate" in kb_mention.mention_text.lower():
            modifier = "Approximate"
        if "min_val" in numeric_dict.keys():
            modifier = "Min"
            value = numeric_dict['min_val']
        elif "max_val" in numeric_dict.keys():
            modifier = "Max"
            value = numeric_dict['max_val']
        else:
            value = 1 if numeric_dict.get('val', 'NA') == 'NA' else numeric_dict.get('val', 'NA')
        count_obj = {
            "@id": entity_id + "-CNT",
            "@type": "Count",
            "modifier": modifier,
            "value": value,
            "unit": unit
        }
        if abs(value - 1) < 0.0001:
            return None
        else:
            return count_obj

    def get_json_object_for_entity(self, kb_entity_id, kb_entity, kb_entity_in_kb_events,
                                   kb_entity_mention_in_kb_events):
        entities = []  # each mention is an entity; this function will return a list of entities
        coreference_relations = []

        if self.regrounding_mode is True and kb_entity not in kb_entity_in_kb_events:
            return entities, coreference_relations

        for kb_mention in kb_entity.mentions:
            entity = dict()
            provenance = self.get_json_object_for_provenance(kb_mention.document, kb_mention.start_char,
                                                             kb_mention.end_char, kb_mention.sentence)
            entity["@id"] = span_id_generator(provenance, type(kb_mention).__name__)
            if kb_entity.canonical_name is not None:
                entity["canonicalName"] = kb_entity.canonical_name

            if kb_entity.properties.get("geonameid", None) is not None:
                entity['geoname_id'] = kb_entity.properties.get("geonameid", None)

            entity["@type"] = "Extraction"
            entity["labels"] = ["Entity"]

            if "numeric" in kb_mention.properties:
                entity['counts'] = []
                count_obj = self.get_count_objects_for_mention(kb_mention, entity["@id"])
                if count_obj is not None:
                    entity['counts'].append(count_obj)

            groundings = []
            ontology_type = None
            for entity_type_info_key in kb_entity.entity_type_to_confidence.keys():
                entity_type_info = entity_type_info_key.split(".")
                entity_type = entity_type_info[0]
                entity_subtype = entity_type_info[1]

                ontology_concept = self.get_ontology_concept_for_entity(entity_type, entity_subtype)

                ontology_type = ontology_concept  # "/entity/" + entity_type + "/" + entity_subtype
                grounding = self.get_json_object_for_grounding(ontology_type, kb_entity.entity_type_to_confidence[
                    entity_type_info_key])
                groundings.append(grounding)

            if ontology_type is None:
                raise ValueError("Cannot find mapping for entity type {}".format(ontology_type))
            entity["grounding"] = groundings
            entity["type"] = "concept"
            entity["subtype"] = "entity"

            entity["provenance"] = [provenance]
            entity["text"] = kb_mention.mention_text
            self.kb_mention_to_serialized_entity_id[kb_mention] = entity["@id"]
            entities.append(entity)
        if len(kb_entity.mentions) > 1:
            first_entity_mention_output = entities[0]["@id"]
            for idx, entity_mention in enumerate(entities[1:]):
                coreference_relation = self.get_json_object_for_coreference_relation("{}-{}".format(kb_entity_id, idx),
                                                                                     first_entity_mention_output,
                                                                                     entity_mention["@id"])
                coreference_relations.append(coreference_relation)

        return entities, coreference_relations

    def get_json_object_for_coreference_relation(self, relation_id, entity_id1, entity_id2):
        relation = dict()
        relation["@type"] = "Extraction"

        relation["@id"] = relation_id

        relation["labels"] = ["DirectedRelation"]
        relation["type"] = "relation"
        relation["subtype"] = "coreference"

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
        event_group['labels'] = ["EventGroup"]
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

    def get_json_object_for_event_event_relation(self, kb_relation):
        kb_relation_mention = kb_relation.relation_mentions[0]
        left_mention = kb_relation_mention.left_mention
        right_mention = kb_relation_mention.right_mention

        left_mention_json_ld_id = self.kb_event_to_serialized_event_id[left_mention]
        right_mention_jsonld_id = self.kb_event_to_serialized_event_id[right_mention]

        relation = dict()
        relation["@type"] = "Extraction"

        labels = []
        labels.append(kb_relation.relation_type)
        relation["labels"] = ["DirectedRelation"]
        relation['type'] = "relation"
        relation_type = self.get_event_to_event_relation_name(kb_relation.relation_type)
        relation['subtype'] = relation_type

        # add arguments
        arguments = []
        argument = dict()
        argument["@type"] = "Argument"
        left_pred = self.config["mappings"]["event-event-relation"][relation_type]["left_predicate"]
        argument["type"] = left_pred
        arg_ids = dict()
        arg_ids["@id"] = left_mention_json_ld_id
        argument["value"] = arg_ids
        arguments.append(argument)

        argument = dict()
        argument["@type"] = "Argument"
        right_pred = self.config["mappings"]["event-event-relation"][relation_type]["right_predicate"]
        argument["type"] = right_pred
        arg_ids = dict()
        arg_ids["@id"] = right_mention_jsonld_id
        argument["value"] = arg_ids
        arguments.append(argument)
        relation["arguments"] = arguments

        # provenance
        relation_span_start, relation_span_end = self.get_relation_span(left_mention.trigger_start,
                                                                        left_mention.trigger_end,
                                                                        right_mention.trigger_start,
                                                                        right_mention.trigger_end)
        provenances = []
        provenance = self.get_json_object_for_provenance(kb_relation_mention.document, relation_span_start,
                                                         relation_span_end, left_mention.sentence)
        provenances.append(provenance)
        relation["provenance"] = provenances
        relation["@id"] = "{}#{}#{}".format(left_mention_json_ld_id, relation_type, right_mention_jsonld_id)
        return relation, kb_relation_mention.document.properties["uuid"]

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
        grounding["name"] = "bbn"  # use the "BBN ontology" (for now, it's just a hierarchy of concepts)
        if self.mode == "CauseEx":
            type = self.get_causeex_ontology_concept(type)
        grounding["ontologyConcept"] = type
        grounding["value"] = confidence
        return grounding

    def get_json_object_for_provenance(self, kb_document, char_start, char_end, kb_sentence):
        provenance = dict()
        provenance["@type"] = "Provenance"
        doc_ref = dict()
        doc_ref["@id"] = kb_document.properties["uuid"]
        provenance["document"] = doc_ref

        position = dict()
        position["@type"] = "Interval"
        position["start"] = char_start + kb_document.properties["offset"]
        position["end"] = char_end + kb_document.properties["offset"]
        provenance["documentCharPositions"] = position
        provenance["sentence"] = "{}#{}#{}".format(kb_document.properties["uuid"],
                                                   kb_document.properties["offset"] + kb_sentence.start_offset,
                                                   kb_document.properties["offset"] + kb_sentence.end_offset)
        sent_position = dict()
        sent_position["@type"] = "Interval"
        sent_position["start"] = char_start - kb_sentence.start_offset
        sent_position["end"] = char_end - kb_sentence.start_offset
        provenance["sentenceCharPositions"] = sent_position

        return provenance

    def make_value_mention_as_property_entities(self, value_mention):
        if isinstance(value_mention, KBValueMention):
            entity = dict()
            provenance = self.get_json_object_for_provenance(
                value_mention.document,
                value_mention.head_start_char,
                value_mention.head_end_char,
                value_mention.sentence)
            entity["canonicalName"] = value_mention.value_mention_text
            entity["@type"] = "Extraction"
            entity_id = span_id_generator(provenance, type(value_mention).__name__)
            entity["@id"] = entity_id
            labels = ["Entity"]
            entity["labels"] = labels

            groundings = []
            value_type_info = value_mention.value_type.split(".")
            value_type = value_type_info[0]
            value_subtype = None
            if len(value_type_info) == 2:
                value_subtype = value_type_info[1]
            ontology_concept = self.get_ontology_concept_for_property(value_type, value_subtype)
            grounding = self.get_json_object_for_grounding(ontology_concept,
                                                           0.75)  # TODO where is KBValueMention confidence?
            groundings.append(grounding)

            entity["grounding"] = groundings
            entity["type"] = "concept"
            entity["subtype"] = "entity"  # ontology_type

            entity["provenance"] = [provenance]
            entity["text"] = value_mention.value_mention_text

            return entity_id, entity
        else:
            return None, None

    def make_value_mention_as_temporal_entities(self, value_mention):
        if isinstance(value_mention, KBTimeValueMention):
            entity = dict()
            provenance = self.get_json_object_for_provenance(value_mention.document, value_mention.head_start_char,
                                                             value_mention.head_end_char, value_mention.sentence)
            entity["canonicalName"] = value_mention.normalized_date

            entity["@type"] = "Extraction"

            entity_id = span_id_generator(provenance, type(value_mention).__name__)
            entity["@id"] = entity_id

            labels = ["Entity"]
            entity["labels"] = labels

            groundings = []
            if self.use_compositional_ontology:
                ontology_type = "/wm/concept/time"  # grounding for temporal entity
            else:
                ontology_type = "/wm/concept/time"  # grounding for temporal entity
            grounding = self.get_json_object_for_grounding(ontology_type, 0.75)
            groundings.append(grounding)

            entity["grounding"] = groundings
            entity["type"] = "concept"
            entity["subtype"] = "entity"  # ontology_type

            entity["provenance"] = [provenance]
            entity["text"] = value_mention.value_mention_text

            if value_mention.normalized_date is not None:
                # Third argument to match_time is document date used for resolving PRESENT_REF, PAST_REF, FUTURE_REF
                kb_document = value_mention.document
                document_date = None
                if "date_created" in kb_document.properties and kb_document.properties["date_created"] != "UNKNOWN":
                    document_date = kb_document.properties["date_created"]
                earliestStartTime, earliestEndTime, latestStartTime, latestEndTime = \
                    self.time_matcher.match_time(value_mention.normalized_date, value_mention.value_mention_text,
                                                 document_date)
                if earliestStartTime is not None and latestEndTime is not None:
                    try:
                        entity['timeInterval'] = [{
                            "start": earliestStartTime.strftime('%Y-%m-%dT%H:%M'),
                            "end": latestEndTime.strftime('%Y-%m-%dT%H:%M'),
                            'duration': int((latestEndTime - earliestStartTime).total_seconds()),
                            '@type': "TimeInterval"
                        }]
                    except ValueError:
                        pass
            return entity_id, entity
        else:
            return None, None

    def get_mentioned_kb_entity_kb_entity_mention_from_all_event(self):
        mentioned_kb_entity = set()
        mentioned_kb_entity_mention = set()
        for evid, kb_event in self.kb.evid_to_kb_event.items():
            for kb_event_mention in kb_event.event_mentions:
                for kb_arg_role, args_for_role in kb_event_mention.arguments.items():
                    for kb_argument, arg_score in args_for_role:
                        if isinstance(kb_argument, KBMention):
                            if kb_argument in self.kb.kb_mention_to_entid:
                                kb_entity = self.kb.entid_to_kb_entity[self.kb.kb_mention_to_entid[kb_argument]]
                                mentioned_kb_entity.add(kb_entity)
                                mentioned_kb_entity_mention.add(kb_argument)
        return mentioned_kb_entity, mentioned_kb_entity_mention

    def get_json_object_for_event(self, evid, kb_event):
        events = list()
        argument_value_entities = list()
        kb_event_mention_to_serialized_event_ids = dict()
        for kb_event_mention in kb_event.event_mentions:
            provenance = self.get_json_object_for_provenance(kb_event_mention.document,
                                                             kb_event_mention.trigger_start,
                                                             kb_event_mention.trigger_end,
                                                             kb_event_mention.sentence)
            event = dict()
            event["@type"] = "Extraction"
            event["@id"] = span_id_generator(provenance, type(kb_event_mention).__name__)
            kb_event_mention_to_serialized_event_ids[kb_event_mention] = event["@id"]
            event["labels"] = ["Event"]

            event_text = self.get_event_text(kb_event_mention)

            groundings_with_scores = self.get_ontology_concept_for_event(kb_event_mention)

            groundings = []
            for (concept, score) in groundings_with_scores:
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
            trigger["provenance"] = [provenance]
            event["provenance"] = [provenance]
            event["trigger"] = trigger

            # states
            states = []
            focus_causal_factor = sorted(kb_event_mention.causal_factors,
                                         key=lambda x: (1, x.factor_class) if "food_security" in x.factor_class else (
                                             0, x.factor_class), reverse=True)[0]
            if kb_event_mention.properties is not None:
                for field in "tense", "modality", "genericity":
                    if field in kb_event_mention.properties:
                        value = kb_event_mention.properties[field]
                        if value not in ("Unspecified", "unavailable"):
                            state = dict()
                            state["@type"] = "State"
                            state["type"] = field
                            state["text"] = value
                            states.append(state)
                # Handling magnitude
                state = dict()
                state["type"] = "magnitude"
                state["@type"] = "State"
                state["text"] = abs(focus_causal_factor.magnitude)
                states.append(state)

                # Handling polarity
                state = dict()
                state["type"] = "polarity"
                state["@type"] = "State"
                state["text"] = "Negative" if focus_causal_factor.magnitude < 0 else "Positive"
                states.append(state)

                # Handling direction_of_change
                state = dict()
                state["@type"] = "State"
                state["type"] = "direction_of_change"
                state["text"] = kb_event_mention.properties["direction_of_change"]
                states.append(state)

            event["states"] = states

            # add arguments
            arguments = []
            for kb_arg_role, args_for_role in kb_event_mention.arguments.items():
                for kb_argument, arg_score in args_for_role:
                    # convert KBP roles to new role names
                    kb_arg_role_wm_ontology = self.get_event_argument_role(kb_arg_role)

                    # get argument mention text
                    if isinstance(kb_argument, KBValueMention):
                        mention_text = kb_argument.value_mention_text

                        if self.mode != "CauseEx":

                            if kb_arg_role_wm_ontology == "has_property":
                                # Property value (such as the cost of an intervention)
                                property_entity_id, property_entity = self.make_value_mention_as_property_entities(
                                    kb_argument)
                                if property_entity_id is not None and property_entity is not None:
                                    argument = dict()
                                    argument["@type"] = "Argument"
                                    argument["type"] = kb_arg_role_wm_ontology
                                    arg_ids = dict()
                                    arg_ids["@id"] = property_entity_id
                                    argument["value"] = arg_ids
                                    arguments.append(argument)
                                    argument_value_entities.append(property_entity)

                            else:
                                # Time mention: temporal entities
                                temporal_entity_id, temporal_entity = self.make_value_mention_as_temporal_entities(
                                    kb_argument)
                                if temporal_entity_id is not None and temporal_entity is not None:
                                    argument = dict()
                                    argument["@type"] = "Argument"
                                    argument["type"] = kb_arg_role_wm_ontology
                                    arg_ids = dict()
                                    arg_ids["@id"] = temporal_entity_id
                                    argument["value"] = arg_ids

                                    arguments.append(argument)

                                    argument_value_entities.append(temporal_entity)
                    else:
                        mention_text = kb_argument.mention_text

                        if kb_argument in self.kb.kb_mention_to_entid:
                            arg_entity_id = self.kb.entid_to_kb_entity[self.kb.kb_mention_to_entid[kb_argument]]

                            argument = dict()
                            argument["@type"] = "Argument"
                            argument["type"] = kb_arg_role_wm_ontology
                            arg_ids = dict()
                            arg_ids["@id"] = self.kb_mention_to_serialized_entity_id[kb_argument]
                            argument["value"] = arg_ids
                            arguments.append(argument)
            event["arguments"] = arguments
            events.append(event)
        return events, argument_value_entities, kb_event_mention_to_serialized_event_ids

    def add_extractions(self, doc_uuid_to_json_ld):
        self.add_documents_and_sentence(doc_uuid_to_json_ld)

        kb_entity_in_kb_events, kb_entity_mention_in_kb_events = self.get_mentioned_kb_entity_kb_entity_mention_from_all_event()

        # add entities
        for entid, kb_entity in self.kb.entid_to_kb_entity.items():
            entities, coreference_relations = self.get_json_object_for_entity(entid, kb_entity, kb_entity_in_kb_events,
                                                                              kb_entity_mention_in_kb_events)
            doc_uuid = kb_entity.document.properties["uuid"]
            doc_uuid_to_json_ld.setdefault(doc_uuid, dict()).setdefault("extractions", list()).extend(entities)
            doc_uuid_to_json_ld.setdefault(doc_uuid, dict()).setdefault("extractions", list()).extend(
                coreference_relations)

        # add events
        self.kb_event_to_serialized_event_id = dict()
        for evid, kb_event in self.kb.evid_to_kb_event.items():
            events, argument_value_entities, kb_event_mention_to_serialized_event_ids_local = self.get_json_object_for_event(
                evid, kb_event)
            self.kb_event_to_serialized_event_id.update(kb_event_mention_to_serialized_event_ids_local)
            doc_uuid = kb_event.get_document().properties["uuid"]
            doc_uuid_to_json_ld.setdefault(doc_uuid, dict()).setdefault("extractions", list()).extend(events)
            doc_uuid_to_json_ld.setdefault(doc_uuid, dict()).setdefault("extractions", list()).extend(
                argument_value_entities)
            self.event_count += len(events)

        # add entity-entity and event-event relations
        if self.regrounding_mode is False:
            for relid, kb_relation in self.kb.relid_to_kb_relation.items():
                if kb_relation.argument_pair_type == "event-event":
                    relation, doc_uuid = self.get_json_object_for_event_event_relation(kb_relation)
                    doc_uuid_to_json_ld.setdefault(doc_uuid, dict()).setdefault("extractions", list()).append(relation)
                    self.text_causal_assertion_count += 1

    def add_ontology_meta(self, result):
        commit_hash = self.wm_external_ontology_hash
        ontology_file = "wm_flat_metadata.yml"
        if self.use_compositional_ontology:
            ontology_file = "CompositionalOntology_metadata.yml"
        result['ontologyMeta'] = {
            "URL": "https://raw.githubusercontent.com/WorldModelers/Ontologies/{}/{}".format(commit_hash,
                                                                                             ontology_file),
            "commit": commit_hash,
            "@type": "OntologyMeta"
        }

    def add_context(self, result):
        contexts = dict()

        prefix = "https://github.com/BBN-E/Hume/wiki#"
        contexts["Corpus"] = prefix + "Corpus"
        contexts["Document"] = prefix + "Document"
        # DCT
        contexts["Sentence"] = prefix + "Sentence"
        contexts["Extraction"] = prefix + "Extraction"
        contexts["Grounding"] = prefix + "Grounding"
        contexts["Provenance"] = prefix + "Provenance"
        contexts["Interval"] = prefix + "Interval"
        contexts["State"] = prefix + "State"
        contexts["Trigger"] = prefix + "Trigger"
        contexts["Argument"] = prefix + "Argument"
        contexts["TimeInterval"] = prefix + "TimeInterval"
        contexts["TimeValueMention"] = prefix + "TimeValueMention"
        contexts["PropertyMention"] = prefix + "PropertyMention"
        contexts["Count"] = prefix + "Count"
        contexts["OntologyMeta"] = prefix + "OntologyMeta"
        result["@context"] = contexts
        result["@type"] = "Corpus"

    def read_config(self, filepath):
        with open(filepath) as fp:
            config = json.load(fp)
        return config

    def read_namespaces(self):
        for namespace, URI in self.config.get('namespace', {}).items():
            self.namespace[namespace] = URI


if __name__ == "__main__":
    pass
    # if len(sys.argv) != 4:
    #     print("Usage: " + sys.argv[0] + " pickled_kb_file output_jsonld_file mode")
    #     sys.exit(1)
    #
    # logger.setLevel(logging.DEBUG)
    #
    # pickled_kb_file,output_jsonld_file,mode = sys.argv[1:]
    # with open(pickled_kb_file, "rb") as pickle_stream:
    #     logger.info("Loading pickle file...")
    #     kb = pickle.load(pickle_stream)
    #     logger.info("Done loading. Serializing...")
    #     rdf_serializer = JSONLDSerializer()
    #     rdf_serializer.serialize(kb, output_jsonld_file, mode)
