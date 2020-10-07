# Sample call:
# python3 /nfs/raid66/u14/users/azamania/git/Hume/src/python/actor_aggregation/output_affiliation_information_info.py /nfs/raid87/u11/users/azamania/actor_aggregation/pickled_kbs_127_doc_set.list causeex_dbpedia_20170308_collab2 /nfs/raid87/u11/users/azamania/actor_aggregation/baltic_countries.txt /nfs/raid66/u14/users/azamania/git/Hume/src/python/knowledge_base/data_files/awake_iso_country_code_to_cameo.txt  /nfs/raid66/u14/users/azamania/git/Hume/src/python/knowledge_base/data_files/actor_affiliation_info.txt

# This loads the entity groups in KBs and looks in the AWAKE DB for any affiliated entities
# Used to produce a data file that will be used in a KB Resolver


import pickle, pg8000
import os, sys, codecs, unidecode, operator

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'knowledge_base'))

from knowledge_base import KnowledgeBase

affiliated_actors_cache = dict()
actor_id_to_iso_code = dict() # country_actor_id to iso_code
iso_code_to_cameo_code = dict()

blacklist = [(191565, 117970), # Stripe affiliated_with Kingdom of Sweden
             (191565, 2858), # Stripe affiliated_with Kingdom of Denmark
             (191565, 52158), # Stripe affiliated_with Republic of Finland
             (191565, 56489), # Stripe affiliated_with Federal Republic of Germany
             (198131, 56489), # European Council on Foreign Relations affiliated_with Federal Republic of Germany
             (198131, 74394), # European Council on Foreign Relations affiliated_with Republic of Poland
             (310240, 52158), # Gennady Timchenko affiliated_with Republic of Finland
             (247983, 42620), # Carnegie Endowment for International Peace affiliated_with People’s Republic of China
             (436792, 42620), # Aleksey Pushkov affiliated_with People’s Republic of China
             (549824, 42620), # Sergei Stepashin affiliated_with People’s Republic of China
             (237317, 42620),  # Fox affiliated_with People’s Republic of China
             (622025, 'GBR'), # John Peters affiliated_with United Kingdom of Great Britain and Northern Ireland
             (609648, 'USA'), # Jim Thomas affiliated_with United States
             (237317, 'BGR'), # Fox affiliated_with Republic of Bulgaria
             (191565, 'LUX'), # Stripe affiliated_with Grand Duchy of Luxembourg
             (575557, 'GBR'), # Mark A. Smith affiliated_with United Kingdom of Great Britain and Northern Ireland
             (247142, 'USA'), # Ace affiliated_with United States
             (480727, 'DEU'), # Robert Bosch affiliated_with Federal Republic of Germany
             (237317, 'HRV'), # Fox affiliated_with Republic of Croatia
             (226743, 'USA'), # Eureka affiliated_with United States
             (731144, 'USA'), # David Brooks affiliated_with United States
             (721269, 'GBR'), # Andrew Macdonald affiliated_with United Kingdom of Great Britain and Northern Ireland
             (513699, 'SVN'), # Frank Gorenc affiliated_with Republic of Slovenia
             (241031, 'USA'), # CNN International affiliated_with United States
             (145233, 'USA'), # United Press International affiliated_with United States
             (177592, 'USA'), # Seventeen (American magazine) affiliated_with United States
             (567832, 'USA'), # Hal Varian affiliated_with United States
             (432460, 'USA'), # Alireza Nader affiliated_with United States
             (471554, 'USA'), # Andrew Wilson affiliated_with United States
             (401781, 'NLD'), # Ivo Daalder affiliated_with Kingdom of the Netherlands
             (613226, 'GBR'), # Anne McElvoy affiliated_with United Kingdom of Great Britain and Northern Ireland
             (211611, 'USA'), # Star affiliated_with United States
             (243643, 'USA'), # Sentinel affiliated_with United States
             (199950, 'USA'), # University of Minnesota Press affiliated_with United States
             (180080, 'TUR'), # Dia affiliated_with Republic of Turkey
             (234239, 'USA'), # Battalion affiliated_with United States
             (440693, 'GBR'), # William Luce affiliated_with United Kingdom of Great Britain and Northern Ireland
             (147172, 'GBR'), # Times Higher Education affiliated_with United Kingdom of Great Britain and Northern Ireland
             (345926, 'USA'), # Cristopher Moore affiliated_with United States
             (728861, 'USA'), # Max Fisher affiliated_with United States
             (482319, 'GBR'), # Chris Williams affiliated_with United Kingdom of Great Britain and Northern Ireland
             (373855, 'GBR'), # Peter Baker (British politician) affiliated_with United Kingdom of Great Britain and Northern Ireland
             (350121, 'GBR'), # Michael Bradshaw affiliated_with United Kingdom of Great Britain and Northern Ireland
             (255665, 'USA'), # Path affiliated_with United States
             (299130, 'LVA'), # Harmony Centre affiliated_with Republic of Latvia
             (191565, 'GBR'), # Stripe affiliated_with United Kingdom of Great Britain and Northern Ireland
             (191565, 'ITA'), # Stripe affiliated_with Repubblica Italiana
             (191565, 'ESP'), # Stripe affiliated_with Kingdom of Spain
             (191565, 'ITA'), # Stripe affiliated_with Repubblica Italiana
             (191565, 'NLD'), # Stripe affiliated_with Kingdom of the Netherlands
             (191565, 'NOR'), # Stripe affiliated_with Kingdom of Norway
             (191565, 'FRA'), # Stripe affiliated_with Republic of France
             (191565, 'USA') # Stripe affiliated_with United States

]

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

def get_affiliated_actors(conn, actor_id):

    if actor_id in affiliated_actors_cache:
        return affiliated_actors_cache[actor_id]

    results = []
    cur = conn.cursor()
    # External facts
    # All possible fact types: (2, 5, 6, 7, 8, 16, 23, 48, 62)
    # Less aggressive fact types used for NATO countries: (2, 5, 6, 7, 48, 60)

    cur.execute("""
                select a.actorid, a.canonicalname, ft.facttypename
                from actor a, externalfact ef, externalfactargument efa1, externalfactargument efa2, facttype ft
                where externalfacttypeid in (2, 5, 6, 7, 8, 16, 23, 48, 62)
                and efa1.externalfactid=ef.externalfactid and efa2.externalfactid=ef.externalfactid
                and ef.externalfacttypeid=ft.facttypeid
                and efa1.actorid=%s and efa2.actorid=a.actorid 
                and efa1.actorid!=efa2.actorid order by a.importancescore DESC""", (actor_id,))
    while (True):
        row = cur.fetchone()
        if row is None:
            break

        related_actorid = row[0]
        canonical_name = row[1]
        fact_name = row[2]

        results.append((related_actorid, canonical_name, fact_name,))

    # actor on left of actor_info
    cur.execute("""
         SELECT a.actorid, a.canonicalname
         FROM actorlink al, actor a
         WHERE leftactorid=%s AND a.actorid=al.rightactorid
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
    if len(sys.argv) != 6:
        print("Usage: " + sys.argv[0] + "list_of_kbs actor_db_name list_of_relevant_country_actor_ids iso_code_to_cameo_code_file output_file")
        sys.exit(1)

    kb_list = sys.argv[1]
    awake_db_name = sys.argv[2]
    relevant_country_actor_id_list = sys.argv[3]
    iso_code_to_cameo_code_file = sys.argv[4]
    output_file = sys.argv[5]

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

    count = 0
    k = open(kb_list)
    relations = set()
    for line in k:
        if count % 1 == 0:
            print(str(count))
        count += 1
        pickled_kb_file = line.strip()
        p = open(pickled_kb_file, "rb")
        kb = pickle.load(p)
        p.close()
        
        #if count == 5: 
        #    break

        for egid, entity_group in kb.get_entity_groups():
            if entity_group.actor_id is None:
                continue
            try:
                actor_id_int = int(entity_group.actor_id)
            except ValueError:
                continue

            affiliated_actor_ids = get_affiliated_actors(conn, int(entity_group.actor_id))
            for (affiliated_actor_id, affiliated_actor_name, fact_type) in affiliated_actor_ids:
                if affiliated_actor_id not in relevant_actor_ids:
                    continue

                iso_code = get_iso_code(conn, affiliated_actor_id)
                cameo_code = None
                if iso_code is not None:
                    cameo_code = iso_code_to_cameo_code[iso_code]
                
                if ((entity_group.actor_id, affiliated_actor_id) in blacklist or 
                    (entity_group.actor_id, cameo_code) in blacklist):
                    continue

                affiliated_actor_code_or_id = affiliated_actor_id
                
                if iso_code is not None:
                    affiliated_actor_code_or_id = iso_code_to_cameo_code[iso_code]

                relations.add(str(entity_group.actor_id) + " " + str(affiliated_actor_code_or_id) + " # " +  entity_group.canonical_name + " affiliated_with " + affiliated_actor_name)

    for relation in relations:
        o.write(relation + "\n")
    k.close()
    o.close()
    conn.close()
