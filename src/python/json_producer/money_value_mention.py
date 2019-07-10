from value_mention import ValueMention

class MoneyValueMention(ValueMention):
    def __init__(self, value_type, value_text, docid, start_char, end_char, currency_type, currency_amount, currency_minimum, currency_maximum, sent_no):
        super(MoneyValueMention, self).__init__(value_type, value_text, docid, start_char, end_char, sent_no)

        self.currency_type = currency_type
        self.currency_amount = currency_amount
        self.currency_minimum = currency_minimum
        self.currency_maximum = currency_maximum
        

