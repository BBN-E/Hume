import sys, os

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input-serialization-dir output-file"
    sys.exit(1)

input_dir, output_file = sys.argv[1:]

o = open(output_file, 'w')

document_type_names = os.listdir(input_dir)
counts = dict() # label => total count
for document_type_name in document_type_names:
    document_type_dir = os.path.join(input_dir, document_type_name)
    filenames = os.listdir(document_type_dir)
    for filename in filenames:
        if not filename.endswith(".info"):
            continue
        info_file = os.path.join(document_type_dir, filename)
        i = open(info_file, 'r')
        for line in i:
            line = line.strip()
            if len(line) == 0:
                continue
            pieces = line.rsplit(":", 1)
            description = pieces[0]
            count = int(pieces[1])
            if description not in counts:
                counts[description] = 0
            counts[description] += count
        i.close()

for description, count in counts.iteritems():
    o.write(description + ": " + str(count) + "\n")

o.close()


        
