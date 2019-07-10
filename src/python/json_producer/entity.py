from causeex_object import CauseExObject

class Entity(CauseExObject):

    def __init__(self, eid, entity_type, entity_subtype):
        self.eid = eid
        self.entity_type = entity_type
        self.entity_subtype = entity_subtype
        self.mentions = []

    def add_mention(self, mention):
        self.mentions.append(mention)

    def split_into_doc_types(self, docid_to_doc_type_map):
        doc_type_to_entity = dict()

        for mention in self.mentions:
            doc_type = docid_to_doc_type_map[mention.docid]
            if doc_type not in doc_type_to_entity:
                doc_type_to_entity[doc_type] = Entity(self.eid, self.entity_type, self.entity_subtype)
            doc_type_to_entity[doc_type].add_mention(mention)

        return doc_type_to_entity
