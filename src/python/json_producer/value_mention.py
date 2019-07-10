from causeex_object import CauseExObject

class ValueMention(CauseExObject):
    
    def __init__(self, value_type, value_text, docid, start_char, end_char, sent_no):
        self.value_type = value_type
        self.value_text = value_text
        self.docid = docid
        self.head_start_char = start_char # Call the head_start_char to be consistent with Mention
        self.head_end_char = end_char 
        self.sent_no = sent_no
        
