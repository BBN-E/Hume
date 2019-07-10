import sys, json, io

if len(sys.argv) != 3:
    print "Usage: input-list output-json"
    sys.exit(1)

input_file, output_file = sys.argv[1:]

input_json_paths = [x.strip() for x in open(input_file,'r').readlines()]

out_dict = dict()
for file_ in input_json_paths:
    with io.open(file_,'rb') as f_in:
        d = json.load(f_in,encoding='utf8')
        out_dict.update(d)

with io.open(output_file, 'wb') as f_out:
    json.dump(out_dict, f_out, sort_keys=True, indent=4, encoding="utf-8")
