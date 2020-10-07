import os, sys, json


def get_groundings(extraction):
    event_groundings = [[k, v] for k, v in extraction['frame']['frame_types'].items()]
    factor_groundings = [
        [i['factor_class'], i['relevance'], "trend:{}".format(i['trend']), "magnitude:{}".format(i['magnitude'])] for i
        in extraction['frame']['causal_factors']]
    total = list()
    total.extend(event_groundings)
    total.extend(factor_groundings)
    string_types = ""
    for i in sorted(total, key=lambda x: x[1], reverse=True):
        string_types += "{}:{},{};\n".format(i[0], str(i[1]), ",".join(i[2:]))
    return string_types


rel_cnt = 0


def single_json_handler(json_path):
    global rel_cnt
    with open(json_path) as fp:
        json_ens = json.load(fp)
    for eer in json_ens:
        sentence_text = eer['evidence']['sentence']['text']
        confidence = list(eer['frame_types'].values())[0]
        for left_or_right in eer['arguments']:
            is_right = True if "http://ontology.causeex.com/ontology/odps/CauseEffect#has_effect" == left_or_right[
                'role'] else False
            if is_right:
                right_type_str = get_groundings(left_or_right)
                right_em_str = left_or_right['frame']['evidence']['extended_trigger']['text'].replace("\n", " ")
            else:
                left_type_str = get_groundings(left_or_right)
                left_em_str = left_or_right['frame']['evidence']['extended_trigger']['text'].replace("\n", " ")
                causal_type = left_or_right['role'].split("CauseEffect#")[1]
        print("{} Sentence: {}".format(rel_cnt, sentence_text))
        rel_cnt += 1
        print("\n{}\n{}\n{}:{}\n\n{}\n{}".format(left_em_str,
                                                 left_type_str, causal_type, confidence,
                                                 right_em_str, right_type_str))
        print("----")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--serialization_root", required=True)
    args = parser.parse_args()
    serialization_root = args.serialization_root
    # serialization_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/causeex_sams_estonia.120719.121619/serialization"

    for root, dirs, files in os.walk(serialization_root):
        if "relation" in root:
            for file in files:
                if file.endswith(".json"):
                    single_json_handler(os.path.join(root, file))
