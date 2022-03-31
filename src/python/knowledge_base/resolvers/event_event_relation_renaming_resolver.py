import logging
from enum import Enum
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver

logger = logging.getLogger(__name__)

relation_type_mapping = {
    "Preventative-Effect": "mitigate",
    "MitigatingFactor-Effect": "mitigate",
    "Cause-Effect": "cause",
    "Catalyst-Effect": "cause",
    "Precondition-Effect": "cause",
    "Before-After": "before"
}


class EventEventRelationRenamingResolver(KBResolver):
    def __init__(self):
        super(EventEventRelationRenamingResolver, self).__init__()

    def resolve(self, kb):
        resolved_kb = KnowledgeBase()
        super(EventEventRelationRenamingResolver, self).copy_all(resolved_kb, kb)

        added_relation_triples = set()
        resolved_relid_to_kb_relation = dict()
        for kb_relation in resolved_kb.relid_to_kb_relation.values():
            if kb_relation.argument_pair_type == "event-event":
                current_relation_type = kb_relation.relation_type
                resolved_relation_type = relation_type_mapping[current_relation_type]
                kb_relation.relation_type = resolved_relation_type
                if (kb_relation.left_argument_id,resolved_relation_type,kb_relation.right_argument_id) not in added_relation_triples:
                    resolved_relid_to_kb_relation[kb_relation.id] = kb_relation
                    added_relation_triples.add((kb_relation.left_argument_id,resolved_relation_type,kb_relation.right_argument_id))
            else:
                resolved_relid_to_kb_relation[kb_relation.id] = kb_relation

        resolved_kb.relid_to_kb_relation = resolved_relid_to_kb_relation

        return resolved_kb
