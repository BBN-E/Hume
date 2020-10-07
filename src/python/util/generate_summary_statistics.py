import codecs
import json
import os
import re
import sys
from datetime import datetime

sys.path.append("/nfs/raid88/u10/users/bmin/exp_envs/wm/text-open/src/python")

import serifxml3

whitespace_re = re.compile(r"\s+")

from model_for_summary_statics import EntityT1,EventT1,database





class GenerateSummaryStatistics:
    def __init__(self,entity_output_callback,event_output_callback,serifxml_list_path):
        self.serif_name_to_actor = dict()  # Supplimental cross-document linking
        self.event_key_to_cross_doc_key = dict()  # Event cross-document linking

        ## TODO: The following needs to be populated into a relational DB, (e.g., sqlite?) that supports SQL in which we could query for one or more column, and return counts of elements on any other column
        #self.entity_freq_counter # <type, canonical_name, freq>
        #self.entity_relation_freq_counter # <type1, canonical_name1, relation_type, type2, canonical_name2>
        #self.event_freq_counter # <event_type, event_phrase, active_actor_canonical_name, affected_actor_canonical_name,  actor_name, location_name>
        self.event_output_callback = event_output_callback
        self.entity_output_callback = entity_output_callback
        self.serifxml_list_path = serifxml_list_path

    def get_canonical_name(self, serif_entity, serif_actor_entity):
        if serif_actor_entity is not None:
            return serif_actor_entity.actor_name
        # No actor match, take longest name
        longest_name = ""
        for mention in serif_entity.mentions:
            if mention.mention_type.value == "name":
                mention_head_text = mention.head.text
                mention_head_text = whitespace_re.sub(" ", mention_head_text)
                if len(mention_head_text) > len(longest_name):
                    longest_name = mention_head_text
        if longest_name == "":
            return None
        return longest_name

    def get_event_mention_argument(self, serif_event_mention,
                                   mention_to_entity, serif_entity_to_serif_actor_entity):

        role_args = []
        for argument in serif_event_mention.arguments:
            mention_or_value_mention = None
            if argument.mention is not None:
                entity_type, canonical_name = self.get_type_and_canonical_name_for_mention(mention_to_entity,                     serif_entity_to_serif_actor_entity,argument.mention)

                if entity_type is not None and canonical_name is not None:
                    role_args.append((argument.role, entity_type, canonical_name))
        return role_args

    @staticmethod
    def get_event_mention_semantic_phrase_info(serif_em, serif_sentence_tokens):
        serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[
                                                                 int(serif_em.semantic_phrase_start):int(
                                                                     serif_em.semantic_phrase_end) + 1])
        return serif_em_semantic_phrase_text, None, None

    @staticmethod
    def get_event_mention_types_and_confidences(serif_em):
        ret = list()
        for event_type in serif_em.event_types:
            ret.append([event_type.event_type, event_type.score])
        return ret


    def get_type_and_canonical_name_for_mention(self, mention_to_entity, serif_entity_to_serif_actor_entity, mention):
        if mention in mention_to_entity:
            serif_entity = mention_to_entity[mention]

            if serif_entity in serif_entity_to_serif_actor_entity:
                actor_entity = serif_entity_to_serif_actor_entity.get(serif_entity)

                canonical_name = self.get_canonical_name(serif_entity, actor_entity)

                serif_entity_type = serif_entity.entity_type

                return serif_entity_type, canonical_name

        return None, None


    def get_acceptable_anchor_expansion(self,anchor_node,token_idx_to_token,token_to_token_idx):
        ret = list()
        ret.append(anchor_node.text)
        assert isinstance(anchor_node,serifxml3.SynNode)
        parent = anchor_node.parent
        if parent is not None:
            start_token_idx = token_to_token_idx[parent.start_token]
            end_token_idx = token_to_token_idx[parent.end_token]
            if end_token_idx-start_token_idx+1 <= 3:
                ret.append(parent.text)
            parent = anchor_node.parent
            if parent is not None:
                start_token_idx = token_to_token_idx[parent.start_token]
                end_token_idx = token_to_token_idx[parent.end_token]
                if end_token_idx-start_token_idx+1 <= 5:
                    ret.append(parent.text)
        return ret


    def read(self):

        # serifxml_dir = "/nfs/raid88/u10/users/hqiu/runjob/expts/Hume/causeex_collab2_0913a_m24_shaved_dataset/event_consolidation/00826/output/"
        # serifxml_dir = "/nfs/raid88/u10/users/hqiu/regtest/results/1570669203/wm_dart.100219.v1/expts/probabilistic-grounding/00092/output/"
        # serifxml_dir = "/nfs/raid87/u11/users/azamania/runjobs/expts/Hume/causeex_collab2_0916c_m24_shaved_dataset_serialization/final_serifxml/COLLAB2_1/"


        print("Reading from: " + self.serifxml_list_path)
        serifxml_files = []

        with open(self.serifxml_list_path) as fp:
            for i in fp:
                i = i.strip()
                serifxml_files.append(i)


        files_length = len(serifxml_files)
        count = 0

        actor_id_to_entity_group = dict()

        for serifxml_file in serifxml_files:
            mention_to_entity = dict()

            count += 1
            print("SerifXMLReader producing KB objects in: " + serifxml_file + " (" + str(count) + "/" + str(files_length) + ")")

            serif_doc = serifxml3.Document(serifxml_file)

            serif_entity_to_serif_actor_entity = self.get_entity_to_actor_entity_cache(serif_doc)

            nato_country_kb_entities = []
            for serif_entity in serif_doc.entity_set:
                for serif_mention in serif_entity.mentions:
                    mention_to_entity[serif_mention] = serif_entity

                    entity_type, entity_canonical_name = self.get_type_and_canonical_name_for_mention(
                        mention_to_entity,
                        serif_entity_to_serif_actor_entity, serif_mention)

                    if entity_type is not None and entity_canonical_name is not None:
                        # For entity table, we're outputing
                        self.entity_output_callback(entity_type,entity_canonical_name)



            for serif_sentence in serif_doc.sentences:
                st = serif_sentence.sentence_theories[0]
                token_idx_to_token = dict()
                # We're not doing entity entity relation yet.
                for token_idx,token in enumerate(st.token_sequence):
                    # @hqiu We need this because original_token_index is not bind correctly!
                    assert isinstance(token,serifxml3.Token)
                    token_idx_to_token[token_idx] = token
                token_to_token_idx = {v:k for k,v in token_idx_to_token.items()}
                for serif_em in st.event_mention_set:

                    # TODO: we need to be careful about serif_em_semantic_phrase_text: it shouldn't be super long, should remove modifiers, should allow variants (shorter forms)


                    actor_names = set()
                    location_names = set()
                    for arg_role,arg_entity_type,arg_canonical_name in self.get_event_mention_argument(serif_em,
                                                                                                   mention_to_entity, serif_entity_to_serif_actor_entity):
                        if arg_role == "has_location":
                            location_names.add(arg_canonical_name)
                        if arg_role == "has_active_actor" or arg_role == "has_affected_actor" or arg_role == "has_actor":
                            actor_names.add(arg_canonical_name)
                    for event_type in serif_em.event_types:
                        event_type_str = event_type.event_type
                        for anchor in serif_em.anchors:
                            anchor_texts = self.get_acceptable_anchor_expansion(anchor.anchor_node,token_idx_to_token,token_to_token_idx)
                            for anchor_text in anchor_texts:
                                anchor_text = anchor_text.replace("\t","").replace("\n","").lower()
                                self.event_output_callback(event_type_str,anchor_text,"","")

                                for actor_name in actor_names:
                                    for location_name in location_names:
                                        self.event_output_callback(event_type_str,anchor_text,actor_name,location_name)
                                for actor_name in actor_names:
                                    self.event_output_callback(event_type_str,anchor_text,actor_name,"")
                                for location_name in location_names:
                                    self.event_output_callback(event_type_str,anchor_text,"",location_name)

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
        for ae in serif_doc.actor_entity_set:
            if ae.confidence < 0.55 or ae.actor_uid is None:
                continue
            ae_to_use = ae
            if ae.actor_name == "Mahdia":
                ae_to_use = self.SerifActorEntity("Africa", 0)
            entity_to_actor_entity[ae.entity] = ae_to_use
        return entity_to_actor_entity

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


if __name__ == "__main__":

    database.init("/nfs/raid88/u10/users/hqiu/tmp/event_statics.db", pragmas={
        'journal_mode': 'wal',  # WAL-mode.
        'cache_size': -64 * 1000,  # 64MB cache.
        'synchronous': 0})
    database.connect()

    def event_callback(event_type,event_mention_str,actor_str,location_str):
        event = EventT1(event_type=event_type,event_mention_str=event_mention_str,actor_str=actor_str,location_str=location_str)
        event.save()
        # print("Event:\t{}\t{}\t{}\t{}".format(event_type,event_mention_str,actor_str,location_str))

    def entity_callback(entity_type,canonical_name):
        entity = EntityT1(entity_type=entity_type,canonical_name=canonical_name)
        entity.save()
        # print("Entity:\t{}\t{}".format(entity_type,canonical_name))

    serifxml_list_path = "/nfs/raid88/u10/users/hqiu/runjob/expts/Hume/causeex_collab2_0913a_m24_shaved_dataset/event_consolidation_serifxml_out.list"
    generator = GenerateSummaryStatistics(entity_callback,event_callback,serifxml_list_path)
    generator.read()
    database.commit()
    database.close()