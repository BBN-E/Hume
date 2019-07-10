from value_mention import ValueMention

class TimexValueMention(ValueMention):
    def __init__(self, value_type, value_text, docid, start_char, end_char, normalized_date, sent_no):
        super(TimexValueMention, self).__init__(value_type, value_text, docid, start_char, end_char, sent_no)
        self.normalized_date = normalized_date
        
