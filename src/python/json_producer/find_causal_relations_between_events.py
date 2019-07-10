import json
import argparse
import codecs
import glob
import re
from json_encoder import ComplexEncoder

def read_relations_from_json(filename, docid):
    relations = []
    
    with codecs.open(filename, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    for relation in json_data['relations']:
        left_mention = relation['left_mention']
        left_mention['docid'] = docid

        right_mention = relation['right_mention']
        right_mention['docid'] = docid

        if 'event_type' in left_mention or 'event_type' in right_mention:
            relations.append(relation)

    return relations

#python python/causality/causal_json.py --dir_json /home/bmin/Downloads/json_with_causal/ --out_json /home/bmin/Downloads/event_event_relations.json
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir_json')
    parser.add_argument('--out_json')
    args = parser.parse_args()

    relations = []
    doc_idx=0
    for filename in glob.glob(args.dir_json+'/*.json'):
        doc_idx+=1
        docid = re.search(r'(.*)/(.*?)\.json', filename).group(2)
        print ("#" + str(doc_idx) + "\t" + docid + "\t" + filename)
        relations.extend(read_relations_from_json(filename, docid))


    with codecs.open(args.out_json, 'w', encoding='utf-8') as o:
        o.write(json.dumps(relations, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
        o.close()