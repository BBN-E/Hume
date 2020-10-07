
import sys, os, codecs, operator

if len(sys.argv) != 3:
    print("Usage: " + sys.argv[0] + " input_directory_of_tsv_files output_file")
    sys.exit(1)

input_dir, output_file = sys.argv[1:]

o = codecs.open(output_file, 'w', encoding='utf8')

relations_to_count = dict() # (actor1, actor2) => count
filenames = os.listdir(input_dir)
for filename in filenames:
    f = os.path.join(input_dir, filename)
    i = codecs.open(f, encoding='utf8')

    for line in i: 
        line = line.strip()
        pieces = line.split("\t")
        if len(pieces) != 3:
            print("Malformed file")
            sys.exit(1)
        actor1 = pieces[0]
        actor2 = pieces[1]
        count = int(pieces[2])
        
        key = (actor1, actor2)
        if key not in relations_to_count:
            relations_to_count[key] = 0
        relations_to_count[key] += count
    i.close()

sorted_relations = sorted(relations_to_count.items(), key=operator.itemgetter(1))
sorted_relations.reverse()

for relation, count in sorted_relations:
    o.write(relation[0] + "\t" + relation[1] + "\t" + str(count) + "\n")

o.close()
