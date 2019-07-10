import sys
import json

json_file = sys.argv[1]

domain_ontology_file = sys.argv[2]

out_json_file = sys.argv[3]

params = json.load(open(json_file, 'r'))

for extractor_params in params['extractors']:
    extractor_params['domain_ontology'] = domain_ontology_file
    
json.dump(params, open(out_json_file,'w'), indent=4, sort_keys=True)

    
