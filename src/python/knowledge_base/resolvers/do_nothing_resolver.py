from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

class DoNothingResolver(KBResolver):

    def __init__(self):
        pass

    def resolve(self, kb, parameter):
        print "Resolving KB with parameter: " + parameter

        resolved_kb = KnowledgeBase()

        super(DoNothingResolver, self).copy_all(resolved_kb, kb)

        # Just some silly code to test behavior
        #
        # for kb_event in resolved_kb.evid_to_kb_event.values():
        #     if kb_event.id.startswith("ACCENT"):
        #         kb_event.id = kb_event.id + "-CHANGED"
        #         kb_event_mention = kb_event.event_mentions[0]
        #         sources = kb_event_mention.arguments.get("Source")
        #         if sources is not None:
        #             source = sources[0]
        #             print "source is from entity: " + resolved_kb.kb_mention_to_entid[source]

        # for kb_event in resolved_kb.evid_to_kb_event.values():
        #     if kb_event.id.startswith("ACCENT"):
        #         kb_event_mention = kb_event.event_mentions[0]
        #         print(kb_event_mention.event_type)

        return resolved_kb
