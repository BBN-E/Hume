import sys, os, re, codecs, json

from accent_event import AccentEvent
from mention import Mention
from entity import Entity
from relation_mention import RelationMention
from value_mention import ValueMention
from money_value_mention import MoneyValueMention
from timex_value_mention import TimexValueMention
from event import Event
from date import Date
from event_argument import EventArgument
from actor_match import ActorMatch
from agent_match import AgentMatch
from generic_event import GenericEvent
from fake_serif_objects import SerifActorEntity, SerifActorMention 
import monetary_normalizer
import uuid
import collections

sys.path.append(os.path.join(os.environ['SVN_PROJECT_ROOT'], 'SERIF', 'python'))
import serifxml
script_dir = os.path.dirname(os.path.realpath(__file__))

class CauseExResults:

    def __init__(self):
        self.event_code_to_name = dict() # CAMEO event code -> description of event
        
        # Read event types file
        event_types_file = os.path.join(script_dir, '..', '..', '..', 'lib', 'events', 'event_types.txt')
        if not os.path.exists(event_types_file):
            print "Could not find: " + event_types_file
            sys.exit(1)
        event_code_re = re.compile(r'code "(\d+)"')
        event_name_re =  re.compile(r'name "(.*?)"')
        events_file_stream = codecs.open(event_types_file, encoding='utf8')
        event_code = None
    
        for line in events_file_stream:
            code_m = event_code_re.search(line)
            if code_m:
                event_code = code_m.group(1)
                continue
            name_m = event_name_re.search(line)
            if name_m:
                event_name = name_m.group(1)
                self.event_code_to_name[event_code] = event_name
                event_code = None
        events_file_stream.close()

        ### for cross-doc entities
        self.eid=0
        self.eid_to_entity = {}
        self.doc_to_entity_to_eid = {}
        # self.mention_to_eid = {}
        self.timex2_to_date = {}
        self.country_actor_id_to_eid = {}

    def clean_actor_name_for_entity_id(self, n):
        return n.replace(" ", "_").replace("#", "_").replace('"', '_')

    #################################### cross-doc coreference
    def global_get_entity_id(self, docid, serif_doc, eid_in_doc, entity, mention_to_actor_entity):
        # look up in cache
        if docid in self.doc_to_entity_to_eid:
            if eid_in_doc in self.doc_to_entity_to_eid[docid]:
                return self.doc_to_entity_to_eid[docid][eid_in_doc]

        for m in entity.mentions:
            if m in mention_to_actor_entity:
                actor_entity = mention_to_actor_entity[m]
                #if len(actor_entity.actor_name.strip()) == 0:
                #    print "Actor entity has empty actor name string for: " + str(actor_entity.actor_uid)
                #    print "mention text is: " + m.text
                return entity.entity_type + "-" + self.clean_actor_name_for_entity_id(actor_entity.actor_name) + "-" + str(actor_entity.actor_uid)

        # if no good actor mention
        self.eid+=1
        entity_id = entity.entity_type + "-" + str(self.eid)
        #print ("creating entiy_id: " + entity_id)

        if docid not in self.doc_to_entity_to_eid:
            self.doc_to_entity_to_eid[docid] = {}
        self.doc_to_entity_to_eid[docid][eid_in_doc] = entity_id

        return entity_id

    def preprocess_doc(self, docid, serif_doc):
        mention_to_eid = dict()
        mention_to_actor_entity = self.get_mention_to_actor_entity_cache(serif_doc)

        eid_in_doc=0
        for e in serif_doc.entity_set:
            eid_in_doc += 1
            global_eid = self.global_get_entity_id(docid, serif_doc, eid_in_doc, e, mention_to_actor_entity)

            for m in e.mentions:
                mention_to_eid[m] = global_eid

        return mention_to_eid

    #################################### cross-doc coreference

    # AWAKE entity-level cross-document coreference
    def get_mention_to_actor_entity_cache(self, serif_doc):
        mention_to_actor_entity = dict()
        for ae in serif_doc.actor_entity_set:
            if ae.confidence < 0.55 or ae.actor_uid is None:
                continue
            ae_to_use = ae
            if ae.actor_name == "Mahdia":
                ae_to_use = SerifActorEntity("Africa", 0)
            for m in ae.entity.mentions:
                mention_to_actor_entity[m] = ae_to_use
        return mention_to_actor_entity
    
    # ICEWS mention-level cross-document coreference and 
    # agent matching
    def get_mention_to_actor_mention_cache(self, serif_doc):
        mention_to_actor_mention = dict()
        for am in serif_doc.actor_mention_set:
            am_to_use = am
            if am.actor_name == "Mahdia":
                am_to_use = SerifActorMention("Africa")
            if am.paired_actor_name == "Mahdia":
                continue
            mention_to_actor_mention[am.mention] = am_to_use
        return mention_to_actor_mention

    # Creates list of CauseEx Entity objects from serifxml Document object
    def produce_entities(self, docid, serif_doc):
        mention_to_actor_mention = self.get_mention_to_actor_mention_cache(serif_doc)
        mention_to_actor_entity = self.get_mention_to_actor_entity_cache(serif_doc)

        eid_in_doc=0
        for e in serif_doc.entity_set:
            
            eid_in_doc += 1
            global_eid = self.global_get_entity_id(docid, serif_doc, eid_in_doc, e, mention_to_actor_entity)
            #print ("= Look up global entiy ID: " + global_eid.encode('ascii','ignore'))

            entity = Entity(global_eid, e.entity_type, e.entity_subtype)
            if global_eid in self.eid_to_entity:
                entity = self.eid_to_entity[global_eid]

            # entity = Entity(global_eid, e.entity_type, e.entity_subtype)
            for m in e.mentions:

                # Store country eid info, we'll need this later to create 
                # some document-level relatoins
                if (m == e.mentions[0] and
                    m.entity_type == "GPE" and
                    m in mention_to_actor_entity and
                    len(mention_to_actor_entity[m].actor_mentions) > 0):
                    
                    ae = mention_to_actor_entity[m]
                    am = ae.actor_mentions[0]
                    if am.country_info_actor_id is not None and am.country_info_actor_id == am.actor_uid:
                        # This is a country, keep track of its global_eid by actor id
                        self.country_actor_id_to_eid[am.actor_uid] = global_eid

                entity.add_mention(self.create_causeex_mention(serif_doc, m, mention_to_actor_mention, mention_to_actor_entity))

            if global_eid not in self.eid_to_entity:
                self.eid_to_entity[global_eid] = entity
            # results.append(entity)

        # return results

    # Creates list of CauseEx RelationMention objects from serifxml Document object
    def produce_relations(self, serif_doc, mention_to_eid):
        results = []
        
        mention_to_actor_mention = self.get_mention_to_actor_mention_cache(serif_doc)
        mention_to_actor_entity = self.get_mention_to_actor_entity_cache(serif_doc)

        for s in serif_doc.sentences:
            st = s.sentence_theories[0]
            for rm in st.rel_mention_set:
                snippet = self.get_snippet(serif_doc, st)
                left_mention = self.create_causeex_mention(serif_doc, rm.left_mention, mention_to_actor_mention, mention_to_actor_entity)
                right_mention = self.create_causeex_mention(serif_doc, rm.right_mention, mention_to_actor_mention, mention_to_actor_entity)
                left_eid = "UNKNOWN"
                right_eid = "UNKNOWN"
                if rm.left_mention in mention_to_eid:
                    left_eid = mention_to_eid[rm.left_mention]
                if rm.right_mention in mention_to_eid:
                    right_eid =mention_to_eid[rm.right_mention]
                relation_mention = RelationMention(rm.type, rm.tense.value, rm.modality.value, left_mention, right_mention, left_eid, right_eid, snippet)
                if rm.time_arg:
                    value_mention = TimexValueMention(
                        rm.time_arg.value_type, rm.time_arg.text, 
                        serif_doc.docid, rm.time_arg.start_char, 
                        rm.time_arg.end_char, self.get_normalized_time(serif_doc, rm.time_arg),
                        rm.time_arg.sent_no)

                    relation_mention.add_time_arg(value_mention, rm.time_arg_role)
                results.append(relation_mention)

        # Corpus-level PART-WHOLE relations -- look for city mentions and
        # create a PART-WHOLE relation for the city and its country
        for e in serif_doc.entity_set:
            for m in e.mentions:
                if (m.entity_type == "GPE" and
                    m in mention_to_actor_entity and
                    len(mention_to_actor_entity[m].actor_mentions) > 0):
                    
                    ae = mention_to_actor_entity[m]
                    am = ae.actor_mentions[0]
                    if (am.country_info_actor_id is not None and 
                        am.country_info_actor_id != am.actor_uid and
                        am.country_info_actor_id in self.country_actor_id_to_eid):

                        # This is a location which is in a country that we have a eid
                        # for. Create a PART-WHOLE relation for it.
                        country_eid = self.country_actor_id_to_eid[am.country_info_actor_id]
                        left_mention = self.create_causeex_mention(serif_doc, m, mention_to_actor_mention, mention_to_actor_entity)
                        left_eid = "UNKNOWN"
                        if m in mention_to_eid:
                            left_eid = mention_to_eid[m]
                        st = serif_doc.sentences[m.syn_node.sent_no]
                        snippet = self.get_snippet(serif_doc, st)
                        relation_mention = RelationMention("PART-WHOLE.Geographical", 
                                                           "Unspecified", "Asserted", 
                                                           left_mention, None, left_eid,
                                                           country_eid, snippet)
                        results.append(relation_mention)

        return results

    # Take in mention object from serifxml and create a CauseEx Mention object
    def create_causeex_mention(self, serif_doc, m, mention_to_actor_mention, mention_to_actor_entity):
        mention = self.produce_mention(serif_doc, m)
        
        if m in mention_to_actor_entity:
            # AWAKE-level match
            actor_match = self.produce_actor_match(mention_to_actor_entity[m])
            mention.add_actor_match(actor_match)
        elif m in mention_to_actor_mention and not mention_to_actor_mention[m].actor_uid:
            # ICEWS agent match
            agent_match = self.produce_agent_match(mention_to_actor_mention[m])
            mention.add_agent_match(agent_match)
        
        return mention

    def produce_generic_events(self, serif_doc, event_info_file):
        results = []

        event_info = []
        with codecs.open(event_info_file, 'r', encoding='utf-8') as f:
            for line in f:
                tokens = line.strip().split()
                classname = 'Class-' + tokens[1]
                anchor_text = tokens[2]
                start_char = int(tokens[3])
                end_char = int(tokens[4])
                event_info.append((classname, anchor_text, start_char, end_char))

        sent_no = -1
        for s in serif_doc.sentences:
            sent_no += 1
            st = s.sentence_theories[0]
            if len(st.token_sequence) > 0:
                st_start = st.token_sequence[0].start_char
                st_end = st.token_sequence[-1].end_char
                for (classname, anchor_text, start_char, end_char) in event_info:
                    if st_start <= start_char and end_char <= st_end:
                        snippet = self.get_snippet(serif_doc, st)
                        event = GenericEvent(serif_doc.docid, snippet, classname, anchor_text, start_char, end_char, sent_no)
                        results.append(event)
        return results


    # Creates list of CauseEx Event objects from serifxml Document object
    def produce_events(self, serif_doc, mention_to_eid):
        results = []

        mention_to_actor_mention = self.get_mention_to_actor_mention_cache(serif_doc)
        mention_to_actor_entity = self.get_mention_to_actor_entity_cache(serif_doc)

        sent_no = -1
        for s in serif_doc.sentences:
            sent_no += 1
            st = s.sentence_theories[0]
            for em in st.event_mention_set:
                snippet = self.get_snippet(serif_doc, st)
                event = Event(snippet, em.event_type, em.genericity.value, em.polarity.value, em.tense.value, em.modality.value, em.anchor_node.text, serif_doc.docid, em.anchor_node.start_char, em.anchor_node.end_char, sent_no)
                for a in em.arguments:
                    argument_mention = None
                    argument_value_mention = None

                    global_eid_or_timex = "UNKNOWN"
                    if a.mention:
                        argument_mention = self.create_causeex_mention(serif_doc, a.mention, mention_to_actor_mention, mention_to_actor_entity)
                        if a.mention in mention_to_eid:
                            global_eid_or_timex = mention_to_eid[a.mention]
                    elif a.value_mention:
                        currency_type = None
                        currency_amount = None
                        currency_range = None
                        
                        if a.value_mention.value_type == "Numeric.Money":
                            currency_type, currency_amount, currency_minimum, currency_maximum = monetary_normalizer.normalize(a.value_mention.text)

                            #o = codecs.open("/nfs/raid66/u14/users/azamania/temp/money-values", "a+", encoding='utf-8')
                            #o.write(a.value_mention.text + " | " + str(currency_type) + " | " + str(currency_amount) + " | " + str(currency_minimum) + " | " + str(currency_maximum) + "\n")
                            #o.close()
                            
                            argument_value_mention = MoneyValueMention(
                                a.value_mention.value_type, a.value_mention.text, 
                                serif_doc.docid, a.value_mention.start_char, 
                                a.value_mention.end_char, 
                                currency_type, currency_amount, currency_minimum, currency_maximum,
                                a.value_mention.sent_no)

                        elif a.value_mention.value_type == "TIMEX2.TIME":
                            argument_value_mention = TimexValueMention(
                                a.value_mention.value_type, a.value_mention.text, 
                                serif_doc.docid, a.value_mention.start_char, 
                                a.value_mention.end_char,
                                self.get_normalized_time(serif_doc, a.value_mention),
                                a.value_mention.sent_no)

                        else:
                            argument_value_mention = ValueMention(
                                a.value_mention.value_type, a.value_mention.text, 
                                serif_doc.docid, a.value_mention.start_char, 
                                a.value_mention.end_char, a.value_mention.sent_no)
                        
                    event_arg = EventArgument(a.role, argument_mention, argument_value_mention, global_eid_or_timex)
                    event.add_argument(event_arg)

                results.append(event)

        return results

    # Creates list of CauseEx AccentEvent objects from serifxml Document object
    def produce_accent_events(self, serif_doc, mention_to_eid):
        results = []

        mention_to_actor_mention = self.get_mention_to_actor_mention_cache(serif_doc)
        mention_to_actor_entity = self.get_mention_to_actor_entity_cache(serif_doc)
        
        for iem in serif_doc.icews_event_mention_set:
            source_actor_mention = None
            target_actor_mention = None
            
            for participant in iem.participants:
                if participant.role == "SOURCE":
                    source_actor_mention = participant.actor
                elif participant.role == "TARGET":
                    target_actor_mention = participant.actor

            participants = dict() # role -> Mention
            sentence_theory = None

            source_eid = "UNKNOWN"
            target_eid = "UNKNOWN"
            sent_no = None
            if source_actor_mention:
                mention = source_actor_mention.mention
                if mention in mention_to_eid:
                    source_eid = mention_to_eid[mention]
                participants["Source"] = self.create_causeex_mention(serif_doc, mention, mention_to_actor_mention, mention_to_actor_entity)
                sentence_theory = source_actor_mention.sentence_theory
                sent_no = sentence_theory.parse.sent_no
            if target_actor_mention:
                mention = target_actor_mention.mention
                if mention in mention_to_eid:
                    target_eid = mention_to_eid[mention]
                participants["Target"] = self.create_causeex_mention(serif_doc, mention, mention_to_actor_mention, mention_to_actor_entity)
                sentence_theory = target_actor_mention.sentence_theory
                sent_no = sentence_theory.parse.sent_no

            snippet = self.get_snippet(serif_doc, sentence_theory)
            event_tense = iem.event_tense
            event_code = iem.event_code
            event_name = self.event_code_to_name[event_code]
            time_value_mention = iem.time_value_mention
            causeex_time_value_mention = None
            if time_value_mention:
                causeex_time_value_mention = TimexValueMention(
                    time_value_mention.value_type, time_value_mention.text, 
                    serif_doc.docid, time_value_mention.start_char, 
                    time_value_mention.end_char,
                    self.get_normalized_time(serif_doc, time_value_mention),
                    time_value_mention.sent_no)
                if not sent_no:
                    sent_no = time_value_mention.sent_no
            
            results.append(AccentEvent(snippet, event_code, event_tense, event_name, participants, source_eid, target_eid, causeex_time_value_mention,serif_doc.docid, sent_no))

        return results

    # Returns Mention object
    def produce_mention(self, serif_doc, serif_mention):
        mention = Mention(serif_mention.entity_type, serif_mention.mention_type.value, serif_mention.text, serif_mention.head.text, serif_doc.docid, serif_mention.syn_node.start_char, serif_mention.syn_node.end_char, serif_mention.head.start_char, serif_mention.head.end_char, serif_mention.sent_no)
        return mention

    def get_lat_long_from_actor_entity(self, actor_entity):
        for am in actor_entity.actor_mentions:
            if am.geo_latitude and am.geo_longitude:
                return am.geo_latitude, am.geo_longitude
        return None, None

    # Returns ActorMatch object
    def produce_actor_match(self, actor_entity):
        latitude = None
        longitude = None
        
        latitude, longitude = self.get_lat_long_from_actor_entity(actor_entity)        
        actor_match = ActorMatch(actor_entity.actor_name, latitude, longitude)
        
        return actor_match

    # Returns AgentMatch object
    def produce_agent_match(self, actor_mention):
        paired_agent_name = "Unknown"
        paired_actor_name = "Unknown"

        if actor_mention.paired_agent_name:
            paired_agent_name = actor_mention.paired_agent_name

        if actor_mention.paired_actor_name:
            paired_actor_name = actor_mention.paired_actor_name

        agent_match = AgentMatch(paired_agent_name, paired_actor_name)
        return agent_match

    def get_snippet(self, serif_doc, sentence_theory):
        sentence_start = sentence_theory.token_sequence[0].start_char
        sentence_end = sentence_theory.token_sequence[-1].end_char

        return serif_doc.get_original_text_substring(sentence_start, sentence_end), sentence_start, sentence_end
    
    def get_normalized_time(self, serif_doc, value_mention):
        for value in serif_doc.value_set:
            if value.value_mention == value_mention:
                return value.timex_val
        return None
    
