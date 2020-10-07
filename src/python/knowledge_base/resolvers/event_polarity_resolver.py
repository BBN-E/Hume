from resolvers.kb_resolver import KBResolver
from knowledge_base import KnowledgeBase


negative_word_set = {"lack","lacks","absence","blockades","hindered","deficits"}

negative_type_set = {"shortage","insecurity"}


class EventPolarityResolver(KBResolver):
    def __init__(self):
        pass
    def resolve(self, kb):
        print("EventPolarityResolver RESOLVE")

        resolved_kb = KnowledgeBase()
        super(EventPolarityResolver, self).copy_all(resolved_kb, kb)

        for evid, kb_event in resolved_kb.get_events():
            for kb_event_mention in kb_event.event_mentions:
                event_mention_text = kb_event_mention.trigger
                should_reverse_polarity = False
                tokens_in_mention = event_mention_text.split(" ")
                for token in tokens_in_mention:
                    if token in negative_word_set and len(tokens_in_mention) > 1:
                        should_reverse_polarity = True
                if should_reverse_polarity is True:
                    for event_type,grounding in kb_event_mention.external_ontology_sources:
                        for negative_type_keyword in negative_type_set:
                            if negative_type_keyword in event_type:
                                should_reverse_polarity = False
                if should_reverse_polarity is True:
                    kb_event_mention.properties["polarity"] = "Negative"
        return resolved_kb
