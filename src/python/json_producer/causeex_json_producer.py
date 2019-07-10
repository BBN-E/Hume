import sys, os, codecs, json
from causeex_results import CauseExResults
from json_encoder import ComplexEncoder # Helper class for converting to json

include_entities = True
include_relations = True
include_events = True
include_accent_events = True
include_generic_events = True

if len(sys.argv) != 5:
    print "Usage: " + sys.argv[0] + " input-serifxml-dir output-json-dir generic-event-filelist metadata-file"
    sys.exit(1)

result = dict() # { "doc_type1" => { "entities" => [e1, e2...], "relations" => [r1, r2] ... } 
                #   "doc_type2" => { ... } }

sys.path.append(os.path.join(os.environ['SVN_PROJECT_ROOT'], 'SERIF', 'python'))
import serifxml

input_dir, output_dir, generic_event_filelist, metadata_file = sys.argv[1:]
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

# Read metadat file to be able to map docid to doc_type ("Abstract", "News_Article", "Analytic_Report")
docid_to_doc_type_map = dict()
m = open(metadata_file, 'r')
line_count = 0
for line in m:
    line_count += 1
    pieces = line.strip().split("\t")
    docid = pieces[0]
    doc_type = pieces[4].strip()
    docid_to_doc_type_map[docid] = doc_type
    if doc_type not in result:
        result[doc_type] = dict()
result["all"] = dict()

# Each doc_type gets it's own list of entities, relations, etc.
for doc_type in result:
    if include_entities:
        result[doc_type]["entities"] = []
    if include_relations:
        result[doc_type]["relations"] = []
    if include_events:
        result[doc_type]["events"] = []
    if include_accent_events:
        result[doc_type]["accent_events"] = []
    if include_generic_events:
        result[doc_type]["generic_events"] = []


# read the filepaths of generic event info
generic_event_files = dict()
with open(generic_event_filelist, 'r') as f:
    for line in f:
        line = line.strip()
        docid = os.path.basename(line)
        generic_event_files[docid] = line

processor = CauseExResults()

# Make sure we can write to the output directory
test_outfile = os.path.join(output_dir, "test")
o = codecs.open(test_outfile, 'w', encoding='utf8')
o.close()
os.unlink(test_outfile)

doc_num=0
# pre-populate entities: cross-doc coreference
for filename in os.listdir(input_dir):
    docid = filename
    if filename.endswith(".txt.xml"):
        docid = filename[0:-(len(".txt.xml"))]
    elif filename.endswith(".serifxml"):
        docid = filename[0:-(len(".serifxml"))]
    elif filename.endswith(".sgm.xml"):
        docid = filename[0:-(len(".sgm.xml"))]
    else:
        docid = None

    if docid is None:
        continue

    doc_num+=1
    print ("[cross-doc] Doc #" + str(doc_num) + ": " + docid)

    # outfile = os.path.join(output_dir, docid + ".json")
    # o = codecs.open(outfile, 'w', encoding='utf8')

    serif_doc = serifxml.Document(os.path.join(input_dir, filename))

    processor.produce_entities(docid, serif_doc)

if include_entities:

    for eid in processor.eid_to_entity:
        entity = processor.eid_to_entity[eid]
        result["all"]["entities"].append(entity)
        # If we have 3 doc types, we'll split the entity into 3, 
        # each containing the mentions from a particular doc type
        # doc_type_to_entity is a dict that maps doc_type to a single entity
        doc_type_to_entity = entity.split_into_doc_types(docid_to_doc_type_map)
        for doc_type in doc_type_to_entity:
            entity = doc_type_to_entity[doc_type]
            result[doc_type]["entities"].append(entity)

doc_num=0
for filename in os.listdir(input_dir):
    docid = filename
    if filename.endswith(".txt.xml"):
        docid = filename[0:-(len(".txt.xml"))]
    elif filename.endswith(".serifxml"):
        docid = filename[0:-(len(".serifxml"))]
    elif filename.endswith(".sgm.xml"):
        docid = filename[0:-(len(".sgm.xml"))]
    else:
        docid = None

    if docid is None:
        print "Could not get docid from: " + filename
        sys.exit(1)

    doc_type = docid_to_doc_type_map[docid]

    doc_num += 1
    print ("[reln/event] Doc #" + str(doc_num) + ": " + docid)

    # outfile = os.path.join(output_dir, docid + ".json")
    # o = codecs.open(outfile, 'w', encoding='utf8')

    serif_doc = serifxml.Document(os.path.join(input_dir, filename))

    # prepopulate entities
    mention_to_eid = processor.preprocess_doc(docid, serif_doc)

    if include_relations:
        doc_relations_list = processor.produce_relations(serif_doc, mention_to_eid)
        result[doc_type]["relations"].extend(doc_relations_list)
        result["all"]["relations"].extend(doc_relations_list)
    if include_events:
        doc_events_list = processor.produce_events(serif_doc, mention_to_eid)
        result[doc_type]["events"].extend(doc_events_list)
        result["all"]["events"].extend(doc_events_list)
    if include_accent_events:
        doc_accent_events_list = processor.produce_accent_events(serif_doc, mention_to_eid)
        result[doc_type]["accent_events"].extend(doc_accent_events_list)
        result["all"]["accent_events"].extend(doc_accent_events_list)
    if include_generic_events:
        generic_events_list = processor.produce_generic_events(serif_doc, generic_event_files[docid])
        result[doc_type]["generic_events"].extend(generic_events_list)
        result["all"]["generic_events"].extend(generic_events_list)

for doc_type in result:
    outfile = os.path.join(output_dir, doc_type + ".json")
    o = codecs.open(outfile, 'w', encoding='utf8')
    o.write(json.dumps(result[doc_type], sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False))
    o.close()
