import uuid

from elements.kb_element import KBElement

class KBGroup(KBElement):
    def __init__(self, id):
        self.id = id
        self.members = []

    def reprJSON(self):
        d = dict()
        d["members"] = []
        d["id"] = self.id
        
        for member in self.members:
            d["members"].append(member.id)

        return d

class KBEntityGroup(KBGroup):
    def __init__(self, id, canonical_name, actor_id):
        super(KBEntityGroup, self).__init__(id)

        self.canonical_name = canonical_name
        self.actor_id = actor_id
        self.properties = dict()

    @classmethod
    def generate_id(cls, cross_document_id):
        if cross_document_id is not None:
            return "EntityUnified-" + str(cross_document_id)
        else:
            return "EntityUnified-" + str(uuid.uuid1())

    def reprJSON(self):
        d = dict()
        d["id"] = self.id
        d["canonical_name"] = self.canonical_name
        d["actor_id"] = self.actor_id
        d["members"] = []
        d["properties"] = self.properties
        for member in self.members:
            d["members"].append(member.id)

        return d

    def get_cameo_code_or_id(self):
        for kb_entity in self.members:
            if "GPE.Nation" in kb_entity.entity_type_to_confidence and "cameo_country_code" in kb_entity.properties:
                return True,kb_entity.properties["cameo_country_code"]
        else:
            return False,self.id

    @property
    def is_referred_in_kb(self):
        return self.properties.get("is_referred_in_kb",True)

    @is_referred_in_kb.setter
    def is_referred_in_kb(self, is_referred_in_kb):
        self.properties["is_referred_in_kb"] = is_referred_in_kb

class KBEventGroup(KBGroup):
    def __init__(self, id):
        super(KBEventGroup, self).__init__(id)

    @classmethod
    def generate_id(cls, cross_document_id):
        if cross_document_id is not None:
            return "EventUnified-" + str(cross_document_id)
        else:
            return "EventUnified-" + str(uuid.uuid1())

class KBRelationGroup(KBGroup):
    def __init__(self, id, relation_type=None, left_argument_id=None, right_argument_id=None):
        super(KBRelationGroup, self).__init__(id)
        self.relation_type = relation_type
        self.left_argument_id = left_argument_id
        self.right_argument_id = right_argument_id

    @classmethod
    def generate_id(cls, cross_document_id):
        if cross_document_id is not None:
            return "RelationUnified-" + str(cross_document_id)
        else:
            return "RelationUnified-" + str(uuid.uuid1())
