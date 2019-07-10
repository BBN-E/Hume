# Sample call:
# python /nfs/raid66/u14/users/azamania/git/Hume/src/python/misc/adjust_entity_offsets_in_unification_json.py /nfs/raid87/u11/users/azamania/unification_sample_korea/bbn_sample_korea_json_2  /nfs/raid87/u11/users/azamania/unification_sample_korea/bbn_sample_korea_json_3 /nfs/raid87/u11/users/azamania/unification_sample_korea/metadata.txt

import sys, os, codecs, json

def adjust_frame(frame, offset):
    arguments = frame["arguments"]
    for argument in arguments:
        if "entity" in argument:
            adjust_entity(argument["entity"], offset)
        if "frame" in argument:
            adjust_frame(argument["frame"], offset)

def adjust_entity(entity, offset):
    entity["evidence"]["span"]["start"] += offset
    entity["evidence"]["head_span"]["start"] += offset
    
def get_adjustment(frame, offsets):
    frame_start = frame["evidence"]["sentence"]["start"]
    adjustment = None
    for offset in offsets:
        if frame_start > offset:
            adjustment = offset
    return adjustment

if len(sys.argv) != 4:
    print "Usage: input-dir output-dir metadata-file"
    sys.exit(1)

input_dir, output_dir, metadata_file = sys.argv[1:]

# read offset adjustments
offsets = dict() # UUID to possible adjustment list
uuid_count = dict() # UUID to number of sgm files that correspond to uuid
m = codecs.open(metadata_file, 'r', encoding='utf8')
for line in m:
    pieces = line.split("\t")
    uuid = pieces[6]
    adjustment = int(pieces[7])
    if uuid not in uuid_count:
        uuid_count[uuid] = 0
    uuid_count[uuid] += 1
    
    if uuid not in offsets:
        offsets[uuid] = []
    offsets[uuid].append(adjustment)
    offsets[uuid] = sorted(offsets[uuid])
    
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

filenames = os.listdir(input_dir)
for filename in filenames:
    uuid = filename[0:-5]
    
    input_file = os.path.join(input_dir, filename)
    i = codecs.open(input_file, 'r', encoding='utf8')
    json_obj = json.loads(i.read())
    i.close()
    
    output_file = os.path.join(output_dir, filename)
    o = codecs.open(output_file, 'w', encoding='utf8')
    
    if len(offsets[uuid]) > 1:
        print uuid

    for frame in json_obj:
        adjustment = get_adjustment(frame, offsets[uuid])
        adjust_frame(frame, adjustment)

    o.write(json.dumps(json_obj, sort_keys=True, indent=4, ensure_ascii=False))
    o.close()
