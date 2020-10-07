import json

from itertools import chain, combinations

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def main(structure_query_json_path,output_path):
    with open(structure_query_json_path) as fp:
        j = json.load(fp)
    with open(output_path,'w') as wfp:
        wfp.write("{}\t{}\t{}\n".format("query_id", "query_string", "domain_id"))
        for en in j:
            query_original = en['text']
            query_escaped = query_original.replace(" ", "_")
            query_set = set()
            for idx,action in enumerate(powerset(en['actions'])):
                current_query = " ".join(i['text'].lower() for i in action)
                if len(current_query)<1:
                    continue
                else:
                    query_set.add(current_query)
            for idx,potential_query in enumerate(sorted(query_set,key=lambda x:x.count(" "),reverse=True)):
                if " " in potential_query:
                    wfp.write("{}_{}\t\"{}\"\t{}\n".format(query_escaped,idx, potential_query, "TBD"))
                else:
                    wfp.write("{}_{}\t{}\t{}\n".format(query_escaped,idx, potential_query, "TBD"))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_structure_query_json', required=True)
    parser.add_argument('--output_path', required=True)
    args = parser.parse_args()
    # structured_query_path = "/home/hqiu/Public/structure_query_dryrun_110619.json"
    # output_path = "/home/hqiu/tmp/query.tsv"
    main(args.input_structure_query_json,args.output_path)