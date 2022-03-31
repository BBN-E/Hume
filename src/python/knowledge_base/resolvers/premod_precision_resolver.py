import codecs
import os
import re
import nltk
from collections import defaultdict

from elements.kb_group import KBEventGroup
from internal_ontology import OntologyMapper
from resolvers.kb_resolver import KBResolver
from knowledge_base import KnowledgeBase

# TODO this should be done on the serifxml level, before kb_constructor, to allow finding actual premod rather than string search
class PremodPrecisionResolver(KBResolver):
    def __init__(self):

        self.bad_modifier_trigger_for_type_triples = set()  # (modifier, trigger, event_type)

        script_dir = os.path.dirname(os.path.realpath(__file__))
        bad_modifier_trigger_for_type_triples_file = os.path.join(script_dir, "..", "data_files",
                                                                  "bad_modifier_trigger_for_type_triples.txt")

        self.load_data_file(bad_modifier_trigger_for_type_triples_file, self.bad_modifier_trigger_for_type_triples)
        self.bad_modifier_trigger_for_type_triples = {tuple(t.split("\t")) for t in self.bad_modifier_trigger_for_type_triples}
        self.type_to_bad_modifier_trigger = defaultdict(list)
        for (a,b,t) in self.bad_modifier_trigger_for_type_triples:
            self.type_to_bad_modifier_trigger[t].append(" ".join([a.lower(), b.lower()]))

    def load_data_file(self, file_to_load_from, s, lower_first=True):
        stream = codecs.open(file_to_load_from, 'r', encoding='utf8')
        for line in stream:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            line = re.sub('[ ]+', ' ', line)  # collapse contiguous space chars to one space char
            if lower_first:
                line = line.lower()
            else:
                head, tail = line.split(' ', 1)
                line = " ".join([head, tail.lower()])
            s.add(str(line))
        stream.close()

    # def find_modifier_in_sentence_given_trigger(self, sentence_text, trigger):
    #
    #     sentence_tokens = nltk.word_tokenize(sentence_text)
    #     try:
    #         trigger_token_index = sentence_tokens.index(trigger)
    #     except ValueError:
    #         trigger_token_index = -1
    #     modifier = None
    #     if trigger_token_index > 0:
    #         modifier = sentence_tokens[trigger_token_index - 1]
    #     return modifier

    def resolve(self, kb):
        print("PremodPrecisionResolver RESOLVE")

        resolved_kb = KnowledgeBase()
        super(PremodPrecisionResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_events_relations_and_groups()

        bad_event_ids = set()

        # Bad events by modifier, trigger and type
        for evid, event in kb.get_events():
            bad_event_mention = False
            event_type = 'UNDET'
            if len(event.event_mentions[0].external_ontology_sources) > 0:
                event_type = event.event_mentions[0].external_ontology_sources[0][0].lower()
            event_mention = event.event_mentions[0]  # TODO this is the current assumption that there is one event mention per event
            if event_type.lower() in self.type_to_bad_modifier_trigger:
                for mod_trig in self.type_to_bad_modifier_trigger[event_type.lower()]:
                    if mod_trig in event_mention.sentence.text.lower():
                        bad_event_mention = True
                        break

            if bad_event_mention:
                bad_event_ids.add(evid)

        # Add in non-bad events to resolved KB
        for evid, event in kb.get_events():
            if evid not in bad_event_ids:
                resolved_kb.add_event(event)
            # else:
            #    print "Removing: " + evid

        # Add in relations that didn't have an event removed
        for relid, relation in kb.get_relations():
            if (relation.left_argument_id not in bad_event_ids and
                    relation.right_argument_id not in bad_event_ids):
                resolved_kb.add_relation(relation)
            # else:
            #    print "Removing: " + relid

        # add event group to event mapping:
        for evgid, event_group in kb.get_event_groups():
            ev_group = KBEventGroup(event_group.id)
            for event in event_group.members:
                if event.id not in bad_event_ids:
                    ev_group.members.append(event)
            if len(ev_group.members) > 0:
                resolved_kb.add_event_group(ev_group)

        return resolved_kb
