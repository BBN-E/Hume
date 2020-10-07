import json, os, codecs, sys
from collections import defaultdict, Counter


def read_lines(file):
    lines = []
    with open(file) as fp:
        while True:
            sline = fp.readline().strip()
            if not sline:
                break

            if not sline.startswith("#") and sline:
                if "GeneralConcepts#description" in sline or "ICM#has_factor_type" in sline or "ICM#has_factor" in sline:
                    lines.append(sline)
    return lines

def parse_valid_line(sline):
    sline = sline.strip()

    if not sline.startswith("#") and sline:
        if sline:
            if len(sline.split("\t"))==4:
                s, p, o, _ = sline.split("\t")
                return s, p, o
            else:
                print("SKIP: " + sline)

    return None, None, None

def get_trigger(description):
    # print(description)
    index_start = description.index("[[") + 2
    index_end = description.index("]]")
    trigger_text = description[index_start:index_end]
    return trigger_text

def get_trigger_freq(triggers):
    cnt = Counter()
    for trigger in triggers:
        cnt[trigger]+=1
    return cnt

if __name__ == "__main__":
    # file = "/mnt/c/Users/bmin/Downloads/sams_lcc_user_submitted/sams_lcc_user_submitted.nt.mod.head"
    # file = "/mnt/c/Users/bmin/Downloads/sams_lcc_user_submitted/sams_lcc_user_submitted.nt.mod
    # preprocessing: cat /mnt/c/Users/bmin/Downloads/sams_lcc_user_submitted/sams_lcc_user_submitted.nt | grep -v "#date_" |grep -v "#classification" |grep -v "has_document_type" | grep -v "#title" > /mnt/c/Users/bmin/Downloads/sams_lcc_user_submitted/sams_lcc_user_submitted.nt.mod
    file = "C:\\Users\\bmin\\Downloads\\sams_lcc_user_submitted\\sams_lcc_user_submitted.nt.mod"

    factor_ids = set()
    factor_id_to_type = defaultdict(list)
    factor_details_id_to_type = dict()
    factor_type_to_text = defaultdict(list)

    # read types
    lines = read_lines(file)
    for line in lines:
        s, p, o = parse_valid_line(line)
        if s and p and o:
            if p=="<http://ontology.causeex.com/ontology/odps/ICM#has_factor_type>":
                factor_details_id=s
                factor_type=o
                factor_details_id_to_type[factor_details_id]=factor_type

    # read factor details
    lines = read_lines(file)
    for line in lines:
        s, p, o = parse_valid_line(line)
        if s and p and o:
            if p=="<http://ontology.causeex.com/ontology/odps/ICM#has_factor>":
                factor_id=s
                factor_details_id=o

                factor_ids.add(factor_id)
                factor_id_to_type[factor_id].append(factor_details_id_to_type[factor_details_id])

    # read triggers
    lines = read_lines(file)
    for line in lines:
        s, p, o = parse_valid_line(line)
        if s and p and o:
            if p=="<http://ontology.causeex.com/ontology/odps/GeneralConcepts#description>":
                factor_id=s
                description=o
                if factor_id in factor_ids:
                    trigger_text = get_trigger(description)

                    for factor_type in factor_id_to_type[s]:
                        # print(str(factor_type))
                        factor_type_to_text[factor_type].append(trigger_text)

    for factor_type in factor_type_to_text:
        cnt = get_trigger_freq(factor_type_to_text[factor_type])

        for k, v in sorted(cnt.items(), key=lambda item: 0-item[1]):
            print ("type:\t" + factor_type + "\t" + str(v) + "\t" + k)