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

    print ("Could not find external uri for " + str(actor_id))

def convert_original_source_element_to_wikipedia(original_source_element):
    wikipedia_path = original_source_element.replace("dbpedia.org/resource", "en.wikipedia.org/wiki", 1)
    if wikipedia_path.startswith("<"):
        wikipedia_path = wikipedia_path[1:]
    if wikipedia_path.endswith(">"):
        wikipedia_path = wikipedia_path[:-1]
    return wikipedia_path

printed_geonames = set()
# if url is a geonames URL, make it a wikipedia URL
def convert_to_wikipedia_url(url, geonames_to_wikipedia):
    if url.find("geoname") != -1:
        if url in geonames_to_wikipedia:
            url = geonames_to_wikipedia[url]
        elif url not in printed_geonames:
            print("Need geoname->wikipedia mapping for " + url)
            printed_geonames.add(url)
    return url
