import json

class StructuredDataReader:
    def __init__(self):
        pass

    def read(self, kb, structured_kb_file):
        print("StructuredDataReader READ")
        with open(structured_kb_file) as f:
            structured_kb = json.load(f)
            kb.structured_kb = structured_kb
