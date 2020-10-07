import sys, os, pg8000, codecs
from utilities import *

if len(sys.argv) != 5:
    print("Usage: " + sys.argv[0] + " awake_actor_db actor_id_list geonames_to_wikipedia_file output_file")
    sys.exit(1)

awake_db, actor_id_list, geonames_to_wikipedia_file, output_file = sys.argv[1:]

o = codecs.open(output_file, 'w', encoding='utf8')

input_actor_infos = set()
i = open(actor_id_list)
for line in i: 
    line = line.strip()
    if line.startswith("#"):
        continue
    pieces = line.split(" ", 1)
    actor_info = (int(pieces[0]), pieces[1],)
    input_actor_infos.add(actor_info)
i.close()

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




conn = pg8000.connect(host="awake-hn-01", user="azamania", password="Welcome123$", database=awake_db, socket_timeout=1200)
cur = conn.cursor()

for actor_info in input_actor_infos:
    actor_id, actor_name = actor_info
    print(str(actor_id) + " " + actor_name)
    
    external_url = None

    if actor_name == "European Union":
        external_url = "http://en.wikipedia.org/wiki/European_Union"
    else:
        external_url = get_external_url_for_actor_id(cur, actor_id)

    # ORGs + PERs
    cur.execute("""SELECT string FROM actorstring 
                   WHERE actorid=%s""", (actor_id,))
    while (True):
        row = cur.fetchone()
        if row is None:
            break
    
        o.write(external_url + "\t" + row[0] + "\n")

    # cities/countries
    cur.execute(
        """SELECT alternate_name FROM actor a, altnames n
           WHERE a.geonameid=n.geonameid AND a.actorid=%s""",
        (actor_id,))

    while (True):
        row = cur.fetchone()
        if row is None:
            break
        
        external_url = convert_to_wikipedia_url(external_url, geonames_to_wikipedia)
        o.write(external_url + "\t" + row[0] + "\n")
    
 

conn.close()
o.close()
