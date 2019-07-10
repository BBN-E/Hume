from kb_element import KBElement

class KBDocument(KBElement):
    def __init__(self, id, properties):
        self.id = id
        self.properties = properties
        self.sentences = []

    def add_sentence(self, kb_sentence):
        self.sentences.append(kb_sentence)



