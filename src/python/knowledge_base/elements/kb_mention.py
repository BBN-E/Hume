from elements.kb_element import KBElement

class KBMention(KBElement):
    
    def __init__(self, mentid, entity_type, mention_type, mention_text, mention_head_text, kb_document, start_char, end_char, head_start_char, head_end_char, kb_sentence, link_confidence,mention_original_text,mention_original_head_text):
        self.id = mentid
        self.entity_type = entity_type
        self.mention_type = mention_type
        self.mention_text = mention_text
        self.mention_head_text = mention_head_text
        self.document = kb_document
        self.start_char = start_char
        self.end_char = end_char
        self.head_start_char = head_start_char
        self.head_end_char = head_end_char
        self.sentence = kb_sentence
        self.link_confidence = link_confidence
        self.mention_original_text = mention_original_text
        self.mention_original_head_text = mention_original_head_text

        self.properties = dict()

    @property
    def is_referred_in_kb(self):
        return self.properties.get("is_referred_in_kb",True)

    @is_referred_in_kb.setter
    def is_referred_in_kb(self, is_referred_in_kb):
        self.properties["is_referred_in_kb"] = is_referred_in_kb
