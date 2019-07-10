from knowledge_base import KnowledgeBase

class KBResolver(object):
    def __init__(self):
        pass

    def copy_all(self, resolved_kb, kb):
        resolved_kb.entid_to_kb_entity = kb.entid_to_kb_entity
        resolved_kb.evid_to_kb_event = kb.evid_to_kb_event
        resolved_kb.relid_to_kb_relation = kb.relid_to_kb_relation
        resolved_kb.docid_to_kb_document = kb.docid_to_kb_document
        
        resolved_kb.entgroupid_to_kb_entity_group = kb.entgroupid_to_kb_entity_group
        resolved_kb.relgroupid_to_kb_relation_group = kb.relgroupid_to_kb_relation_group
        resolved_kb.evgroupid_to_kb_event_group = kb.evgroupid_to_kb_event_group
        
        resolved_kb.kb_mention_to_entid = kb.kb_mention_to_entid

        resolved_kb.structured_kb = kb.structured_kb
        resolved_kb.structured_documents = kb.structured_documents
        resolved_kb.structured_relationships = kb.structured_relationships


