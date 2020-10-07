from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver
from elements.kb_causal_factor import KBCausalFactor
from shared_id_manager.shared_id_manager import SharedIDManager


class InterventionWhitelistResolver(KBResolver):

    def __init__(self):
        super(InterventionWhitelistResolver,self).__init__()



    def resolve(self, kb, whitelist_path):
        print("InterventionWhitelistResolver Resolving KB with whitelist: " + whitelist_path)
        whitelisted = set()
        intervention_prefix = "/wm/concept/causal_factor/interventions"
        with open(whitelist_path,'r') as fp:
            for i in fp:
                i = i.strip()
                whitelisted.add(i)

        resolved_kb = KnowledgeBase()
        super(InterventionWhitelistResolver, self).copy_all(resolved_kb, kb)

        for evid, event in kb.get_events():
            for event_mention in event.event_mentions:

                resolved_external_ontology_sources = list()

                for causal_factor in event_mention.causal_factors:
                    assert isinstance(causal_factor,KBCausalFactor)
                    if causal_factor.factor_class.startswith(intervention_prefix) is False:
                        resolved_external_ontology_sources.append(causal_factor)
                    else:
                        if causal_factor.factor_class in whitelisted:
                            resolved_external_ontology_sources.append(causal_factor)
                if len(resolved_external_ontology_sources) < 1:
                    cf_id = SharedIDManager.get_in_document_id("CausalFactor", event_mention.document.id)
                    resolved_external_ontology_sources.append(KBCausalFactor(cf_id, "/wm/concept/causal_factor", "NEUTRAL", 0.3, 0.25))
                event_mention.causal_factors = resolved_external_ontology_sources

        return resolved_kb
