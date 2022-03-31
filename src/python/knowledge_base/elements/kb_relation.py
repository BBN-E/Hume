from elements.kb_element import KBElement

# argument_pair_type is either entity-entity or event-event
class KBRelation(KBElement):
    
    def __init__(self, id, argument_pair_type, relation_type, left_argument_id, right_argument_id):
        super(KBRelation,self).__init__()
        self.id = id
        self.argument_pair_type = argument_pair_type
        self.relation_type = relation_type
        self.left_argument_id = left_argument_id
        self.right_argument_id = right_argument_id
        self.relation_mentions = []
        self.confidence = 0

    def add_relation_mention(self, kb_relation_mention):
        self.confidence = (self.confidence * len(self.relation_mentions) + kb_relation_mention.confidence)/(len(self.relation_mentions) +1)
        self.relation_mentions.append(kb_relation_mention)

    @property
    def polarity(self):
        p = list()
        for i in self.relation_mentions:
            p.append(i.properties['polarity'])
        return max(p,key=p.count)

    @property
    def trigger_text(self):
        max_s = ""
        for i in self.relation_mentions:
            if i.properties.get("trigger_text") and len(i.properties.get("trigger_text")) > len(max_s):
                max_s = i.properties.get("trigger_text")
        return max_s

    @property
    def document(self):
        return self.relation_mentions[0].document