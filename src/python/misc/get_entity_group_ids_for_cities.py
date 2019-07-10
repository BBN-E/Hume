import sys, os, codecs, sqlite3

# Canonical names of countries we want to grab cities for
countries = ["Federal Republic of Nigeria"]

if len(sys.argv) != 3:
    print "Usage: input-sqlite-awake-db output-file"
    sys.exit(1)

input_db, output_file = sys.argv[1:]

conn = sqlite3.connect(input_db)
o = codecs.open(output_file, 'w', encoding='utf8')

cur = conn.cursor()
for country in countries:
    query = "SELECT isocode FROM actor a, actorisocode aic WHERE a.actorid=aic.actorid AND a.canonicalname=?"
    cur.execute(query, (country,))
    row = cur.fetchone()
    if not row:
        print "Could not find: " + str(country) + " in database"
        sys.exit(1)
    isocode = row[0]

    query = """SELECT g.name, g.asciiname, a.alternate_name, ac.actorid FROM actor ac, altnames a, geonames g 
    WHERE a.geonameid=g.geonameid AND ac.geonameid=g.geonameid AND g.country_code=?
    AND ac.canonicalname!=?"""

    country_results = set()

#    print query
#    print isocode
#    print country

    print "Executing query"
    cur.execute(query, (isocode, country,))
    print "Done executing"

    count = 0
    while True:
        row = cur.fetchone()
        if row is None:
            break
        if count % 25 == 0:
            print str(count)
        count += 1
        name1 = row[0]
        name2 = row[1]
        name3 = row[2]
        actorid = row[3]
        country_results.add((name1, "EntityUnified-" + str(actorid),))
        country_results.add((name2, "EntityUnified-" + str(actorid),))
        country_results.add((name3, "EntityUnified-" + str(actorid),))

    for name, unified_id in country_results:
        o.write(name + "\t" + country + "\t" + unified_id + "\n")

o.close()
