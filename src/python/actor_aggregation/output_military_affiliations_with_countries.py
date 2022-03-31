# Sample call:
# python3 

# This loads the entity groups in KBs and looks in the AWAKE DB for any affiliated entities
# Used to produce a data file that will be used in a KB Resolver


import pg8000
import os, sys, codecs, operator

blacklist = []
actor_id_to_iso_code = dict()

def get_iso_code(conn, actor_id):
    if actor_id in actor_id_to_iso_code:
        return actor_id_to_iso_code[actor_id]
    cur = conn.cursor()
    cur.execute("""select isocode from actor a, actorisocode i
                   where a.actorid=i.actorid and a.actorid=%s""",
                   (actor_id,))
    row = cur.fetchone()
    if row is None:
        actor_id_to_iso_code[actor_id] = None
        return None

    actor_id_to_iso_code[actor_id] = row[0]
    return row[0]

def get_military_actor_ids(conn):
    results = set()
    cur = conn.cursor()

    cur.execute(""" 
                select a.actorid, a.canonicalname 
	        from actor a, sector s, actorsectorlink asl
	        where asl.actorid=a.actorid and asl.sectorid=s.sectorid
	        and s.sectorid=14""")
    while True:
        row = cur.fetchone()
        if row is None:
            break
        results.add(row[0])
    return results

def get_actors_affiliated_with_country(conn, country_actor_id):
    results = []
    cur = conn.cursor()
    # External facts
    # All possible fact types: (2, 5, 6, 7, 8, 16, 23, 48, 62)
    # Less aggressive fact types used for NATO countries: (2, 5, 6, 7, 48, 60)

    cur.execute("""
                select efa1.actorid, a.canonicalname, ft.facttypename
                from actor a, externalfact ef, externalfactargument efa1, externalfactargument efa2, facttype ft
                where externalfacttypeid in (2, 5, 6, 7, 8, 16, 23, 48, 62)
                and efa1.externalfactid=ef.externalfactid and efa2.externalfactid=ef.externalfactid
                and ef.externalfacttypeid=ft.facttypeid
                and efa2.actorid=%s and efa1.actorid=a.actorid 
                and a.entitytype='ORG'
                and efa1.actorid!=efa2.actorid order by a.importancescore DESC""", (country_actor_id,))
    while (True):
        row = cur.fetchone()
        if row is None:
            break

        related_actorid = row[0]
        canonical_name = row[1]
        fact_name = row[2]

        results.append((related_actorid, canonical_name, fact_name,))

    # actor on left of actorlink
    cur.execute("""
         SELECT a.actorid, a.canonicalname
         FROM actorlink al, actor a
         WHERE rightactorid=%s AND a.actorid=al.leftactorid
         AND a.entitytype='ORG'
         ORDER by importancescore DESC""", (actor_id,))
    
    while (True):
        row = cur.fetchone()
        if row is None:
            break

        related_actorid = row[0]
        canonical_name = row[1]
        results.append((related_actorid, canonical_name, "LINK"))

    return results

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: " + sys.argv[0] + " actor_db_name list_of_relevant_country_actor_ids iso_code_to_cameo_code_file output_file")
        sys.exit(1)

    awake_db_name = sys.argv[1]
    relevant_country_actor_id_list = sys.argv[2]
    iso_code_to_cameo_code_file = sys.argv[3]
    output_file = sys.argv[4]

    iso_code_to_cameo_code = dict()
    iso = codecs.open(iso_code_to_cameo_code_file, 'r', encoding='utf8')
    for line in iso:
        line = line.strip()
        pieces = line.split()
        iso_code_to_cameo_code[pieces[0]] = pieces[1]
    iso.close()

    conn = pg8000.connect(host="awake-hn-01", user="azamania", password="Welcome123$", database=awake_db_name, socket_timeout=1200)
    cur = conn.cursor()
    
    c = open(relevant_country_actor_id_list)
    relevant_actor_ids = set()
    for line in c:
        line = line.strip()
        relevant_actor_ids.add(int(line.split()[0]))
    c.close()

    o = codecs.open(output_file, 'w', encoding='utf8')

    military_actor_ids = get_military_actor_ids(conn)
    
    relations = set()
    count = 0
    for actor_id in relevant_actor_ids:
        iso_code = get_iso_code(conn, actor_id)
        cameo_code = None
        if iso_code is not None:
            cameo_code = iso_code_to_cameo_code[iso_code]
        
        if count % 1 == 0:
            print(str(count))
        count += 1

        #if count == 6:
        #    break

        affiliated_actor_ids = get_actors_affiliated_with_country(conn, int(actor_id))
        for affiliated_actor_id, canonical_name, fact_type in affiliated_actor_ids:
            if affiliated_actor_id in military_actor_ids:
                relations.add(str(affiliated_actor_id) + " " + str(cameo_code) + " # " + canonical_name)

    for relation in relations:
        o.write(relation + "\n")

    o.close()
    conn.close()
