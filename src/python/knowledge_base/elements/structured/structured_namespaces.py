import json
import os
from rdflib import Namespace

ns_lookup = dict()

filepath = os.path.dirname(os.path.realpath(__file__)) + "/../../config_files/config_ontology.json"
with open(filepath) as fp:
    config = json.load(fp)
    for namespace, URI in config.get('namespace', {}).items():
        ns_lookup[namespace] = Namespace(URI)
