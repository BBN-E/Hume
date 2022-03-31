import sys
from collections import defaultdict

import codecs
import json
import os
import re
from datetime import datetime

from elements.kb_causal_factor import KBCausalFactor
from elements.kb_document import KBDocument
from elements.kb_entity import KBEntity
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from elements.kb_group import KBEntityGroup, KBEventGroup
from elements.kb_mention import KBMention
from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from elements.kb_sentence import KBSentence
from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention
from shared_id_manager.shared_id_manager import SharedIDManager

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_dir, "..", "..", "json_producer"))
import monetary_normalizer

import serifxml3
from serif.theory.value_mention import ValueMention

whitespace_re = re.compile(r"\s+")

import collections

EventMentionID = collections.namedtuple('EventMentionID', ['doc_id', 'char_start', 'char_end'])


class SerifXMLReader:
    month_re = re.compile(r"\d\d\d\d\-\d\d")
    year_re = re.compile(r"[12]\d\d\d")  # only events from second and third millenia
    dct_re = re.compile(r"[12]\d\d\d\d\d\d\d")

    def __init__(self):
        self.docid_to_ff_relations = None
        self.docid_to_document_properties = None
        self.serif_name_to_actor = dict()  # Supplimental cross-document linking
        self.event_key_to_cross_doc_key = dict()  # Event cross-document linking

        # Read supplimental cross-document linking file
        supplimental_actor_id_file = os.path.join(script_dir, "..", "data_files", "additional_actor_linking.txt")
        supplimental_actor_id_stream = codecs.open(supplimental_actor_id_file, 'r', encoding='utf8')
        current_actor_id = None
        for line in supplimental_actor_id_stream:
            line = line.strip()
            if line.startswith("#"):
                continue
            if line.startswith("ID:"):
                pieces = line.split()
                if len(pieces) != 2:
                    print("Error: bad line in supplimental_actor_id_file: " + line)
                    sys.exit(1)
                current_actor_id = pieces[1]
                canonical_name = None
                continue
            if line.startswith("CANONICAL_NAME:"):
                pieces = line.split()
                if len(pieces) != 2:
                    print("Error: bad line in supplimental_actor_id_file: " + line)
                    sys.exit(1)
                canonical_name = pieces[1]
                continue
            if current_actor_id is None or canonical_name is None:
                print("Error: no current actor id or canonical_name when loading supplimental_actor_id_file")
                sys.exit(1)
            self.serif_name_to_actor[line.lower()] = (current_actor_id, canonical_name,)
        supplimental_actor_id_stream.close()

        # Read supplimental canonical name change file
        self.canonical_name_change = dict()
        name_file = os.path.join(script_dir, "..", "data_files", "canonical_name_change.txt")
        name_stream = codecs.open(name_file, 'r', encoding='utf8')
        for line in name_stream:
            line = line.strip()
            if len(line) == 0 or line.startswith("#"):
                continue
            pieces = line.split("\t")
            if len(pieces) != 2:
                print("Malformed line in canonical name change file")
                sys.exit(1)
            self.canonical_name_change[pieces[0]] = pieces[1]
        name_stream.close()

    # cross-doc event coreference
    def read_event_coreference_file(self, event_coreference_file):

        # If event_coreference_file is populated, use it.
        if len(event_coreference_file) > 0 and event_coreference_file != 'NULL':
            event_coreference_dict = json.load(open(event_coreference_file))
            # event_coreference_dict has two levels of dictionaries
            # The first level differentiates between test and ground_truth methods
            # The second level differentiates between approaches tried

            list_of_list_of_event_keys = event_coreference_dict.values()[0].values()[0]

            for i, list_of_event_keys in enumerate(list_of_list_of_event_keys):
                for event_key in list_of_event_keys:
                    self.event_key_to_cross_doc_key[event_key] = i

    def read_metadata_file(self, metadata_file):
        self.docid_to_document_properties = dict()
        with open(metadata_file, 'r') as m:
            for line in m:
                pieces = line.strip().split("\t")
                document_properties = dict()
                docid = pieces[0]
                document_properties["docid"] = docid
                document_properties["doc_type"] = pieces[4].strip()
                document_properties["source"] = re.sub("^\./", "", re.sub("\n", " ", pieces[1]))
                document_properties["uuid"] = pieces[6]
                document_properties["filename"] = re.sub("\n", " ", pieces[5])
                document_properties["credibility"] = float(pieces[3])
                date_created_str = pieces[2]
                if date_created_str != "UNKNOWN":
                    document_properties["date_created"] = datetime.strptime(date_created_str, "%Y%m%d").strftime(
                        "%Y-%m-%d")
                else:
                    document_properties["date_created"] = "UNKNOWN"
                document_properties["offset"] = 0
                if len(pieces) > 7:
                    document_properties["offset"] = int(pieces[7])
                document_properties["author"] = "UNKNOWN"
                if len(pieces) > 8:
                    document_properties["author"] = pieces[8]
                document_properties["online_source"] = "UNKNOWN"
                if len(pieces) > 9:
                    document_properties["online_source"] = pieces[9]
                if len(pieces) > 10:
                    print("Too many pieces")
                    sys.exit(1)
                self.docid_to_document_properties[docid] = document_properties

    def add_sentences(self, kb_document, serif_doc):
        for sentence in serif_doc.sentences:
            sentid = SharedIDManager.get_in_document_id("Sentence", serif_doc.docid)
            kb_sentence = KBSentence(sentid, sentence.start_char, sentence.end_char, sentence.text,
                                     sentence.get_original_text_substring(sentence.start_char, sentence.end_char),
                                     sentence.sent_no)
            kb_document.add_sentence(kb_sentence)

    # def find_NP_for_event_triggers(self, sentence):
    #     em2nptext = dict()
    #     # print "sentence=" + sentence.text.replace("\n", "")
    #     st = sentence.sentence_theories[0]
    #     for serif_em in st.event_mention_set:
    #         span_covering_ratio = 20
    #         for mention in sentence.mention_set:
    #             if mention.mention_type.value != "pron" and mention.mention_type.value != "name":
    #                 if mention.start_char<=serif_em.anchor_node.start_char and mention.end_char>=serif_em.anchor_node.end_char:
    #                     cur_span_covering_ratio=(mention.end_char-mention.start_char+1)/(serif_em.anchor_node.end_char-serif_em.anchor_node.start_char+1)
    #                     # find the minimally covering span
    #                     if cur_span_covering_ratio<span_covering_ratio:
    #                         em2nptext[serif_em]=mention.text
    #     return em2nptext
    #
    # def find_NP_for_event_mention_triggers(self, serif_em, sentence):
    #     span_covering_ratio = 20 # why 20? isn't it too large?
    #     for mention in sentence.mention_set:
    #         if mention.mention_type.value != "pron" and mention.mention_type.value != "name":
    #             if mention.start_char <= serif_em.anchor_node.start_char and mention.end_char >= serif_em.anchor_node.end_char:
    #                 cur_span_covering_ratio = (mention.end_char - mention.start_char + 1) / (
    #                 serif_em.anchor_node.end_char - serif_em.anchor_node.start_char + 1)
    #                 # find the minimally covering span
    #                 if cur_span_covering_ratio < span_covering_ratio:
    #                     return mention.text
    #     return None

    # Entity is a CauseExResults entity
    def get_canonical_name(self, serif_entity, serif_actor_entity):
        if serif_actor_entity is not None:
            return serif_actor_entity.actor_name
        # No actor match, take longest name
        longest_name = ""
        for mention in serif_entity.mentions:
            if mention.mention_type.value == "name":
                mention_head_text = mention.get_original_text_substring(mention.head.start_char, mention.head.end_char)
                mention_head_text = whitespace_re.sub(" ", mention_head_text).replace("\n", " ").replace("\t", " ")
                if len(mention_head_text) > len(longest_name):
                    longest_name = mention_head_text
        if longest_name == "":
            return None
        return longest_name

    def build_mention_to_actor_mentions_map(self, serif_doc):
        mention_to_actor_mentions_map = defaultdict(list)
        for s in serif_doc.sentences:
            if s.actor_mention_set is not None:
                for am in s.actor_mention_set:
                    mention_to_actor_mentions_map[am.mention].append(am)
        return mention_to_actor_mentions_map

    def add_event_mention_arguments(self, kb_event_mention, serif_event_mention, mention_map, kb_document, docid,
                                    serif_valid_to_kb_valmention, serif_doc):
        for argument in serif_event_mention.arguments:
            mention_or_value_mention = None
            if argument.mention is not None:
                mention_or_value_mention = mention_map.get(argument.mention)
            if argument.value_mention is not None:
                vm = argument.value_mention
                if kb_event_mention.is_particular_event_argument_existed(argument.role, vm.start_char,
                                                                         vm.end_char) is False:
                    value_mention_id = SharedIDManager.get_in_document_id("ValueMention", docid)
                    if vm.value_type == "Numeric.Money":
                        currency_type, currency_amount, currency_minimum, currency_maximum = monetary_normalizer.normalize(
                            vm.text)
                        mention_or_value_mention = KBMoneyValueMention(value_mention_id, vm.value_type, vm.text,
                                                                       kb_document, vm.start_char, vm.end_char,
                                                                       currency_type, currency_amount, currency_minimum,
                                                                       currency_maximum,
                                                                       kb_document.sentences[vm.sent_no],
                                                                       vm.get_original_text_substring(vm.start_char,
                                                                                                      vm.end_char))
                    elif vm.value_type == "TIMEX2.TIME":
                        mention_or_value_mention = KBTimeValueMention(value_mention_id, vm.value_type, vm.text,
                                                                      kb_document, vm.start_char, vm.end_char,
                                                                      self.get_normalized_time(serif_doc, vm),
                                                                      kb_document.sentences[vm.sent_no],
                                                                      vm.get_original_text_substring(vm.start_char,
                                                                                                     vm.end_char))
                    else:
                        mention_or_value_mention = KBValueMention(value_mention_id, vm.value_type, vm.text, kb_document,
                                                                  vm.start_char, vm.end_char,
                                                                  kb_document.sentences[vm.sent_no],
                                                                  vm.get_original_text_substring(vm.start_char,
                                                                                                 vm.end_char))
                    serif_valid_to_kb_valmention[value_mention_id] = mention_or_value_mention
            if mention_or_value_mention is not None:
                if isinstance(mention_or_value_mention, KBValueMention):
                    if kb_event_mention.is_particular_event_argument_existed(argument.role,
                                                                             mention_or_value_mention.head_start_char,
                                                                             mention_or_value_mention.head_end_char) is False:
                        kb_event_mention.add_argument(argument.role, mention_or_value_mention, argument.score)
                elif kb_event_mention.is_particular_event_argument_existed(argument.role,
                                                                           mention_or_value_mention.start_char,
                                                                           mention_or_value_mention.end_char) is False:
                    kb_event_mention.add_argument(argument.role, mention_or_value_mention, argument.score)

    def get_best_month_from_value_mention(self, vm, best_year_only=False):
        nt = vm.get_normalized_time()
        if nt is None:
            return None
        if best_year_only:
            match = SerifXMLReader.year_re.match(nt)
        else:
            match = SerifXMLReader.month_re.match(nt)
        if match is None:
            return None
        return match.group(0)

    def overlap(self, vm, m):
        start = None
        end = None
        if m.syn_node is None:
            start = m.start_token.start_char
            end = m.end_token.end_char
        else:
            start = m.syn_node.start_token.start_char
            end = m.syn_node.end_token.end_char
        return ((vm.start_token.start_char >= start and vm.start_token.start_char <= end) or
                (start >= vm.start_token.start_char and start <= vm.end_token.end_char))

    def get_best_month_from_mention(self, mention, sentence):
        # look for overlapping value mention
        for vm in sentence.value_mention_set or ():
            if self.overlap(vm, mention):
                nt = vm.get_normalized_time()
                if nt is None:
                    continue
                match = SerifXMLReader.month_re.match(nt)
                if match is None:
                    continue
                return match.group(0)
        return None

    # Look to find the best month e.g. 2020-08 for a particular event based 
    # on slots, dates in the sentence, and document date
    def set_month_property(self, kb_event_mention, kb_document, mention_map, serif_em, serif_doc):
        best_month = None
        sentence = serif_doc.sentences[serif_em.anchor_node.sent_no] if serif_em.anchor_node is not None else \
            serif_doc.sentences[serif_em.sentence.sent_no]

        # Check for good Time argument
        for argument in serif_em.arguments:
            time_value_mention = None
            if argument.role == "Time" or argument.role == "has_time" or argument.role == "Time-Within":
                if (argument.value_mention is not None):
                    best_month = self.get_best_month_from_value_mention(argument.value_mention)
                elif (argument.mention is not None):
                    best_month = self.get_best_month_from_mention(argument.mention, sentence)
                if best_month is not None:
                    break
        if best_month is not None:
            kb_event_mention.properties["best_month"] = best_month
            kb_event_mention.properties["best_month_method"] = "argument"
            return

        # Check for month mentioned in sentence
        for vm in sentence.value_mention_set or ():
            normalized_time = vm.get_normalized_time()
            if normalized_time is None:
                continue
            m = SerifXMLReader.month_re.match(normalized_time)
            if m is not None:
                kb_event_mention.properties["best_month"] = m.group(0)
                kb_event_mention.properties["best_month_method"] = "sentence"
                return

        # Use document date as fallback
        m = SerifXMLReader.month_re.match(kb_document.properties["date_created"])
        if m is not None:
            kb_event_mention.properties["best_month"] = m.group(0)
            kb_event_mention.properties["best_month_method"] = "document"
            return

    @staticmethod
    def get_event_mention_semantic_phrase_info(serif_em, serif_sentence_tokens):
        serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end, serif_em_semantic_phrase_text = None, None, None
        # Get from anchor
        anchor_node = serif_em.anchor_node
        if anchor_node is not None:
            serif_em_semantic_phrase_char_start = anchor_node.start_token.start_char
            serif_em_semantic_phrase_char_end = anchor_node.end_token.end_char
            serif_em_semantic_phrase_text = anchor_node.text

        # Reset from semantic phrase info if it exists
        if serif_em.semantic_phrase_start is not None and serif_em.semantic_phrase_end is not None:
            serif_em_semantic_phrase_char_start = serif_sentence_tokens[int(serif_em.semantic_phrase_start)].start_char
            serif_em_semantic_phrase_char_end = serif_sentence_tokens[int(serif_em.semantic_phrase_end)].end_char
            serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[
                                                                     int(serif_em.semantic_phrase_start):int(
                                                                         serif_em.semantic_phrase_end) + 1])

        return serif_em_semantic_phrase_text, serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end

    @staticmethod
    def get_event_mention_semantic_phrase_origin_str(serif_em, serif_sentence_tokens):
        serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end = None, None
        start_token_idx, end_token_idx = None, None
        # Get from anchor
        anchor_node = serif_em.anchor_node
        if anchor_node is not None:
            serif_em_semantic_phrase_char_start = anchor_node.start_token.start_char
            serif_em_semantic_phrase_char_end = anchor_node.end_token.end_char
            start_token_idx = anchor_node.start_token.index()
            end_token_idx = anchor_node.end_token.index()

        # Reset from semantic phrase info if it exists
        if serif_em.semantic_phrase_start is not None and serif_em.semantic_phrase_end is not None:
            serif_em_semantic_phrase_char_start = serif_sentence_tokens[int(serif_em.semantic_phrase_start)].start_char
            serif_em_semantic_phrase_char_end = serif_sentence_tokens[int(serif_em.semantic_phrase_end)].end_char
            start_token_idx = int(serif_em.semantic_phrase_start)
            end_token_idx = int(serif_em.semantic_phrase_end)

        serif_em_semantic_phrase_text = serif_em.owner_with_type("Sentence").get_original_text_substring(
            serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end)
        return serif_em_semantic_phrase_text, start_token_idx, end_token_idx

    @staticmethod
    def get_event_mention_types_and_confidences(serif_em):
        ret = list()
        for event_type in serif_em.event_types:
            ret.append([event_type.event_type, event_type.score])
        return ret

    @staticmethod
    def get_causal_factors(serif_em, docid):
        ret = list()

        for factor_type in serif_em.factor_types:
            cf_id = SharedIDManager.get_in_document_id("CausalFactor", docid)
            trend = "Unknown"
            if factor_type.trend == serifxml3.Trend.Increase:
                trend = "Increase"
            elif factor_type.trend == serifxml3.Trend.Decrease:
                trend = "Decrease"
            elif factor_type.trend == serifxml3.Trend.Stable:
                trend = "Stable"
            new_causal_factor = KBCausalFactor(cf_id, factor_type.event_type, trend, factor_type.score,
                                               factor_type.magnitude)
            ret.append(new_causal_factor)

        return ret

    def get_mention_to_entities(self, serif_doc):
        ret = dict()
        for entity in serif_doc.entity_set or ():
            for mention in entity.mentions:
                ret.setdefault(mention,set()).add(entity)
        return ret

    def read(self, kb, batch_file_dir, mode, event_coreference_file):
        print("SerifXMLReader READ")

        metadata_file = os.path.join(batch_file_dir, "metadata.txt")
        serifxml_list = os.path.join(batch_file_dir, "serifxml.list")
        self.read_event_coreference_file(event_coreference_file)
        self.read_metadata_file(metadata_file)

        # Read event types file
        # event_types_file = serif_accent_event_type_file_path
        # @ hqiu : Pending delete start
        # self.event_code_to_name = dict()  # CAMEO event code -> description of event
        # if mode != "WorldModelers":
        #     if not os.path.exists(event_types_file):
        #         print
        #         "Could not find: " + event_types_file
        #         sys.exit(1)
        #     event_code_re = re.compile(r'code "(\d+)"')
        #     event_name_re = re.compile(r'name "(.*?)"')
        #     events_file_stream = codecs.open(event_types_file, encoding='utf8')
        #     event_code = None
        # from resolvers.external_ontology_cache_grounder import ExternalOntologyCacheGrounder
        #     for line in events_file_stream:
        #         code_m = event_code_re.search(line)
        #         if code_m:
        #             event_code = code_m.group(1)
        #             continue
        #         name_m = event_name_re.search(line)
        #         if name_m:
        #             event_name = name_m.group(1)
        #             self.event_code_to_name[event_code] = event_name
        #             event_code = None
        #     events_file_stream.close()
        # @ hqiu : Pending delete end
        print("Reading from: " + serifxml_list)
        original_num_eerms_in_serif = 0
        num_eerms_from_mtdp = 0
        serifxml_files = []
        with open(serifxml_list) as fp:
            for i in fp:
                i = i.strip()
                serifxml_files.append(i)

        files_length = len(serifxml_files)
        count = 0

        actor_id_to_entity_group = dict()

        for serifxml_file in serifxml_files:
            mention_map = dict()  # maps serif mention to KBMention
            event_map = dict()  # maps serif event mention (or icews event mention) to (KBEvent, KBEventMention, SentenceTheory)

            count += 1
            serif_doc = serifxml3.Document(serifxml_file)
            docid = serif_doc.docid
            print(
                "SerifXMLReader producing KB objects in: " + docid + " (" + str(count) + "/" + str(files_length) + ")")

            kb_document = KBDocument(docid, self.docid_to_document_properties[docid])
            kb.add_document(kb_document)

            self.add_sentences(kb_document, serif_doc)

            serif_entity_to_serif_actor_entity = self.get_entity_to_actor_entity_cache(serif_doc)
            serif_entid_to_kb_ent = {}
            serif_valid_to_kb_valmention = {}

            # Entities/Mentions
            if mode.lower() != "covid":
                for serif_entity in serif_doc.entity_set or ():
                    country_iso_code = None  # For geonames where we can determine its country
                    entid = SharedIDManager.get_in_document_id("Entity", docid)
                    serif_actor_entity = serif_entity_to_serif_actor_entity.get(serif_entity)

                    canonical_name = self.get_canonical_name(serif_entity, serif_actor_entity)
                    serif_entity_type = serif_entity.entity_type
                    kb_entity = KBEntity(entid, canonical_name, serif_entity_type + "." + serif_entity.entity_subtype)
                    if serif_entity.mention_confidences:
                        mention_confidences = serif_entity.mention_confidences.split()
                    else:
                        mention_confidences = ["OtherDesc"] * serif_entity.num_mentions()

                    if serif_actor_entity is not None and (
                            serif_entity_type == "GPE" or serif_entity_type == "LOC" or serif_entity_type == "FAC"):
                        for serif_actor_mention in serif_actor_entity.actor_mentions:
                            if serif_actor_mention.geo_uid is not None and len(
                                    serif_actor_mention.geo_uid.strip()) != 0:
                                kb_entity.properties["geonameid"] = serif_actor_mention.geo_uid

                            if serif_actor_mention.geo_latitude and serif_actor_mention.geo_longitude:
                                kb_entity.properties["latitude"] = serif_actor_mention.geo_latitude
                                kb_entity.properties["longitude"] = serif_actor_mention.geo_longitude

                            if (serif_actor_mention.geo_country is not None and
                                    serif_actor_mention.country_info_actor_id != serif_actor_mention.actor_uid):
                                country_iso_code = serif_actor_mention.geo_country
                                break

                    mention_count = 0
                    longest_name = None
                    longest_name_length = None
                    shortest_desc = None
                    shortest_desc_length = None
                    pron = None
                    for serif_mention in serif_entity.mentions:

                        link_confidence = mention_confidences[mention_count]
                        mentid = SharedIDManager.get_in_document_id("Mention", docid)
                        kb_mention = KBMention(
                            mentid,
                            serif_mention.entity_type, serif_mention.mention_type.value,
                            serif_mention.text,
                            serif_mention.head.text if serif_mention.head is not None else serif_mention.text,
                            kb_document,
                            serif_mention.syn_node.start_char, serif_mention.syn_node.end_char,
                            serif_mention.head.start_char if serif_mention.head is not None else serif_mention.start_char,
                            serif_mention.head.end_char if serif_mention.head is not None else serif_mention.end_char,
                            kb_document.sentences[serif_mention.sent_no], link_confidence,
                            serif_mention.syn_node.get_original_text_substring(serif_mention.syn_node.start_char,
                                                                               serif_mention.syn_node.end_char),
                            serif_mention.head.get_original_text_substring(serif_mention.head.start_char,
                                                                           serif_mention.head.end_char) if serif_mention.head is not None else serif_mention.syn_node.get_original_text_substring(
                                serif_mention.syn_node.start_char,
                                serif_mention.syn_node.end_char))
                        mention_map[serif_mention] = kb_mention
                        kb.add_mention_to_entity(kb_entity, kb_mention)

                        if serif_mention.mention_type.value == "name":
                            if longest_name is None or len(serif_mention.head.text) > longest_name_length:
                                longest_name = kb_mention
                                longest_name_length = len(serif_mention.head.text)
                        elif serif_mention.mention_type.value != "pron":
                            if shortest_desc is None or len(serif_mention.text) < shortest_desc_length:
                                shortest_desc = kb_mention
                                shortest_desc_length = len(serif_mention.text)
                        elif serif_mention.mention_type.value == "pron" and pron is None:
                            pron = kb_mention

                    if longest_name is not None:
                        kb_entity.properties["canonical_mention"] = longest_name
                    elif shortest_desc is not None:
                        kb_entity.properties["canonical_mention"] = shortest_desc
                    elif pron is not None:  # Might matter for first person pronouns(?)
                        kb_entity.properties["canonical_mention"] = pron

                    kb.add_entity(kb_entity)
                    serif_entid_to_kb_ent[serif_entity.id] = kb_entity

                    # Cross-document entities
                    actor_id = None
                    actor_canonical_name = None
                    if serif_actor_entity is not None:
                        actor_id = serif_actor_entity.actor_uid
                        actor_canonical_name = serif_actor_entity.actor_name
                        if actor_canonical_name in self.canonical_name_change:
                            actor_canonical_name = self.canonical_name_change[actor_canonical_name]
                    elif canonical_name is not None and canonical_name.lower() in self.serif_name_to_actor:
                        actor_id, actor_canonical_name = self.serif_name_to_actor[canonical_name.lower()]

                    if actor_id is None:
                        # Will not coreference with any other KBEntity
                        entity_group_id = KBEntityGroup.generate_id(None)
                        kb_entity_group = KBEntityGroup(entity_group_id, canonical_name, None)
                        kb_entity_group.members.append(kb_entity)
                        kb.add_entity_group(kb_entity_group)
                    elif actor_id in actor_id_to_entity_group:
                        # We've seen this cross-document entity before
                        kb_entity_group = actor_id_to_entity_group[actor_id]
                        kb_entity_group.members.append(kb_entity)
                    else:
                        # New cross-document entity
                        entity_group_id = KBEntityGroup.generate_id(actor_id)
                        kb_entity_group = KBEntityGroup(entity_group_id, actor_canonical_name, actor_id)
                        kb_entity_group.members.append(kb_entity)
                        kb.add_entity_group(kb_entity_group)
                        actor_id_to_entity_group[actor_id] = kb_entity_group
                        # We can place geoname inside a country
                        if country_iso_code is not None:
                            kb_entity_group.properties["country_iso_code"] = country_iso_code

            # Sentence-level Mentions/ActorMentions
            if mode.lower() == "covid":
                serif_entity_to_geoname_serif_actor_entities = self.get_entity_to_actor_entities_cache(serif_doc,
                                                                                                       source_note="geonames")
                serif_entity_to_wikidata_serif_actor_entities = self.get_entity_to_actor_entities_cache(serif_doc,
                                                                                                        source_note="wikidata")
                serif_mention_to_entities = self.get_mention_to_entities(serif_doc)
                singlton_entity_mentions = set()
                corefered_entity_mentions = set()
                for serif_sentence in serif_doc.sentences:
                    for serif_mention in serif_sentence.mention_set:
                        serif_entity = serif_mention.entity()
                        if serif_entity is not None:
                            corefered_entity_mentions.add(serif_mention)
                        else:
                            # Sometimes CSerif will produce this
                            singlton_entity_mentions.add(serif_mention)

                # Sometimes CSerif will produce this
                for serif_mention in singlton_entity_mentions:
                    entid = SharedIDManager.get_in_document_id("Entity", docid)
                    if serif_mention.start_token is not None:
                        canonical_name = serif_mention.get_original_text_substring(serif_mention.start_token.start_char,
                                                                                   serif_mention.end_token.end_char)
                    else:
                        canonical_name = serif_mention.get_original_text_substring(serif_mention.syn_node.start_char,
                                                                                   serif_mention.syn_node.end_char)
                    kb_entity = KBEntity(entid, canonical_name,
                                         "UNDEF",
                                         conceiver_entity_links=[])
                    mentid = SharedIDManager.get_in_document_id("Mention", docid)
                    kb_mention = KBMention(
                        mentid,
                        serif_mention.entity_type, serif_mention.mention_type.value,
                        serif_mention.text,
                        serif_mention.head.text if serif_mention.head is not None else serif_mention.text, kb_document,
                        serif_mention.syn_node.start_char if serif_mention.syn_node is not None else serif_mention.start_token.start_char,
                        serif_mention.syn_node.end_char if serif_mention.syn_node is not None else serif_mention.end_token.end_char,
                        serif_mention.head.start_char if serif_mention.head is not None else serif_mention.start_char,
                        serif_mention.head.end_char if serif_mention.head is not None else serif_mention.end_char,
                        kb_document.sentences[serif_mention.sent_no], 0.5,
                        serif_mention.syn_node.get_original_text_substring(serif_mention.syn_node.start_char,
                                                                           serif_mention.syn_node.end_char) if serif_mention.syn_node is not None else serif_mention.get_original_text_substring(
                            serif_mention.start_token.start_char,
                            serif_mention.end_token.end_char),
                        serif_mention.head.get_original_text_substring(serif_mention.head.start_char,
                                                                       serif_mention.head.end_char) if serif_mention.head is not None else serif_mention.get_original_text_substring(
                            serif_mention.start_token.start_char,
                            serif_mention.end_token.end_char))
                    mention_map[serif_mention] = kb_mention

                    kb.add_mention_to_entity(kb_entity, kb_mention)
                    kb.add_entity(kb_entity)

                # mention_to_actor_mentions_map = self.build_mention_to_actor_mentions_map(serif_doc)
                # @brozonoy's original logic for pyserif
                for serif_mention in corefered_entity_mentions:

                    # create singleton entity
                    entid = SharedIDManager.get_in_document_id("Entity", docid)

                    # serif_entity = serif_mention.entity()
                    serif_entities = serif_mention_to_entities[serif_mention]
                    geoname_actor_entities = list()
                    for serif_entity in serif_entities:
                        geoname_actor_entities.extend(serif_entity_to_geoname_serif_actor_entities[serif_entity])

                    # actor_mentions = mention_to_actor_mentions_map.get(serif_mention, [])
                    # geonames_for_mention = [am.actor_name for am in actor_mentions if am.source_note =="geonames"]
                    geonames_for_mention = [ae.actor_name for ae in geoname_actor_entities]

                    if len(geonames_for_mention) > 0:
                        canonical_name = geonames_for_mention[0]
                    else:
                        if serif_mention.start_token is not None:
                            canonical_name = serif_mention.get_original_text_substring(
                                serif_mention.start_token.start_char,
                                serif_mention.end_token.end_char)
                        else:
                            canonical_name = serif_mention.get_original_text_substring(
                                serif_mention.syn_node.start_char,
                                serif_mention.syn_node.end_char)

                    wikidata_actor_entities = list()
                    for serif_entity in serif_entities:
                        wikidata_actor_entities.extend(serif_entity_to_wikidata_serif_actor_entities[serif_entity])
                    # conceiver_entity_links = [am.actor_name for am in actor_mentions if am.source_note == "wikidata"]
                    conceiver_entity_links = [ae.actor_name for ae in wikidata_actor_entities]

                    # serif_entity_type = serif_mention.entity_type
                    entity_type_to_cnt = dict()
                    for entity in serif_entities:
                        if entity.entity_type !=  "UNDET":
                            entity_type_to_cnt[entity.entity_type] = entity_type_to_cnt.get(entity.entity_type,0)+1
                    if len(entity_type_to_cnt) > 0:
                        serif_entity_type = sorted(entity_type_to_cnt.items(),key=lambda x:x[1],reverse=True)[0][0]
                    else:
                        serif_entity_type = "UNDET"

                    kb_entity = KBEntity(entid, canonical_name,
                                         serif_entity_type + "." + serif_mention.entity_subtype,
                                         conceiver_entity_links=conceiver_entity_links)

                    # if len(geonames_for_mention) > 0:
                    #     kb_entity.properties["geonameid"] = geonames_for_mention[0]

                    mentid = SharedIDManager.get_in_document_id("Mention", docid)
                    kb_mention = KBMention(
                        mentid,
                        serif_entity_type, serif_mention.mention_type.value,
                        serif_mention.text,
                        serif_mention.head.text if serif_mention.head is not None else serif_mention.text, kb_document,
                        serif_mention.syn_node.start_char if serif_mention.syn_node is not None else serif_mention.start_token.start_char,
                        serif_mention.syn_node.end_char if serif_mention.syn_node is not None else serif_mention.end_token.end_char,
                        serif_mention.head.start_char if serif_mention.head is not None else serif_mention.start_char,
                        serif_mention.head.end_char if serif_mention.head is not None else serif_mention.end_char,
                        kb_document.sentences[serif_mention.sent_no], 0.5,
                        serif_mention.syn_node.get_original_text_substring(serif_mention.syn_node.start_char,
                                                                           serif_mention.syn_node.end_char) if serif_mention.syn_node is not None else serif_mention.get_original_text_substring(
                            serif_mention.start_token.start_char,
                            serif_mention.end_token.end_char),
                        serif_mention.head.get_original_text_substring(serif_mention.head.start_char,
                                                                       serif_mention.head.end_char) if serif_mention.head is not None else serif_mention.get_original_text_substring(
                            serif_mention.start_token.start_char,
                            serif_mention.end_token.end_char))
                    mention_map[serif_mention] = kb_mention

                    kb.add_mention_to_entity(kb_entity, kb_mention)
                    kb.add_entity(kb_entity)
                    # serif_entid_to_kb_ent[serif_entity.id] = kb_entity

            # #----------------------------------------------------------------------------------------------------------#
            # # TODO add in singleton mentions
            # #  We can get rid of this block because we only want mentions with a serifxml Entity over them,
            # #  and "MTDP_CONCEIVER" dummy mentions only get stored in a sentence's mention_set anyway, so we don't
            # #  store them in kb because we only aggregate mentions coming from entities
            # mention_to_actor_mentions_map = self.build_mention_to_actor_mentions_map(serif_doc)
            # for s in serif_doc.sentences:
            #     for serif_mention in s.mention_set:
            #         entid = SharedIDManager.get_in_document_id("Entity", docid)
            #         serif_entity_type = serif_mention.entity_type
            #         serif_entity_subtype = serif_mention.entity_subtype
            #
            #         actor_mentions = mention_to_actor_mentions_map.get(serif_mention, [])
            #         canonical_name = "|||".join([am.actor_name for am in actor_mentions])
            #         #
            #         # canonical_name = None
            #         # if serif_mention.mention_type.value == "name":
            #         #     mention_head_text = serif_mention.get_original_text_substring(serif_mention.head.start_char, serif_mention.head.end_char)
            #         #     mention_head_text = whitespace_re.sub(" ", mention_head_text).replace("\n", " ").replace("\t", " ")
            #         #     canonical_name = mention_head_text
            #         kb_entity = KBEntity(entid, canonical_name, serif_entity_type + "." + serif_entity_subtype)
            #         link_confidence = "OtherDesc"
            #         mentid = SharedIDManager.get_in_document_id("Mention", docid)
            #         kb_mention = KBMention(
            #             mentid,
            #             serif_mention.entity_type, serif_mention.mention_type.value,
            #             serif_mention.text, serif_mention.head.text, kb_document,
            #             serif_mention.syn_node.start_char, serif_mention.syn_node.end_char,
            #             serif_mention.head.start_char, serif_mention.head.end_char,
            #             kb_document.sentences[serif_mention.sent_no], link_confidence,serif_mention.syn_node.get_original_text_substring(serif_mention.syn_node.start_char, serif_mention.syn_node.end_char),serif_mention.head.get_original_text_substring(serif_mention.head.start_char, serif_mention.head.end_char))
            #         mention_map[serif_mention] = kb_mention
            #         kb.add_mention_to_entity(kb_entity, kb_mention)
            # #----------------------------------------------------------------------------------------------------------#

            # Relations
            for serif_sentence in serif_doc.sentences:
                st = serif_sentence.sentence_theories[0]
                for serif_relation_mention in st.rel_mention_set or ():

                    left_kb_mention = mention_map.get(serif_relation_mention.left_mention)
                    right_kb_mention = mention_map.get(serif_relation_mention.right_mention)
                    if left_kb_mention is None or right_kb_mention is None:
                        # one of the mentions didn't make it in to an entity, so we don't
                        # have the required information to make a KBRelation
                        continue

                    relation_id = SharedIDManager.get_in_document_id("Relation", docid)
                    rel_mention_id = SharedIDManager.get_in_document_id("RelationMention", docid)
                    kb_relation = KBRelation(relation_id, "entity-entity", serif_relation_mention.type,
                                             kb.kb_mention_to_entid[left_kb_mention],
                                             kb.kb_mention_to_entid[right_kb_mention])
                    kb_relation.add_relation_mention(
                        KBRelationMention(rel_mention_id, left_kb_mention, right_kb_mention,
                                          self.get_snippet(serif_doc, st), kb_document))
                    kb.add_relation(kb_relation)

            if mode != "WorldModelers":
                # ACCENT Events

                # @ hqiu : Pending delete start
                # for serif_iem in serif_doc.icews_event_mention_set:
                #     event_id = SharedIDManager.get_in_document_id("Event", docid)
                #     event_mention_id = SharedIDManager.get_in_document_id("EventMention", docid)
                #     event_type = serif_iem.event_code + " " + self.event_code_to_name[serif_iem.event_code]
                #     kb_event = KBEvent(event_id, event_type)
                #
                #     source_actor_mention = None
                #     target_actor_mention = None
                #
                #     for participant in serif_iem.participants:
                #         if participant.role == "SOURCE":
                #             source_actor_mention = participant.actor
                #         elif participant.role == "TARGET":
                #             target_actor_mention = participant.actor
                #     participants = dict()
                #     sentence_theory = None
                #     snippet = ""
                #     if source_actor_mention:
                #         sentence_theory = source_actor_mention.sentence_theory
                #     elif target_actor_mention:
                #         sentence_theory = target_actor_mention.sentence_theory
                #     if not sentence_theory:
                #         continue
                #
                #     snippet = self.get_snippet(serif_doc, sentence_theory)
                #     proposition_info = []
                #     for prop in serif_iem.propositions:
                #         if prop.head is not None:
                #             proposition_info.append((prop.head.text, prop.head.start_char, prop.head.end_char,))
                #
                #     kb_event_mention = KBEventMention(event_mention_id, kb_document, event_type, None, None, None, snippet, kb_document.sentences[sentence_theory.parse.sent_no], proposition_info, "ACCENT")
                #     kb_event_mention.properties["tense"] = serif_iem.event_tense
                #
                #     if source_actor_mention:
                #         mention = mention_map.get(source_actor_mention.mention)
                #         if mention is not None:
                #             kb_event_mention.add_argument("Source", mention)
                #     if target_actor_mention:
                #         mention = mention_map.get(target_actor_mention.mention)
                #         if mention is not None:
                #             kb_event_mention.add_argument("Target", mention)
                #     if len(kb_event_mention.arguments) == 0:
                #         # Could not find either Source or Target
                #         continue
                #     if serif_iem.time_value_mention is not None:
                #         vm = serif_iem.time_value_mention
                #         value_mention_id = SharedIDManager.get_in_document_id("ValueMention", docid)
                #         kb_value_mention = KBTimeValueMention(value_mention_id, vm.value_type, vm.text, kb_document, vm.start_char, vm.end_char, self.get_normalized_time(serif_doc, vm), kb_document.sentences[vm.sent_no])
                #         kb_event_mention.add_argument("Time", kb_value_mention)
                #
                #     kb_event.add_event_mention(kb_event_mention)
                #     kb.add_event(kb_event)
                #     event_map[serif_iem] = (kb_event, kb_event_mention, sentence_theory,)

                # @ hqiu : Pending delete end
                seen_fact_info = set()

                # Look for certain types of facts and create events out of them
                # The FactReader handles other types of facts

                fact_set = serif_doc.fact_set
                if fact_set is None:
                    fact_set = []
                for fact in fact_set:
                    if fact.fact_type != "Quotation":
                        continue
                    speaker_kb_mention = None
                    quotation_serif_argument = None
                    for argument in fact.mention_fact_arguments:
                        serif_mention = argument.mention
                        if serif_mention not in mention_map:
                            continue
                        speaker_kb_mention = mention_map[serif_mention]
                    for argument in fact.text_span_fact_arguments:
                        quotation_serif_argument = argument
                    if speaker_kb_mention is None or quotation_serif_argument is None:
                        continue

                    # Duplicate removal
                    key = (speaker_kb_mention, quotation_serif_argument.start_sentence,)
                    if key in seen_fact_info:
                        continue
                    seen_fact_info.add(key)

                    sent_no = quotation_serif_argument.start_sentence
                    sentence = serif_doc.sentences[sent_no]
                    st = sentence.sentence_theories[0]
                    snippet = self.get_snippet(serif_doc, st)

                    # Create generic Quote "event" from quotation_serif_argument
                    # It's not really an event, we just ontologize as an event so 
                    # it can be the topic of a Communication event.
                    # @hqiu. This is turned off due to Quotation is not on the ontology hense no groundable.
                    print("[ALERT] We turned off Quote event because it's not on the event ontology")
                    # event_type = "Quote"
                    # event_id = SharedIDManager.get_in_document_id("Event", docid)
                    # event_mention_id = SharedIDManager.get_in_document_id("EventMention", docid)
                    # kb_quote_event = KBEvent(event_id, event_type)
                    # kb_quote_event_mention = KBEventMention(event_mention_id, kb_document, event_type, None, None, None, snippet, kb_document.sentences[sent_no], [], "FACTFINDER")
                    # kb_quote_event_mention.add_argument("Speaker", speaker_kb_mention)
                    # kb_quote_event.add_event_mention(kb_quote_event_mention)
                    # kb.add_event(kb_quote_event)
                    # group_id = KBEventGroup.generate_id(None)
                    # ev_group = KBEventGroup(group_id)
                    # ev_group.members.append(kb_quote_event)
                    # kb.add_event_group(ev_group)
                    #
                    # # Create Communication event that has topic of the Quote event
                    # event_type = "Communication"
                    # event_id = SharedIDManager.get_in_document_id("Event", docid)
                    # event_mention_id = SharedIDManager.get_in_document_id("EventMention", docid)
                    # kb_communication_event = KBEvent(event_id, event_type)
                    # kb_communication_event_mention = KBEventMention(event_mention_id, kb_document, event_type, None, None, None, snippet, kb_document.sentences[sent_no], [], "FACTFINDER")
                    # kb_communication_event_mention.add_argument("Speaker", speaker_kb_mention)
                    # # kb_communication_event_mention.has_topic = kb_quote_event_mention
                    # kb_communication_event.add_event_mention(kb_communication_event_mention)
                    # kb.add_event(kb_communication_event)
                    # group_id = KBEventGroup.generate_id(None)
                    # ev_group = KBEventGroup(group_id)
                    # ev_group.members.append(kb_communication_event)
                    # kb.add_event_group(ev_group)
                # @hqiu. This is turned off due to Quotation is not on the ontology hense no groundable.
            cross_doc_event_key_to_event_group = dict()

            event_mention_id_to_kb_event_mention = dict()

            if mode.lower() == "covid" and (serif_doc.event_set is None or len(serif_doc.event_set) == 0):
                # Create event for each event_mention to make later code work
                event_set = serif_doc.add_new_event_set()
                for sentence in serif_doc.sentences:
                    for event_mention in sentence.event_mention_set:
                        event_set.add_new_event([event_mention], event_mention.event_type)

            for serif_event in serif_doc.event_set:
                for serif_em in serif_event.event_mentions:

                    s = serif_doc.sentences[serif_em.anchor_node.sent_no] if serif_em.anchor_node is not None else \
                        serif_doc.sentences[serif_em.sentence.sent_no]
                    st = s.sentence_theories[0]
                    serif_em_semantic_phrase_text, serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end = SerifXMLReader.get_event_mention_semantic_phrase_info(
                        serif_em, st.token_sequence)
                    serif_em_semantic_phrase_original_text, serif_em_start_token_idx, serif_em_end_token_idx = SerifXMLReader.get_event_mention_semantic_phrase_origin_str(
                        serif_em, st.token_sequence)

                    event_mention_id_de_duplicate = EventMentionID(docid, serif_em_semantic_phrase_char_start,
                                                                   serif_em_semantic_phrase_char_end)
                    if event_mention_id_de_duplicate in event_mention_id_to_kb_event_mention.keys():
                        kb_event_mention = event_mention_id_to_kb_event_mention.get(event_mention_id_de_duplicate)
                        self.add_event_mention_arguments(kb_event_mention, serif_em, mention_map, kb_document, docid,
                                                         serif_valid_to_kb_valmention, serif_doc)
                        kb_event_mention.add_or_change_grounding(serif_em.event_type, serif_em.score)
                        # kb_event.add_event_mention(kb_event_mention)

                    else:
                        # em2nptext = self.find_NP_for_event_mention_triggers(serif_em, s)
                        snippet = self.get_snippet(serif_doc, st)
                        event_mention_id = SharedIDManager.get_in_document_id("EventMention", docid)
                        # print "serif_em.event_type: " + serif_em.event_type

                        list_event_types_and_confidence = SerifXMLReader.get_event_mention_types_and_confidences(
                            serif_em)
                        list_causal_factors = SerifXMLReader.get_causal_factors(serif_em, docid)

                        anchor_node_info = None
                        if serif_em.anchor_node is not None:
                            head = serif_em.anchor_node
                            if serif_em.anchor_node.head is not None:
                                head = serif_em.anchor_node.head
                            anchor_node_info = (head.text, head.start_char, head.end_char)

                        kb_event_mention = KBEventMention(event_mention_id,
                                                          kb_document,
                                                          serif_em_semantic_phrase_text,
                                                          serif_em_semantic_phrase_char_start,
                                                          serif_em_semantic_phrase_char_end,
                                                          snippet,
                                                          list_event_types_and_confidence,
                                                          list_causal_factors,
                                                          kb_document.sentences[st.parse.sent_no],
                                                          [], anchor_node_info, "KBP", serif_em.score,
                                                          serif_em_semantic_phrase_original_text,
                                                          serif_em_start_token_idx, serif_em_end_token_idx)

                        # kb_event_mention.add_or_change_grounding(serif_em.event_type, serif_em.score)
                        # print "serif_em.score: " + str(serif_em.score)

                        ## fill in the extended phrase
                        # if em2nptext is not None:
                        #    kb_event_mention.triggering_phrase = em2nptext
                        # print ("expand event trogger:\t" + kb_event_mention.trigger + "\t->\t" + kb_event_mention.triggering_phrase)

                        kb_event_mention.properties["tense"] = serif_em.tense.value
                        kb_event_mention.properties["genericity"] = serif_em.genericity.value
                        kb_event_mention.properties["modality"] = serif_em.modality.value
                        kb_event_mention.properties["polarity"] = serif_em.polarity.value
                        kb_event_mention.properties["direction_of_change"] = "Unknown"
                        if serif_em.direction_of_change == serifxml3.DirectionOfChange.Increase:
                            kb_event_mention.properties["direction_of_change"] = "Increase"
                        if serif_em.direction_of_change == serifxml3.DirectionOfChange.Decrease:
                            kb_event_mention.properties["direction_of_change"] = "Decrease"

                        if serif_em.pattern_id is not None:
                            kb_event_mention.properties["pattern_id"] = serif_em.pattern_id
                        self.add_event_mention_arguments(kb_event_mention, serif_em, mention_map, kb_document, docid,
                                                         serif_valid_to_kb_valmention, serif_doc)
                        self.set_month_property(kb_event_mention, kb_document, mention_map, serif_em, serif_doc)

                        # kb_event.add_event_mention(kb_event_mention)

                        event_id = SharedIDManager.get_in_document_id(  # Generates a new one for a new Event
                            "Event",
                            docid
                        )
                        kb_event = KBEvent(event_mention_id, serif_event.event_type)
                        kb_event.add_event_mention(kb_event_mention)
                        event_mention_id_to_kb_event_mention[event_mention_id_de_duplicate] = kb_event_mention
                        # It is assumed that the appropriate values of these have been determined before the reader
                        # is ran.

                        # This reader also assigns has_topic attributes for Quotation/Communication event mentions
                        # That may need to be changed for events. JSF
                        kb_event.properties["tense"] = serif_event.tense.value
                        kb_event.properties["genericity"] = serif_event.genericity.value
                        kb_event.properties["modality"] = serif_event.modality.value
                        kb_event.properties["polarity"] = serif_event.polarity.value

                        # It seems like it would be more convenient to directly attach the kb objects
                        # since the memory impact is similar. I couldn't immediately see a way to
                        # recover kb_value_mention information except by passing the object reference
                        # for argument in serif_event.arguments:
                        #     entity_id_or_value_id = None
                        #     if argument.entity is not None and argument.entity.id in serif_entid_to_kb_entid:
                        #         entity_id_or_value_id = serif_entid_to_kb_entid[argument.entity.id]
                        #     elif argument.value is not None and argument.value.id in serif_valid_to_kb_valmentionid:
                        #         entity_id_or_value_id = serif_valid_to_kb_valmentionid[argument.id]
                        #     kb_event.add_argument(argument.role, entity_id_or_value_id)
                        for argument in serif_event.arguments:
                            kb_entity_or_kb_valuemention = None
                            if argument.entity is not None and argument.entity.id in serif_entid_to_kb_ent:
                                kb_entity_or_kb_valuemention = serif_entid_to_kb_ent[argument.entity.id]
                            elif argument.value is not None and argument.value.id in serif_valid_to_kb_valmention:
                                kb_entity_or_kb_valuemention = serif_valid_to_kb_valmention[argument.value.id]
                            kb_event.add_argument(argument.role, kb_entity_or_kb_valuemention)

                        kb.add_event(kb_event)  # Currently adds to KBEventGroup
                        # Here we have all the info the cross-document co-reference system needs
                        event_key = '{}_{}_{}'.format(
                            serif_doc.docid,
                            serif_event.event_type,
                            serif_event.id
                        )
                        cross_doc_event_key = self.event_key_to_cross_doc_key.get(event_key, None)

                        if cross_doc_event_key in cross_doc_event_key_to_event_group:
                            # We've seen this cross-document entity before
                            kb_event_group = cross_doc_event_key_to_event_group[cross_doc_event_key]
                            kb_event_group.members.append(kb_event)
                        elif cross_doc_event_key is not None:
                            # New cross-document event
                            group_id = KBEventGroup.generate_id(None)
                            ev_group = KBEventGroup(group_id)
                            ev_group.members.append(kb_event)
                            kb.add_event_group(ev_group)
                            cross_doc_event_key_to_event_group[cross_doc_event_key] = ev_group
                    event_map[serif_em] = (kb_event, kb_event_mention, st)

            before_after_eerm_set_from_temporal_dependency = set()
            # self.add_modal_temporal_parse_info(kb, event_map, mention_map, serif_doc,
            #                                    before_after_eerm_set_from_temporal_dependency)
            new_eerm_list = list()
            added_eerms = set()

            for serif_eerm in serif_doc.event_event_relation_mention_set or []:
                serif_em_arg1 = None
                serif_em_arg2 = None
                for arg in serif_eerm.event_mention_relation_arguments:
                    if arg.role == "arg1":
                        serif_em_arg1 = arg.event_mention
                    if arg.role == "arg2":
                        serif_em_arg2 = arg.event_mention
                for arg in serif_eerm.icews_event_mention_relation_arguments:
                    if arg.role == "arg1":
                        serif_em_arg1 = arg.icews_event_mention
                    if arg.role == "arg2":
                        serif_em_arg2 = arg.icews_event_mention
                if not serif_em_arg1 or not serif_em_arg2:
                    print("Could not find two arguments for causal relation!")
                    sys.exit(1)
                if (serif_em_arg1, serif_eerm.relation_type, serif_em_arg2) not in added_eerms:
                    original_num_eerms_in_serif += 1
                    new_eerm_list.append(serif_eerm)
                    added_eerms.add((serif_em_arg1, serif_eerm.relation_type, serif_em_arg2))
            for left_em, relation_type, right_em in before_after_eerm_set_from_temporal_dependency:
                if (left_em, relation_type, right_em) not in added_eerms:
                    num_eerms_from_mtdp += 1
                    if serif_doc.event_event_relation_mention_set is None:
                        serif_doc.add_new_event_event_relation_mention_set()
                    serif_eerm = serif_doc.event_event_relation_mention_set.add_new_event_event_relation_mention(
                        relation_type, 0.9, "TemporalDependency")
                    serif_eerm.add_new_event_mention_argument("arg1", left_em)
                    serif_eerm.add_new_event_mention_argument("arg2", right_em)
                    new_eerm_list.append(serif_eerm)

            # Causal relations
            for serif_eerm in new_eerm_list:
                serif_em_arg1 = None
                serif_em_arg2 = None
                for arg in serif_eerm.event_mention_relation_arguments:
                    if arg.role == "arg1":
                        serif_em_arg1 = arg.event_mention
                    if arg.role == "arg2":
                        serif_em_arg2 = arg.event_mention
                for arg in serif_eerm.icews_event_mention_relation_arguments:
                    if arg.role == "arg1":
                        serif_em_arg1 = arg.icews_event_mention
                    if arg.role == "arg2":
                        serif_em_arg2 = arg.icews_event_mention
                if not serif_em_arg1 or not serif_em_arg2:
                    print("Could not find two arguments for causal relation!")
                    sys.exit(1)
                kb_event_arg1, kb_event_mention_arg1, sentence_theory1 = event_map[serif_em_arg1]
                kb_event_arg2, kb_event_mention_arg2, sentence_theory2 = event_map[serif_em_arg2]
                snippet = self.get_snippet(serif_doc,
                                           sentence_theory1)  # currently just dealing with single sentence causal relations

                relation_id = SharedIDManager.get_in_document_id("Relation", docid)
                relation_mention_id = SharedIDManager.get_in_document_id("RelationMention", docid)
                kb_relation = KBRelation(relation_id, "event-event", serif_eerm.relation_type, kb_event_arg1.id,
                                         kb_event_arg2.id)
                kb_relation_mention = KBRelationMention(relation_mention_id, kb_event_mention_arg1,
                                                        kb_event_mention_arg2, snippet, kb_document)

                # Optional fields
                if serif_eerm.model is not None:
                    kb_relation_mention.properties["model"] = serif_eerm.model
                if serif_eerm.pattern is not None:
                    kb_relation_mention.properties["pattern"] = serif_eerm.pattern
                if serif_eerm.confidence is not None:
                    kb_relation_mention.confidence = serif_eerm.confidence

                kb_relation_mention.properties['polarity'] = serifxml3.Polarity.Positive.value
                if serif_eerm.polarity:
                    kb_relation_mention.properties['polarity'] = serif_eerm.polarity.value
                if serif_eerm.trigger_text:
                    kb_relation_mention.properties['trigger_text'] = serif_eerm.trigger_text

                kb_relation.add_relation_mention(kb_relation_mention)
                kb.add_relation(kb_relation)
        # print("num eerms in serif: {}".format(original_num_eerms_in_serif))
        # print("num eerms by mtdp: {}".format(num_eerms_from_mtdp))


    # This is to create dummy objects that can
    # take the place of Serif ActorEntity and ActorMention
    # objects to short-circuit the actor matches in one place
    class SerifActorEntity:
        def __init__(self, name, actor_uid):
            self.actor_name = name
            self.actor_mentions = []
            self.actor_uid = actor_uid

    # AWAKE entity-level cross-document coreference
    def get_entity_to_actor_entity_cache(self, serif_doc):
        entity_to_actor_entity = dict()
        for ae in serif_doc.actor_entity_set or ():
            if ae.confidence < 0.55 or ae.actor_uid is None:
                continue
            ae_to_use = ae
            if ae.actor_name == "Mahdia":
                ae_to_use = self.SerifActorEntity("Africa", 0)
            if ae.actor_name == "Kremlin, Virginia":  # Bad link for Kremlin
                continue
            entity_to_actor_entity[ae.entity] = ae_to_use
        return entity_to_actor_entity

    # PYSERIF, for covid, entity might have more than one actor entity
    def get_entity_to_actor_entities_cache(self, serif_doc, source_note="geonames"):
        entity_to_actor_entities = defaultdict(list)
        for ae in serif_doc.actor_entity_set or ():
            if ae.source_note == source_note:
                entity_to_actor_entities[ae.entity].append(ae)
        return entity_to_actor_entities

    def get_snippet(self, serif_doc, sentence_theory):
        sentence_start = sentence_theory.token_sequence[0].start_char
        sentence_end = sentence_theory.token_sequence[-1].end_char

        return serif_doc.get_original_text_substring(sentence_start, sentence_end), sentence_start, sentence_end

    def get_normalized_time(self, serif_doc, value_mention):
        for value in serif_doc.value_set:
            if value.value_mention == value_mention:
                return value.timex_val
        return None

    def get_any_name_mention(self, kb_entity):
        for kb_mention in kb_entity.mentions:
            if kb_mention.mention_type == "name":
                return kb_mention
        return None

    def add_modal_temporal_parse_info(self, kb, event_map, mention_map, serif_doc, before_after_eerm_set):

        if hasattr(serif_doc,
                   "modal_temporal_relation_mention_set") and serif_doc.modal_temporal_relation_mention_set is not None:
            if serif_doc.modal_temporal_relation_mention_set.modal_root:
                modal_root = serif_doc.modal_temporal_relation_mention_set.modal_root
                assert modal_root.node.value == "ROOT_NODE"

                self.modal_dfs(modal_root, event_map=event_map, mention_map=mention_map, kb=kb, conceivers=[], depth=0)

            if serif_doc.modal_temporal_relation_mention_set.temporal_root:
                temporal_root = serif_doc.modal_temporal_relation_mention_set.temporal_root
                if serif_doc.document_time_start is not None and serif_doc.document_time_end is not None:
                    dct = serif_doc.document_time_start.split("T")[0]
                    dct = SerifXMLReader.month_re.match(dct)
                    assert dct is not None
                    dct = dct.group(0)
                elif self.docid_to_document_properties[serif_doc.docid]["date_created"] != "UNKNOWN":
                    dct = SerifXMLReader.month_re.match(
                        self.docid_to_document_properties[serif_doc.docid]["date_created"])
                    assert dct is not None
                    dct = dct.group(0)
                else:
                    return
                assert temporal_root.node.value == "ROOT_NODE"
                root_to_current = list()
                all_event_mention_path = list()
                self.temporal_dfs(temporal_root, dct, event_map=event_map, root_to_current=root_to_current,
                                  all_event_mention_path=all_event_mention_path, timexps=[], depth=0)
                before_set = set()
                after_set = set()
                for link in all_event_mention_path:
                    current_state = "NEUTRAL"
                    for idx in range(len(link)):
                        node = link[idx]
                        edge_type = node.relation_type
                        if edge_type in {"before", "after", "overlap"}:
                            current_state = edge_type
                        if node.event_mention is not None:
                            if current_state in {"before"}:
                                before_set.add(node.event_mention)
                            elif current_state in {"overlap", "after"}:
                                after_set.add(node.event_mention)
                for before_event in before_set:
                    for after_event in after_set:
                        before_after_eerm_set.add((before_event, 'Before-After', after_event))

    def modal_dfs(self, mtrm, event_map, mention_map, kb, *, conceivers=(), depth=0):
        '''
        :param mtrm: ModalTemporalRelationMention
        :param mention_map: maps serif mention to KBMention
        :param event_map: maps serif event mention (or icews event mention) to (KBEvent, KBEventMention, SentenceTheory)
        :param conceivers: list of conceivers governing current node

        This will do a dfs starting from the root of the modal parse, and at each call it will try to assign the kb element
        corresponding to the current event node with attributes coming from conceivers that are its predecessors in the parse
        '''

        node = mtrm.node  # contains serifxml object
        node_type = node.modal_temporal_node_type  # 'ROOT_NODE', 'AUTHOR_NODE', Conceiver, Event
        rel = node.relation_type  # 'Depends-on', 'pos', 'pp', 'neg', ...

        print("^^^^^^^")
        print("\t" * depth + f"node_type: {node_type}")
        print("\t" * depth + f"node.event_mention: {[node.event_mention]}")
        print("\t" * depth + f"node.value: {[node.value]}")
        if hasattr(node.value, 'event_type'):
            print("\t" * depth + f"node.value.event_type: {[node.value.event_type]}")
        print("\t" * depth + f"rel: {rel}")

        # add Conceiver info to current Event
        if (
                node_type == "Event" or node_type == "Event_SIP") and node.event_mention is not None and node.value.event_type != "MTDP_EVENT":
            kb_event, kb_event_mention, sentence_theory = event_map[node.value]
            kb_event_mention.conceivers = conceivers
            print("\t" * depth + f"conceivers: {str([c.canonical_name if (type(c) != str and c.canonical_name is not None) else c for (c, _) in conceivers])}")

        if len(mtrm.children) > 0:  # non-terminal node

            for child_mtrm in mtrm.children:
                # we're looking at the triples (node, child_rel, child_node)

                child_node = child_mtrm.node  # contains serifxml object
                child_node_type = child_node.modal_temporal_node_type  # 'ROOT_NODE', 'AUTHOR_NODE', Conceiver, Event
                child_rel = child_node.relation_type  # 'Depends-on', 'pos', 'pp', 'neg', ...

                child_conceivers = list(conceivers)
                if node_type == "Conceiver":  # keep only positive conceivers?
                    kb_conceiver = self.lookup_conceiver_as_kb_entity(node.value, mention_map, kb)
                    if kb_conceiver is not None:
                        child_conceivers.append((kb_conceiver, child_rel))

                self.modal_dfs(child_mtrm, event_map=event_map, mention_map=mention_map, kb=kb,
                               conceivers=child_conceivers, depth=depth + 1)


    def temporal_dfs(self, mtrm, dct, event_map, root_to_current, all_event_mention_path, *, timexps=(), depth=0):
        '''
        :param mtrm: ModalTemporalRelationMention
        :param event_map: maps serif event mention (or icews event mention) to (KBEvent, KBEventMention, SentenceTheory)
        :param timexps: list of time expressions governing current node
    
        This will do a dfs starting from the root of the temporal parse, and at each call it will try to assign the kb element
        corresponding to the current event node with attributes coming from Timex's corresponding to its predecessors in the parse
        '''

        node = mtrm.node  # contains serifxml object
        root_to_current.append(node)
        node_type = node.modal_temporal_node_type  # 'ROOT_NODE', Timex, Event
        rel = node.relation_type  # 'Depends-on', 'before', 'overlap' ...

        # add Timex info to current Event
        if node_type == "Event" and node.event_mention is not None and node.value.event_type != "MTDP_EVENT":
            all_event_mention_path.append(list(root_to_current))
            kb_event, kb_event_mention, sentence_theory = event_map[node.value]
            kb_event_mention.timexps = timexps

        if len(mtrm.children) > 0:  # non-terminal node

            for child_mtrm in mtrm.children:
                # we're looking at the triples (node, child_rel, child_node)

                child_node = child_mtrm.node  # contains serifxml object
                child_node_type = child_node.modal_temporal_node_type  # 'ROOT_NODE', Timex, Event
                child_rel = child_node.relation_type  # 'Depends-on', 'before', 'overlap' ...

                # print("-------")
                # print("\t" * depth + f"node_type: {node_type}")
                # print("\t" * depth + f"node.value: {[node.value]}")
                # print("\t" * depth + f"rel: {rel}")
                # print("\t" * depth + f"timexps: {str(timexps)}")
                # if len(timexps) > 1:
                #     print("MORE THAN ONE TIMEXP")
                # if len(set([t for t, _ in timexps])) > 1:
                #     print("DIFFERENT TIMEXPS")

                # Handle Event time
                child_timexps = list(timexps)
                if node_type == "Timex" and type(node.value) == ValueMention and node.value.get_normalized_time():
                    timexp = self.get_best_month_from_value_mention(node.value)  # month-granular timexp
                    if not timexp:
                        timexp = self.get_best_month_from_value_mention(node.value,
                                                                        best_year_only=True)  # year-granular timexp
                        if timexp == dct.split("-")[0]:  # if year is the same as DCT, this is redundant
                            timexp = None
                    if timexp:
                        child_timexps.append((timexp, child_rel))
                elif node.value == "DCT_NODE":
                    child_timexps.append((dct, child_rel))

                self.temporal_dfs(child_mtrm, dct=dct, event_map=event_map, root_to_current=root_to_current,
                                  all_event_mention_path=all_event_mention_path, timexps=child_timexps, depth=depth + 1)
        root_to_current.pop()


    def lookup_conceiver_as_kb_entity(self, conceiver, mention_map, kb):
        '''ensures that conceiver exists as entity in kb, returns None if conceiver not mapped'''
        if conceiver == "AUTHOR_NODE":
            print(">>> returning AUTHOR_NODE")
            return conceiver
        elif conceiver in mention_map:
            kb_mention = mention_map[conceiver]
            kb_entid = kb.kb_mention_to_entid[kb_mention]
            kb_entity = kb.entid_to_kb_entity[kb_entid]
            print(">>> returning {}".format(kb_entity))
            return kb_entity
        else:
            print(">>> returning None")
            return None
