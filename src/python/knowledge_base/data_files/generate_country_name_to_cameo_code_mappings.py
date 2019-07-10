#!/opt/Python-2.7.8-x86_64/bin/python2.7

import sqlite3
import codecs
import os
import json
import re

conn = sqlite3.connect("/nfs/raid87/u14/CauseEx/Assessment/M9/awake_dbs/causeex_dbpedia_20170308_m9.sqlite")
cursor = conn.cursor()

def get_geonameid_for_canonical_name(canonical_name):
    cursor.execute("select geonameid from actor where canonicalname=? and entitytype='GPE' and entitysubtype='Nation'", (canonical_name,))
    query_results = cursor.fetchall()
    assert len(query_results) == 1
    return query_results[0][0]

def get_alternate_names_for_geoname_id(geonameid):
    cursor.execute("select alternate_name from altnames where geonameid=?", (geonameid,))
    query_results = cursor.fetchall()
    return [t[0] for t in query_results]

def read_canonical_country_name_to_cameo_code_map():
    canonical_country_name_to_cameo_code = dict()
    valid_line_pattern = re.compile("^.* [A-Z]{3}$") # some items in country_codes.txt don't have a country code entry - use this to filter them out
    with codecs.open("country_codes.txt", "r", encoding="utf8") as f:
        for line in f.readlines():
            line = line.rstrip()
            if not valid_line_pattern.match(line):
                continue
            [canonical_country_name, cameo_code] = line.rsplit(" ", 1)
            canonical_country_name_to_cameo_code[canonical_country_name] = cameo_code
    return canonical_country_name_to_cameo_code

canonical_country_name_to_cameo_code = read_canonical_country_name_to_cameo_code_map()
all_country_name_to_cameo_code = dict(canonical_country_name_to_cameo_code)
for canonical_country_name in canonical_country_name_to_cameo_code:
    cameo_code = canonical_country_name_to_cameo_code[canonical_country_name]
    # add alternate names
    geonameid = get_geonameid_for_canonical_name(canonical_country_name)
    alternate_country_names = get_alternate_names_for_geoname_id(geonameid)
    for alternate_country_name in alternate_country_names:
        all_country_name_to_cameo_code[alternate_country_name] = cameo_code

conn.close()

output_file_path = os.path.abspath("../config_files/country_name_to_cameo-code_mapping.json")
output_file = codecs.open(output_file_path, "w")
print "writing to " + output_file_path
output_file.write(json.dumps(all_country_name_to_cameo_code, indent=2, sort_keys=True))
output_file.close()
