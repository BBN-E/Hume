from kb_element import KBElement

class KBValueMention(KBElement):
    
    def __init__(self, id, value_type, value_mention_text, kb_document, head_start_char, head_end_char, kb_sentence):
        self.id = id
        self.value_type = value_type
        self.value_mention_text = value_mention_text
        self.document = kb_document
        self.head_start_char = head_start_char
        self.head_end_char = head_end_char
        self.sentence = kb_sentence

class KBTimeValueMention(KBValueMention):
    def __init__(self, id, value_type, value_mention_text, kb_document, head_start_char, head_end_char, normalized_date, kb_sentence):
        super(KBTimeValueMention, self).__init__(id, value_type, value_mention_text, kb_document, head_start_char, head_end_char, kb_sentence)
        self.normalized_date = normalized_date
        
class KBMoneyValueMention(KBValueMention):
    def __init__(self, id, value_type, value_mention_text, kb_document, head_start_char, head_end_char, currency_type, currency_amount, currency_minimum, currency_maximum, kb_sentence):
        super(KBMoneyValueMention, self).__init__(id, value_type, value_mention_text, kb_document, head_start_char, head_end_char, kb_sentence)
        
        self.currency_type = currency_type
        self.currency_amount = currency_amount
        self.currency_minimum = currency_minimum
        self.currency_maximum = currency_maximum
