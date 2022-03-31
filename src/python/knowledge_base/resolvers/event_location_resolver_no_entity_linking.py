import sys, os, codecs, re, json
from collections import defaultdict
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver
from elements.kb_value_mention import KBTimeValueMention

class EventLocationResolverNoEntityLinking(KBResolver):
    location_roles = {"has_location", "has_origin_location", "has_destination_location", "Place", "Origin", "Destination"}

    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))

    def is_location_role(self, role):
        # Could change depending on how we generate arguments
        return role in self.location_roles

    def get_kb_sentence_to_kb_mentions(self, kb):
        kb_sentence_to_kb_mentions = defaultdict(list)
        for entid, entity in kb.get_entities():
            for entity_mention in entity.mentions:
                kb_sentence_to_kb_mentions[entity_mention.sentence].append(entity_mention)
        return kb_sentence_to_kb_mentions

    def resolve(self, kb):
        print("{} RESOLVE".format(type(self).__name__))

        resolved_kb = KnowledgeBase()
        super(EventLocationResolverNoEntityLinking, self).copy_all(resolved_kb, kb)
        kb_sentence_to_kb_mentions = self.get_kb_sentence_to_kb_mentions(resolved_kb)

        for evid, event in resolved_kb.get_events():
            for event_mention in event.event_mentions:
                event_mention_has_location_argument = False
                for role, arguments in event_mention.arguments.items(): # event_mention.arguments is a dictionary mapping role to a list of arguments. An argument consists of a KBMention or KBValueMention and a confidence.
                    if self.is_location_role(role):  # if the event has an explicit location role
                        for kb_mention, confidence in arguments:
                            if kb_mention.entity_type == "GPE" or kb_mention.entity_type == "LOC" or kb_mention.entity_type == "FAC":
                                location_argument_entid = kb.kb_mention_to_entid.get(kb_mention)
                                if location_argument_entid is not None:
                                    location_argument_entity = kb.entid_to_kb_entity[location_argument_entid]
                                    canonical_name = location_argument_entity.canonical_name
                                    if len(canonical_name) > 0:
                                        event_mention_has_location_argument = True
                                        if "state" not in event_mention.properties:
                                            event_mention.properties["state"] = [(canonical_name, kb_mention.head_start_char, kb_mention.head_end_char)]
                                        else:
                                            event_mention.properties["state"].append((canonical_name, kb_mention.head_start_char, kb_mention.head_end_char))
                                        event_mention.properties["best_location_method"] = "argument"
                                        print("Setting state to:", canonical_name, "({})".format(kb_mention.mention_text), "[{}]".format(event_mention.id), "[argument]")
                if not event_mention_has_location_argument:  # otherwise, look through possible locations in the sentence
                    kb_mentions_in_sentence = kb_sentence_to_kb_mentions[event_mention.sentence]
                    for kb_mention in kb_mentions_in_sentence:
                            if kb_mention.entity_type == "GPE" or kb_mention.entity_type == "LOC" or kb_mention.entity_type == "FAC":
                                location_argument_entid = kb.kb_mention_to_entid.get(kb_mention)
                                if location_argument_entid is not None:
                                    location_argument_entity = kb.entid_to_kb_entity[location_argument_entid]
                                    canonical_name = location_argument_entity.canonical_name
                                    if len(canonical_name) > 0:
                                        if "state" not in event_mention.properties:
                                            event_mention.properties["state"] = [(canonical_name, kb_mention.head_start_char, kb_mention.head_end_char)]
                                        else:
                                            event_mention.properties["state"].append((canonical_name, kb_mention.head_start_char, kb_mention.head_end_char))
                                        event_mention.properties["best_location_method"] = "sentence"
                                        print("Setting state to:", canonical_name, "({})".format(kb_mention.mention_text), "[{}]".format(event_mention.id), "[sentence]")

        return resolved_kb

