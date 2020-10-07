import json


def main():
    input_json_path = "/home/hqiu/Public/parsed_collab.json"
    output_query_file_path = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/causeex.m24.clir.test.102419/clir_corpus/query.tsv"

    with open(input_json_path) as fp:
        j = json.load(fp)

    query_set = set()
    for k, vs in j.items():
        q = vs[0].lower()
        query_set.add(q)

    with open(output_query_file_path, 'w') as fp:
        fp.write("{}\t{}\t{}\n".format("query_id", "query_string", "domain_id"))
        for i in query_set:
            qid = i.replace(" ", "_")
            if " " in i:
                fp.write("{}\t\"{}\"\t{}\n".format(qid, i, "TBD"))
            else:
                fp.write("{}\t{}\t{}\n".format(qid, i, "TBD"))


if __name__ == "__main__":
    main()
