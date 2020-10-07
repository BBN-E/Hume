import codecs
import os
import re

from elements.kb_group import KBEventGroup
from internal_ontology import OntologyMapper
from resolvers.kb_resolver import KBResolver
from knowledge_base import KnowledgeBase


class PrecisionResolver(KBResolver):
    def __init__(self):
        self.bad_trigger_words = set()
        self.bad_trigger_word_pairs = set()
        self.bad_relation_patterns = set()
        self.bad_type_and_trigger_pairs = set()
        self.bad_relation_triples = set()  # a relation-triple is a triple of the form (
        # trigger_1, relation_type, trigger_2) or (triggering_phrase_1, relation_type,
        # triggering_phrase_2)
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        bad_trigger_word_file = os.path.join(script_dir, "..", "data_files", "bad_trigger_words.txt")
        bad_trigger_word_pairs_file = os.path.join(script_dir, "..", "data_files", "bad_trigger_word_pairs.txt")
        bad_relation_patterns_file = os.path.join(script_dir, "..", "data_files", "bad_relation_patterns.txt")
        bad_type_and_trigger_pairs_file = os.path.join(script_dir, "..", "data_files", "bad_type_and_trigger_pairs.txt")
        bad_relation_triples_file = os.path.join(script_dir, "..", "data_files", "bad_relation_triples.txt")

        self.load_data_file(bad_trigger_word_file, self.bad_trigger_words)
        self.load_data_file(bad_trigger_word_pairs_file, self.bad_trigger_word_pairs)
        self.load_data_file(bad_relation_patterns_file, self.bad_relation_patterns)
        self.load_data_file(bad_type_and_trigger_pairs_file, self.bad_type_and_trigger_pairs, lower_first=False)
        self.load_data_file(bad_relation_triples_file, self.bad_relation_triples)

    def load_data_file(self, file_to_load_from, s, lower_first=True):
        stream = codecs.open(file_to_load_from, 'r', encoding='utf8')
        for line in stream:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            line = re.sub( '[ ]+', ' ', line) # collapse contiguous space chars to one space char
            if lower_first:
                line = line.lower()
            else:
                head, tail = line.split(' ', 1)
                line = " ".join([head, tail.lower()])
            s.add(str(line))
        stream.close()

    def resolve(self, kb, event_ontology_yaml, ontology_flags):
        print("PrecisionResolver RESOLVE")

        ontology_mapper = OntologyMapper()
        ontology_mapper.load_ontology(event_ontology_yaml)
        tmp_bad_type_and_trigger_pairs = set()
        while self.bad_type_and_trigger_pairs:
            line = self.bad_type_and_trigger_pairs.pop()
            internal_type, trigger = line.split(' ', 1)
            for flag in ontology_flags.split(','):
                grounded_types = ontology_mapper.look_up_external_types(
                    internal_type, flag)
                # print(grounded_types, internal_type)
                for grounded_type in grounded_types:
                    tmp_bad_type_and_trigger_pairs.add(
                        " ".join([grounded_type, trigger]))
        self.bad_type_and_trigger_pairs = tmp_bad_type_and_trigger_pairs

        resolved_kb = KnowledgeBase()
        super(PrecisionResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_events_relations_and_groups()

        bad_event_ids = set()
        # Bad events by trigger word
        for evid, event in kb.get_events():
            found_good_event_mention = False
            for event_mention in event.event_mentions:
                if event_mention.trigger is None or event_mention.trigger.lower() not in self.bad_trigger_words:
                    found_good_event_mention = True
                    break

            if not found_good_event_mention:
                bad_event_ids.add(evid)

        # Bad events by type and trigger word
        for evid, event in kb.get_events():
            found_good_event_mention = False
            for event_mention in event.event_mentions:

                # Events can be created that have no types/external_ontology_sources,
                # but they should have causal factors
                if len(event_mention.external_ontology_sources) == 0 and len(event_mention.causal_factors) > 0:
                    found_good_event_mention = True
                    break
                
                for event_type, score in event_mention.external_ontology_sources:
                    if (event_mention.trigger is None or
                            event_type + " " + event_mention.trigger.lower() not in self.bad_type_and_trigger_pairs):
                        found_good_event_mention = True
                        break

            if not found_good_event_mention:
                #print "Removing event of type: " + event_mention.event_type + " and trigger: "  + event_mention.trigger.lower()
                bad_event_ids.add(evid)

        bad_relation_ids = set()
        # Bad relations or bad triples
        for relid, relation in kb.get_relations():
            if relation.argument_pair_type != "event-event":
                continue

            found_good_relation_mention_triggers = False
            found_good_relation_mention_pattern = False
            found_good_relation_triple = False
            for relation_mention in relation.relation_mentions:
                left_em = relation_mention.left_mention
                right_em = relation_mention.right_mention
                left_trigger = str(left_em.trigger).lower()
                right_trigger = str(right_em.trigger).lower()
                left_phrase = str(left_em.triggering_phrase if left_em.triggering_phrase
                                  else left_em.trigger).lower().replace("\n"," ")
                right_phrase = str(right_em.triggering_phrase if right_em.triggering_phrase else
                                   right_em.trigger).lower().replace("\n"," ")
                left_trigger = re.sub( '[ ]+', ' ', left_trigger)
                right_trigger = re.sub( '[ ]+', ' ', right_trigger)
                left_phrase = re.sub( '[ ]+', ' ', left_phrase)
                right_phrase = re.sub( '[ ]+', ' ', right_phrase)

                if left_trigger + " " + right_trigger not in self.bad_trigger_word_pairs:
                    found_good_relation_mention_triggers = True

                if "pattern" not in relation_mention.properties or relation_mention.properties["pattern"] not in self.bad_relation_patterns:
                    found_good_relation_mention_pattern = True
                    # check if this triple is valid
                    relation_type = str(relation.relation_type).lower()
                    triple_variation_1 = "\t".join([left_trigger,relation_type,right_trigger])
                    triple_variation_2 = "\t".join([left_phrase,relation_type,right_phrase])
                    # if "susceptibility" in triple_variation_2 or "susceptibility" in \
                    #         triple_variation_1:
                    #     print ""
                    if triple_variation_1 not in self.bad_relation_triples and triple_variation_2\
                            not in self.bad_relation_triples:
                        found_good_relation_triple = True

            if not found_good_relation_mention_triggers or not found_good_relation_mention_pattern or not found_good_relation_triple:
                bad_relation_ids.add(relid)

        # Add in non-bad events to resolved KB
        for evid, event in kb.get_events():
            if evid not in bad_event_ids:
                resolved_kb.add_event(event)
            #else:
            #    print "Removing: " + evid

        # Add in non-bad relations that didn't have an event removed 
        for relid, relation in kb.get_relations():
            if (relid not in bad_relation_ids and
                relation.left_argument_id not in bad_event_ids and
                relation.right_argument_id not in bad_event_ids):
                
                resolved_kb.add_relation(relation)
            #else:
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

    
