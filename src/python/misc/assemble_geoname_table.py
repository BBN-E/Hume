import collections


"""
geonameid         : integer id of record in geonames database
name              : name of geographical point (utf8) varchar(200)
asciiname         : name of geographical point in plain ascii characters, varchar(200)
alternatenames    : alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
latitude          : latitude in decimal degrees (wgs84)
longitude         : longitude in decimal degrees (wgs84)
feature class     : see http://www.geonames.org/export/codes.html, char(1)
feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
country code      : ISO-3166 2-letter country code, 2 characters
cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 200 characters
admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80)
admin3 code       : code for third level administrative division, varchar(20)
admin4 code       : code for fourth level administrative division, varchar(20)
population        : bigint (8 byte int)
elevation         : in meters, integer
dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
timezone          : the iana timezone id (see file timeZone.txt) varchar(40)
modification date : date of last modification in yyyy-MM-dd format
"""

GeoNameEn = collections.namedtuple("GeoNameEn",["geonameid", "name", "asciiname", "alternatenames", "latitude", "longitude", "feature_class", "feature_code", "country_code","cc2","admin1_code","admin2_code","admin3_code","admin4_code","population","elevation","dem","timezone","modification_date"])

def parse_geoname_txt(geoname_txt_path):
    geoname_ens = list()
    with open(geoname_txt_path)as fp:
        for i in fp:
            i = i.strip()
            en = GeoNameEn(*i.split("\t"))
            geoname_ens.append(en)
    return geoname_ens

def read_event_argument_strings(argument_string_path):
    count_dict = dict()
    with open(argument_string_path) as fp:
        for i in fp:
            i = i.strip()
            count_dict[i] = count_dict.get(i,0)+1
    return count_dict

def merge_and_filter_event_argument_strings(argument_dicts,low_cut_freq):
    merged_dict = dict()
    for argument_dic in argument_dicts:
        for argument_name,cnt in argument_dic.items():
            merged_dict[argument_name] = merged_dict.get(argument_name,0)+cnt
    filtered_arguments = set()
    for argument_name,cnt in merged_dict.items():
        if cnt >= low_cut_freq:
            filtered_arguments.add(argument_name)
    return filtered_arguments

def process_geoname_file(geoname_ens,filtered_arguments,output_path):
    match_name_to_matched_geoname_ens = dict()
    for geoname_en in geoname_ens:
        possible_names = set(geoname_en.alternatenames.split(","))
        possible_names.add(geoname_en.name)
        possible_names.add(geoname_en.asciiname)
        set_insec = possible_names.intersection(filtered_arguments)
        if len(set_insec) > 0:
            for name in set_insec:
                match_name_to_matched_geoname_ens.setdefault(name,set()).add(geoname_en)
    with open(output_path,"w") as wfp:
        for match_name,geoname_ens in match_name_to_matched_geoname_ens.items():
            population_sorted = sorted(geoname_ens,key=lambda x:int(x.population),reverse=True)
            deduplicate_dict = dict()
            for geoname_en in population_sorted:
                if geoname_en.asciiname not in deduplicate_dict:
                    deduplicate_dict[geoname_en.asciiname] = int(geoname_en.population)
            wfp.write("{}\t{}\n".format(match_name,"\t".join(k for k,v in sorted(deduplicate_dict.items(),key=lambda x:x[1],reverse=True))))


def main():
    geoname_txt_path = "/nfs/raid88/u10/users/bmin-ad/Experiments/geonames/allCountries.txt"
    geoname_ens = parse_geoname_txt(geoname_txt_path)
    argument_print_f1 = "/home/hqiu/tmp/cn_event_args.list"
    argument_print_f2 = "/home/hqiu/tmp/en_event_args.list"
    output_path = "/home/hqiu/tmp/processed_geoname_table.txt"
    count_dict_1 = read_event_argument_strings(argument_print_f1)
    count_dict_2 = read_event_argument_strings(argument_print_f2)
    filtered_arguments = merge_and_filter_event_argument_strings((count_dict_1,count_dict_2),3)
    process_geoname_file(geoname_ens, filtered_arguments, output_path)


if __name__ == "__main__":
    main()