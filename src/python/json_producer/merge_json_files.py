import sys, os, codecs, json
from json_encoder import ComplexEncoder
from pprint import pprint

file_docs="/nfs/mercury-05/u34/CauseEx/data/month_1_deliverables/list_1500_docids"

file_map_id_to_json_kbp="/nfs/mercury-05/u34/CauseEx/data/month_1_deliverables/map_id_to_json_kbp"
file_map_id_to_json_serif_accent_awake="/nfs/mercury-05/u34/CauseEx/data/month_1_deliverables/map_id_to_json_serif_accent_awake"

output_dir="/nfs/mercury-05/u34/CauseEx/data/month_1_deliverables/json_for_1500_docs"

docs=set()
map_id_to_json_kbp=dict()
map_id_to_json_serif_accent_awake=dict()


def load_json(f):
    with open(f) as data_file:
        return json.load(data_file)

with open(file_docs) as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        docs.add(line)

with open(file_map_id_to_json_kbp) as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        items = line.split('\t')
        map_id_to_json_kbp[items[0]] = items[1]

with open(file_map_id_to_json_serif_accent_awake) as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        items = line.split('\t')
        map_id_to_json_serif_accent_awake[items[0]] = items[1]


for doc in docs:
    print("docid: " + doc)

    json_kbp = load_json(map_id_to_json_kbp[doc])
    json_serif_accent_awake = load_json(map_id_to_json_serif_accent_awake[doc])

    
    result = dict()

    result["entities"] = json_serif_accent_awake["entities"]
    result["relations"] = json_serif_accent_awake["relations"]
    result["events"] = json_kbp["events"]
    result["accent_events"] = json_serif_accent_awake["accent_events"]

    outfile = os.path.join(output_dir, doc + ".json")
    o = codecs.open(outfile, 'w', encoding='utf8')

    o.write(json.dumps(result, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
    o.close()
