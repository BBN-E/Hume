import sys, os, codecs
from utilities import *

SCORE_DENOMINATOR = 40
MIN_COUNT = 5

def calculate_score(count):
    denom = float(SCORE_DENOMINATOR)
    s = count / denom
    if s > 1.0:
        s = 1.0

    s = s * 0.95

    if s < 0.5:
        s = 0.5
    
    return s

if len(sys.argv) != 6: 
    print("Usage: " + sys.argv[0] + " awake_db_relations kb_relations bad_relations geonames_to_wikipedia_file output_file")
    sys.exit(1)

awake_db_relations, kb_relations, bad_relations, geonames_to_wikipedia_file, output_file = sys.argv[1:]

o = codecs.open(output_file, 'w', encoding='utf8')

known_relations = set() # (actor1, actor2)
actors_already_found = set() # actor1
geonames_to_wikipedia = dict() # http://www.geonames.org/1814991 => http://en.wikipedia.org/wiki/China

# geonames to wikipedia -- just used when printing out the final results
print("Reading geonames to wikipedia mapping")
g = codecs.open(geonames_to_wikipedia_file, 'r', encoding='utf8')
for line in g:
    line = line.strip()
    pieces = line.split("\t")
    if len(pieces) != 2:
        print("Malformed geonames wikipedia file")
        sys.exit(1)
    geoname = pieces[0]
    wikipedia = pieces[1]
    geonames_to_wikipedia[geoname] = wikipedia
g.close()

# Bad relations
print("Reading bad relations")
b = codecs.open(bad_relations, 'r', encoding='utf8')
for line in b:
    line = line.strip()
    pieces = line.split("\t")
    if len(pieces) != 2:
        print("Malformed bad relations file")
        sys.exit(1)
    actor1 = pieces[0]
    actor2 = pieces[1]
    
    key = (actor1, actor2)
    known_relations.add(key)
b.close()

# AWAKE relations
print("Reading AWAKE relations")
a = codecs.open(awake_db_relations, 'r', encoding='utf8')
for line in a:
    line = line.strip()
    pieces = line.split("\t")
    if len(pieces) != 2:
        print("Malformed awake relations file")
        sys.exit(1)
    actor1 = pieces[0]
    actor2 = pieces[1]
    
    key = (actor1, actor2)
    if key in known_relations:
        continue
    known_relations.add(key)
    actors_already_found.add(pieces[0])

    # convert geonames to wikipedia urls
    actor1 = convert_to_wikipedia_url(actor1, geonames_to_wikipedia)
    actor2 = convert_to_wikipedia_url(actor2, geonames_to_wikipedia)

    o.write(actor1 + "\t" + actor2 + "\t" + "1.0" + "\n")
a.close()

# Sorted KB relations
print("Reading KB relations")
k = codecs.open(kb_relations, 'r', encoding='utf8')
for line in k:
    line = line.strip()
    pieces = line.split("\t")
    if len(pieces) != 3:
        print("Malformed kb relations file")
        sys.exit(1)
    actor1 = pieces[0]
    actor2 = pieces[1]
    count = int(pieces[2])
    if count <= MIN_COUNT:
        continue
    if actor1 in actors_already_found:
        continue
    actors_already_found.add(actor1)
    key = (actor1, actor2)
    if key in known_relations:
        continue
    
    actor1 = convert_to_wikipedia_url(actor1, geonames_to_wikipedia)
    actor2 = convert_to_wikipedia_url(actor2, geonames_to_wikipedia)

    score = calculate_score(count)
    str_score = "{0:.2f}".format(score)
    o.write(actor1 + "\t" + actor2 + "\t" + str_score + "\n")

o.close()
