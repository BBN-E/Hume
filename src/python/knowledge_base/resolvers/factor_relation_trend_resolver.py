import logging
from enum import Enum
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver


logger = logging.getLogger(__name__)


CA_mappings = {
    "Cause-Effect":0,
    "Catalyst-Effect":1,
    "Precondition-Effect":0,
    "Preventative-Effect":-1,
    "MitigatingFactor-Effect":-1,
}

CF_trend_mappings = {
    "Stable":0,
    "Increase":1,
    "Decrease":-1,
    "Unknown":0
}

CF_trend_mappings_reversed = {v:k for k,v in CF_trend_mappings.items()}

class FactorRelationTrendResolver(KBResolver):
    def __init__(self):
        super(FactorRelationTrendResolver, self).__init__()

    def resolve(self, kb):
        resolved_kb = KnowledgeBase()
        super(FactorRelationTrendResolver, self).copy_all(resolved_kb, kb)

        trend_to_corrected_mappings = dict()
        event_direction_of_changes_to_corrected_mappings = dict()

        # Round 1 pre calculation
        for kb_relation in resolved_kb.relid_to_kb_relation.values():
            if kb_relation.argument_pair_type == "event-event":
                relation_type = kb_relation.relation_type
                if relation_type == "Before-After":
                    continue
                left_kb_event = resolved_kb.evid_to_kb_event[kb_relation.left_argument_id]
                right_kb_event = resolved_kb.evid_to_kb_event[kb_relation.right_argument_id]
                left_factor_types = list()
                for left_kb_event_mention in left_kb_event.event_mentions:
                    left_factor_types.extend(left_kb_event_mention.causal_factors)
                right_factor_types = list()
                for right_kb_event_mention in right_kb_event.event_mentions:
                    right_factor_types.extend(right_kb_event_mention.causal_factors)
                ca_mapping_val = CA_mappings[relation_type]
                if ca_mapping_val != 0:
                    # Handling CF
                    for right_cf in right_factor_types:
                        if CF_trend_mappings[right_cf.trend] == 0:
                            corrected_right_cf_trend = CF_trend_mappings_reversed[ca_mapping_val]
                        else:
                            corrected_right_cf_trend = CF_trend_mappings_reversed[ca_mapping_val * CF_trend_mappings[right_cf.trend]]
                        trend_to_corrected_mappings.setdefault(right_cf,list()).append(corrected_right_cf_trend)
                    # Handling event.trend
                    for right_kb_event_mention in right_kb_event.event_mentions:
                        current_direction_of_change = right_kb_event_mention.properties["direction_of_change"]
                        if CF_trend_mappings[current_direction_of_change] == 0:
                            corrected_direction_of_change = CF_trend_mappings_reversed[ca_mapping_val]
                        else:
                            corrected_direction_of_change = CF_trend_mappings_reversed[ca_mapping_val * CF_trend_mappings[current_direction_of_change]]
                        event_direction_of_changes_to_corrected_mappings.setdefault(right_kb_event_mention,list()).append(corrected_direction_of_change)

        # Round 2 make the change
        for kb_relation in resolved_kb.relid_to_kb_relation.values():
            if kb_relation.argument_pair_type == "event-event":
                relation_type = kb_relation.relation_type
                if relation_type == "Before-After":
                    continue
                left_kb_event = resolved_kb.evid_to_kb_event[kb_relation.left_argument_id]
                right_kb_event = resolved_kb.evid_to_kb_event[kb_relation.right_argument_id]
                left_factor_types = list()
                for left_kb_event_mention in left_kb_event.event_mentions:
                    left_factor_types.extend(left_kb_event_mention.causal_factors)
                right_factor_types = list()
                for right_kb_event_mention in right_kb_event.event_mentions:
                    right_factor_types.extend(right_kb_event_mention.causal_factors)
                ca_mapping_val = CA_mappings[relation_type]
                if ca_mapping_val != 0:
                    for right_cf in right_factor_types:
                        if right_cf in trend_to_corrected_mappings:
                            lst = trend_to_corrected_mappings[right_cf]
                            right_cf.trend = max(lst,key=lst.count)
                    for right_kb_event_mention in right_kb_event.event_mentions:
                        if right_kb_event_mention in event_direction_of_changes_to_corrected_mappings:
                            lst = event_direction_of_changes_to_corrected_mappings[right_kb_event_mention]
                            right_kb_event_mention.properties["direction_of_change"] = max(lst,key=lst.count)
                kb_relation.relation_type = "Cause-Effect"

        return resolved_kb