from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver

# Overrides the genericity of "factor" events to "Generic", as required by program guidelines
class FactorEventGenericGenericityResolver(KBResolver):

    def __init__(self):
        pass

    def resolve(self, kb):
        print "FactorEventGenericGenericityResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        # initially, just make a copy of the input kb
        super(FactorEventGenericGenericityResolver, self).copy_all(resolved_kb, kb)

        new_evid_to_kb_event = kb.evid_to_kb_event
        for kb_event_id, kb_event in resolved_kb.evid_to_kb_event.iteritems():
            new_kb_event = kb_event
            new_event_mentions = list()
            is_factor_event = "Event" in kb_event.event_type_to_confidence
            # only expecting one event mention, but using a loop for semantic correctness
            for kb_event_mention in kb_event.event_mentions:
                new_kb_event_mention = kb_event_mention
                if is_factor_event:
                    new_kb_event_mention.properties["genericity"] = "Generic"
                new_event_mentions.append(new_kb_event_mention)
            new_kb_event.event_mentions = new_event_mentions
            new_evid_to_kb_event[kb_event_id] = new_kb_event
        resolved_kb.evid_to_kb_event = new_evid_to_kb_event

        return resolved_kb
