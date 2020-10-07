from elements.kb_element import KBElement

class KBSentence(KBElement):
    
    def __init__(self, id, start_offset, end_offset, text, original_text):
        self.id = id
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.text = text
        self.original_text = original_text

