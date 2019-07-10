from kb_element import KBElement

class KBSentence(KBElement):
    
    def __init__(self, id, start_offset, end_offset, text):
        self.id = id
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.text = text

