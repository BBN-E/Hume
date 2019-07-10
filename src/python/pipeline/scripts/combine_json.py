import sys, os, json, codecs

if len(sys.argv) != 3:
    print "Usage: input-dir output-file"
    sys.exit(1)

input_dir, output_file = sys.argv[1:]

o = codecs.open(output_file, 'w', encoding='utf8')

results = []
for filename in os.listdir(input_dir):
    json_file = os.path.join(input_dir, filename)
    i = codecs.open(json_file, 'r', encoding='utf8')
    contents = i.read()
    i.close()
    lst = json.loads(contents)
    for item in lst:
        results.append(item)

o.write(json.dumps(results, sort_keys=True, indent=4, ensure_ascii=False))
o.close()

