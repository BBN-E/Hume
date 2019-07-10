# Start with a list of countries and an AWAKE DB, pull out actor 
# aggregation information for those countries -- alternate names
# and actors related to those countries. 

# Sample command line:
# python /nfs/raid66/u14/users/azamania/git/Hume/src/python/misc/get_actor_aggregation_info_awake_db.py causeex_dbpedia_20170308_m15a /nfs/raid87/u11/users/azamania/actor_aggregation/actor_id_list.txt /nfs/raid87/u11/users/azamania/actor_aggregation/awake_db_relations.tsv

import sys, os, json, pg8000, codecs, re

all_digits_re = re.compile("^\d+$")

def convert_original_source_element_to_wikipedia(original_source_element):
    wikipedia_path = original_source_element.replace("dbpedia.org/resource", "en.wikipedia.org/wiki", 1)
    if wikipedia_path.startswith("<"):
        wikipedia_path = wikipedia_path[1:]
    if wikipedia_path.endswith(">"):
        wikipedia_path = wikipedia_path[:-1]
    return wikipedia_path

def get_external_url_for_actor_id(cur, actor_id):
    
    # Check for geoname id
    cur.execute(
        """SELECT geonameid FROM actor WHERE actorid=%s""", (actor_id,))
    row = cur.fetchone()
    if row is not None and str(row[0]) != "None":
        return "http://www.geonames.org/" + str(row[0])

    # Check for dbpedia path
    cur.execute(
        """SELECT originalsourceelement from actorsource 
           WHERE actorid=%s""", (actor_id,))
    row = cur.fetchone()
    if row is not None:
        original_source_element = row[0]
        wikipedia_path = convert_original_source_element_to_wikipedia(original_source_element)
        
        return wikipedia_path

    print "Could not find external uri for " + str(actor_id)

def write_related_actor_info(cur, actor_id, actor_url, actor_name, rel_o):
    written_count = 0
    written_relations = set()

    # External facts
    cur.execute("""
                select a.actorid, a.canonicalname, ft.facttypename, s.originalsourceelement
                from actor a, externalfact ef, externalfactargument efa1, externalfactargument efa2, facttype ft, actorsource s
                where externalfacttypeid in (2, 5, 6, 7, 8, 16, 48, 60)
                and efa1.externalfactid=ef.externalfactid and efa2.externalfactid=ef.externalfactid
                and ef.externalfacttypeid=ft.facttypeid
                and efa1.actorid=%s and efa2.actorid=a.actorid 
                and s.actorid=a.actorid
                and efa1.actorid!=efa2.actorid order by a.importancescore DESC""", (actor_id,))
    
    while (True):
        row = cur.fetchone()
        if row is None:
            break

        related_actorid = row[0]
        canonical_name = row[1]
        related_actor_url = row[3]
                
        if written_count >= 100 or related_actor_url.find("dbpedia.org/resource") == -1:
            break

        related_actor_url = convert_original_source_element_to_wikipedia(related_actor_url)
        
        relation_string = related_actor_url + "\taffiliated_with\t" + actor_url + "\t1.00\t" + "# " + canonical_name + " affiliated_with " + actor_name
        if relation_string not in written_relations:
            rel_o.write(relation_string + "\n")
            written_relations.add(relation_string)
            written_count += 1

    # actor on right of actor link table
    cur.execute("""
         SELECT a.actorid, a.canonicalname, a.importancescore, so.originalsourceelement
         FROM actorlink al, actor a, actorsource so 
         WHERE rightactorid=%s AND a.actorid=al.leftactorid AND so.actorid=al.leftactorid
         ORDER by importancescore DESC""", (actor_id,)) 

   
    while (True):
        row = cur.fetchone()
        if row is None:
            break

        related_actorid = row[0]
        canonical_name = row[1]
        related_actor_url = row[3]
        
        if written_count >= 100 or related_actor_url.find("dbpedia.org/resource") == -1:
            break

        related_actor_url = convert_original_source_element_to_wikipedia(related_actor_url)
        
        relation_string = related_actor_url + "\taffiliated_with\t" + actor_url + "\t1.00\t" + "# " + canonical_name + " affiliated_with " + actor_name
        if relation_string not in written_relations:
            rel_o.write(relation_string + "\n")
            written_relations.add(relation_string)
            written_count += 1

    # actor on left of actor_info
    cur.execute("""
         SELECT a.actorid, a.canonicalname, a.importancescore, so.originalsourceelement
         FROM actorlink al, actor a, actorsource so 
         WHERE leftactorid=%s AND a.actorid=al.rightactorid AND so.actorid=al.rightactorid
         ORDER by importancescore DESC""", (actor_id,))
    
    while (True):
        row = cur.fetchone()
        if row is None:
            break

        related_actorid = row[0]
        canonical_name = row[1]
        related_actor_url = row[3]

        if written_count >= 100 or related_actor_url.find("dbpedia.org/resource") == -1:
            break

        related_actor_url = convert_original_source_element_to_wikipedia(related_actor_url)
        
        relation_string = actor_url + "\taffiliated_with\t" + related_actor_url + "\t1.00\t" + "# " + actor_name + " affiliated_with " + canonical_name
        if relation_string not in written_relations:
            rel_o.write(relation_string + "\n")
            written_relations.add(relation_string)
            written_count += 1

if len(sys.argv) != 4:
    print "Usage: " + sys.argv[0] + " awake_actor_db actor_id_list relation_file"
    sys.exit(1)

awake_actor_db, actor_list, output_file_relation = sys.argv[1:]
rel_o = codecs.open(output_file_relation, 'w', encoding='utf8')

actors = dict() # actor_id: dictionary containing information about actor

input_actor_infos = set()
i = open(actor_list)
for line in i: 
    line = line.strip()
    if line.startswith("#"):
        continue
    pieces = line.split(" ", 1)
    actor_info = (int(pieces[0]), pieces[1],)
    input_actor_infos.add(actor_info)
i.close()

conn = pg8000.connect(host="awake-hn-01", user="azamania", password="Welcome123$", database=awake_actor_db, socket_timeout=1200)
cur = conn.cursor()

# Countries
for actor_info in input_actor_infos:
    actor_id, actor_name = actor_info
    print str(actor_id) + " " + actor_name
    
    external_url = None

    if actor_name == "European Union":
        external_url = "http://en.wikipedia.org/wiki/European_Union"
    else:
        external_url = get_external_url_for_actor_id(cur, actor_id)

    write_related_actor_info(cur, actor_id, external_url, actor_name, rel_o)
    
rel_o.close()
