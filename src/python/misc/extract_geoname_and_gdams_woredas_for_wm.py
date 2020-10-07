import io


def parse_all_country(file_path, africa_country_table):
    et_ids = set()  # Set for Ethiopia
    ss_ids = set()  # Set for South Sudan
    africa_ids = set()
    country_to_geoids = dict()
    id_to_name = dict()
    id_to_asciiname = dict()
    name_to_ids = dict()
    asciiname_to_ids = dict()
    altername_name_to_ids = dict()
    africa_country_two_letter = set()
    geoname_id_to_population = dict()
    with open(africa_country_table) as fp:
        for i in fp:
            i = i.strip()
            africa_country_two_letter.add(i)
    with open(file_path) as fp:
        for i in fp:
            i = i.strip()
            # http://download.geonames.org/export/dump/
            geonameid, name, asciiname, alternatenames, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date = i.split(
                "\t")
            name_to_ids.setdefault(name, set()).add(geonameid)
            asciiname_to_ids.setdefault(asciiname, set()).add(geonameid)
            for alternate_name in alternatenames.split(","):
                altername_name_to_ids.setdefault(alternate_name, set()).add(geonameid)
            id_to_name[geonameid] = name
            id_to_asciiname[geonameid] = asciiname
            geoname_id_to_population[geonameid] = int(population)
            country_to_geoids.setdefault(country_code, set)
            if country_code == "ET":
                et_ids.add(geonameid)
            if country_code == "SS":
                ss_ids.add(geonameid)
            if country_code in africa_country_two_letter:
                africa_ids.add(geonameid)

    acc_name_to_ids = dict()

    for name, ids in name_to_ids.items():
        if len(name) > 0:
            acc_name_to_ids.setdefault(name, set()).update(ids)
    for name, ids in asciiname_to_ids.items():
        if len(name) > 0:
            acc_name_to_ids.setdefault(name, set()).update(ids)
    for name, ids in altername_name_to_ids.items():
        if len(name) > 0:
            acc_name_to_ids.setdefault(name, set()).update(ids)

    for name, ids in acc_name_to_ids.items():
        acc_name_to_ids[name] = list(
            sorted(ids, key=lambda x: (3, geoname_id_to_population[x]) if x in et_ids else (
                2, geoname_id_to_population[x]) if x in ss_ids else (
                1, geoname_id_to_population[x]) if x in africa_ids else (0, geoname_id_to_population[x]),
                   reverse=True))

    return acc_name_to_ids


def append_gadm_woredas(file_path, acc_name_to_ids):
    name_to_ids = dict()
    asciiname_to_ids = dict()
    altername_name_to_ids = dict()
    with open(file_path) as fp:
        for i in fp:
            i = i.strip()
            # http://download.geonames.org/export/dump/
            geonameid, name, asciiname, alternatenames, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date = i.split(
                "\t")
            name_to_ids.setdefault(name, set()).add(geonameid)
            asciiname_to_ids.setdefault(asciiname, set()).add(geonameid)
            for alternate_name in alternatenames.split(","):
                altername_name_to_ids.setdefault(alternate_name, set()).add(geonameid)

    for name, ids in name_to_ids.items():
        if len(name) > 0:
            acc_name_to_ids.setdefault(name, list()).extend(ids)
    for name, ids in asciiname_to_ids.items():
        if len(name) > 0:
            acc_name_to_ids.setdefault(name, list()).extend(ids)
    for name, ids in altername_name_to_ids.items():
        if len(name) > 0:
            acc_name_to_ids.setdefault(name, list()).extend(ids)

    return acc_name_to_ids


def main(all_country_path, africa_country_table, adam_woredas_path, output_path):
    name_to_ids = parse_all_country(all_country_path, africa_country_table)
    name_to_ids = append_gadm_woredas(adam_woredas_path, name_to_ids)
    with io.open(output_path, 'w', encoding='utf-8') as fp:
        for name, ids in name_to_ids.items():
            fp.write("{}\t{}\n".format(name, ids[0]))


if __name__ == "__main__":
    all_country_path = "/nfs/raid88/u10/users/ychan/migration_experiment/geonames/allCountries/allCountries.txt"
    # all_country_path = "/home/hqiu/tmp/test"
    africa_country_table = "/home/hqiu/Public/africa_countries_iso_3166.txt"
    adam_woredas_path = "/home/hqiu/Public/gadm_woredas.txt"
    output_path = "/home/hqiu/tmp/word_to_geoname_id_map"
    main(all_country_path, africa_country_table, adam_woredas_path, output_path)
