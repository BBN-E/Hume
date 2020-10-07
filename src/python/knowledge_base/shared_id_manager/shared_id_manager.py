import sys
import io
import os
import json

class SharedIDManager:
   
    # Maps object type to ID counter
    in_document_object_types = { 
        "Mention": 0,
        "Entity": 0,
        "Relation": 0, 
        "Event": 0, 
        "Sentence": 0,
        "MentionSpan": 0, 
        "Span": 0,
        "Worksheet": 0,
        "TimeSeries": 0, 
        "Property": 0,
        "Factor": 0,
        "ReportedValue": 0,
        "TableRef": 0,
        "RelationMention": 0,
        "EventMention": 0,
        "ValueMention": 0,
        "CausalFactor": 0,
        }

    # Load country name to CAMEO code mappings
    with io.open(os.path.dirname(os.path.realpath(__file__)) +
                 "/../data_files/country_name_to_cameo-code_mapping.json",
                 "r", encoding="utf8") as f:
        country_name_to_cameo_code_mappings = json.load(f)
        country_name_to_cameo_code_mappings = {
            k.lower(): v for k, v in
            country_name_to_cameo_code_mappings.items()}

    def __init__(self):
        pass

    @classmethod
    def is_in_document_type(cls, object_type):
        return object_type in cls.in_document_object_types

    @classmethod
    def get_in_document_id(cls, object_type, docid):
        if not cls.is_in_document_type(object_type):
            print("IDManager could not find in-document object type: ",)
            print(object_type)
            sys.exit(1)
            
        current_id = (object_type + "-" + docid + "-" +
                      str(cls.in_document_object_types[object_type]))
        cls.in_document_object_types[object_type] += 1
        
        return current_id

    @classmethod
    def convert_to_cameo_optionally(cls, name):
        if name.lower() in cls.country_name_to_cameo_code_mappings:
            cameo_code = cls.country_name_to_cameo_code_mappings[name.lower()]
            name = "CAMEO" + cameo_code.lower()
        return name
