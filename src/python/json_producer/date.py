from causeex_object import CauseExObject

class Date(CauseExObject):

    def __init__(self, normalized_date):
        self.normalized_date = normalized_date
        self.mentions = []

    def add_mention(self, mention):
        self.mentions.append(mention)

    def split_into_doc_types(self, docid_to_doc_type_map):
        doc_type_to_date = dict()
        
        for mention in self.mentions:
            doc_type = docid_to_doc_type_map[mention.docid]
            if doc_type not in doc_type_to_date:
                doc_type_to_date[doc_type] = Date(self.normalized_date)
            doc_type_to_date[doc_type].add_mention(mention)

        return doc_type_to_date
