import codecs
import os
import re

from internal_ontology import OntologyMapper
from resolvers.kb_resolver import KBResolver
from knowledge_base import KnowledgeBase


class EventTypeChangeResolver(KBResolver):
    whitespace_re = re.compile(r"\s+")

    def __init__(self):
        self.type_change_cache = dict() # type and trigger => new type
        self.type_change_cache_with_orig_types = dict() # (trigger, orig_type,) => new type

        script_dir = os.path.dirname(os.path.realpath(__file__))
        type_change_file = os.path.join(script_dir, "..", "data_files", "corrective_event_mapping.txt")
        i = codecs.open(type_change_file, 'r', encoding='utf8')
        for line in i:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            pieces = line.rsplit(" ", 1)
            self.type_change_cache[pieces[0].lower()] = pieces[1]
        i.close()

        type_change_by_type_and_headword_file = os.path.join(script_dir, "..", "data_files", "corrective_event_mapping_with_orig_types.txt")
        i = codecs.open(type_change_by_type_and_headword_file, 'r', encoding='utf8')
        for line in i:
            line = line.strip()
            if line.startswith("#") or len(line) == 0:
                continue
            pieces = line.rsplit(" ", 2)
            self.type_change_cache_with_orig_types[(pieces[0].lower(), pieces[1],)] = pieces[2]
        i.close()

    def clean_string(self, s):
        if s is None:
            return None

        s = EventTypeChangeResolver.whitespace_re.sub(" ", s)

        return s.lower()

    def resolve(self, kb, event_ontology_yaml, ontology_flags):
        print("EventTypeChangeResolver RESOLVE")

        ontology_mapper = OntologyMapper()
        ontology_mapper.load_ontology(event_ontology_yaml)

        new_type_change_cache = dict()
        for trigger, changed_type in self.type_change_cache.items():
            for flag in ontology_flags.split(','):
                grounded_types = ontology_mapper.look_up_external_types(
                    changed_type, flag)
                new_type_change_cache[trigger] = grounded_types
        self.type_change_cache = new_type_change_cache

        new_type_change_cache_with_orig_types = dict()
        for key, changed_type in self.type_change_cache_with_orig_types.items():
            trigger, original_type = key
            for flag in ontology_flags.split(','):
                grounded_new_types = ontology_mapper.look_up_external_types(
                    changed_type, flag)
                grounded_old_types = ontology_mapper.look_up_external_types(
                    original_type, flag)
                for grounded_old_type in grounded_old_types:
                    new_key = (trigger, grounded_old_type)
                    new_type_change_cache_with_orig_types[new_key] = (
                        grounded_new_types)
        self.type_change_cache_with_orig_types = new_type_change_cache_with_orig_types

        resolved_kb = KnowledgeBase()
        super(EventTypeChangeResolver, self).copy_all(resolved_kb, kb)

        for evid, event in kb.get_events():
            for event_mention in event.event_mentions:

                trigger = self.clean_string(event_mention.trigger)
                triggering_phrase = self.clean_string(event_mention.triggering_phrase)

                old_groundings = event_mention.external_ontology_sources[:]
                event_mention.external_ontology_sources = []

                for event_type, score in old_groundings:
                    if (trigger, event_type) in self.type_change_cache_with_orig_types:
                        for new_type in self.type_change_cache_with_orig_types[
                                (trigger, event_type)]:
                            event_mention.add_or_change_grounding(
                                new_type, score)

                    elif (triggering_phrase, event_type) in self.type_change_cache_with_orig_types:
                        for new_type in self.type_change_cache_with_orig_types[
                               (triggering_phrase, event_type)]:
                            event_mention.add_or_change_grounding(
                                new_type, score)

                    elif trigger and trigger in self.type_change_cache:
                        for new_type in self.type_change_cache[trigger]:
                            event_mention.add_or_change_grounding(new_type, score)

                    elif triggering_phrase and triggering_phrase in self.type_change_cache:
                        for new_type in self.type_change_cache[
                                triggering_phrase]:
                            event_mention.add_or_change_grounding(
                                new_type, score)

                    else:
                        event_mention.add_or_change_grounding(event_type, score)

        return resolved_kb
