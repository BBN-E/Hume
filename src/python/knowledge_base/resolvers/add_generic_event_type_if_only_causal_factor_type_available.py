from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver


class AddGenericEventTypeIfOnlyCausalFactorTypeAvailableResolver(KBResolver):

    def __init__(self):
        super(AddGenericEventTypeIfOnlyCausalFactorTypeAvailableResolver,self).__init__()

    def resolve(self, kb):
        print("AddGenericEventTypeIfOnlyCausalFactorTypeAvailableResolver RESOLVE")
        generic_event_uri = "http://ontology.causeex.com/ontology/odps/Event#Event"
        resolved_kb = KnowledgeBase()
        super(AddGenericEventTypeIfOnlyCausalFactorTypeAvailableResolver, self).copy_all(resolved_kb, kb)

        for kb_event_id, kb_event in resolved_kb.evid_to_kb_event.items():
            for kb_event_mention in kb_event.event_mentions:
                if len(kb_event_mention.external_ontology_sources) < 1 and len(kb_event_mention.causal_factors) > 0:
                    highest_cf_score = max(cf.relevance for cf in kb_event_mention.causal_factors)
                    kb_event_mention.external_ontology_sources.append([generic_event_uri,highest_cf_score])
        return resolved_kb