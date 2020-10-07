import sys
from elements.kb_group import KBEventGroup, KBRelationGroup

class KnowledgeBase:
    def __init__(self):
        # Entity, Relation, Event, Document storage
        self.entid_to_kb_entity = dict()
        self.relid_to_kb_relation = dict()
        self.evid_to_kb_event = dict()
        self.docid_to_kb_document = dict()

        # Cross-document corefernece storage
        self.entgroupid_to_kb_entity_group = dict()
        self.relgroupid_to_kb_relation_group = dict()
        self.evgroupid_to_kb_event_group = dict()
        
        self.kb_mention_to_entid = dict()

        self.structured_kb = dict()
        # TODO replace the below with dict structure and incorporate contents to appropriate locations in this class
        self.structured_documents = []
        self.structured_relationships = []

    def add_entity(self, kb_entity):
        if kb_entity.id in self.entid_to_kb_entity:
            print(kb_entity.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.entid_to_kb_entity[kb_entity.id] = kb_entity

    def add_mention_to_entity(self, kb_entity, kb_mention):
        kb_entity.mentions.append(kb_mention)
        self.kb_mention_to_entid[kb_mention] = kb_entity.id

    def add_relation(self, kb_relation):
        if kb_relation.id in self.relid_to_kb_relation:
            print(kb_relation.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.relid_to_kb_relation[kb_relation.id] = kb_relation
        # No cross-document corefernce yet for relations, so just
        # make a new relation group and add it
        group_id = KBRelationGroup.generate_id(None)
        rel_group = KBRelationGroup(group_id)
        rel_group.members.append(kb_relation)
        self.add_relation_group(rel_group)

    def add_event(self, kb_event):
        if kb_event.id in self.evid_to_kb_event:
            print(kb_event.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.evid_to_kb_event[kb_event.id] = kb_event
        # No cross-document corefernce yet for events, so just
        # make a new relation group and add it
        group_id = KBEventGroup.generate_id(None)
        ev_group = KBEventGroup(group_id)
        ev_group.members.append(kb_event)
        self.add_event_group(ev_group)

    def add_document(self, kb_document):
        if kb_document.id in self.docid_to_kb_document:
            print(kb_document.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.docid_to_kb_document[kb_document.id] = kb_document

    def add_entity_group(self, kb_entity_group):
        if kb_entity_group.id in self.entgroupid_to_kb_entity_group:
            print(kb_entity_group.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.entgroupid_to_kb_entity_group[kb_entity_group.id] = kb_entity_group

    def add_relation_group(self, kb_relation_group):
        if kb_relation_group.id in self.relgroupid_to_kb_relation_group:
            print(kb_relation_group.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.relgroupid_to_kb_relation_group[kb_relation_group.id] = kb_relation_group

    def add_event_group(self, kb_event_group):
        if kb_event_group.id in self.evgroupid_to_kb_event_group:
            print(kb_event_group.id + " already in KnowledgeBase!")
            sys.exit(1)
        self.evgroupid_to_kb_event_group[kb_event_group.id] = kb_event_group

    def get_entities(self):
        return self.entid_to_kb_entity.items()
    
    def get_relations(self):
        return self.relid_to_kb_relation.items()

    def get_events(self):
        return self.evid_to_kb_event.items()

    def get_entity_groups(self):
        return self.entgroupid_to_kb_entity_group.items()

    def get_relation_groups(self):
        return self.relgroupid_to_kb_relation_group.items()

    def get_event_groups(self):
        return self.evgroupid_to_kb_event_group.items()

    def clear_relations_and_relation_groups(self):
        self.relid_to_kb_relation = dict()
        self.relgroupid_to_kb_relation_group = dict()

    # Can't naively clear entities and events because
    # other objects can point to entity mentions and
    # event mentions

    def clear_events_relations_and_groups(self):
        self.relid_to_kb_relation = dict()
        self.relgroupid_to_kb_relation_group = dict()
        self.evid_to_kb_event = dict()
        self.evgroupid_to_kb_event_group = dict()
