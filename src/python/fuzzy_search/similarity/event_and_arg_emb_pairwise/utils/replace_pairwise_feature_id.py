import os, sys, re

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from similarity.event_and_arg_emb_pairwise.utils.feature_loader import load_features


def main(sim_path, feature_list_path, output_path):
    feature_id_to_features = load_features([feature_list_path])
    trigger_re = re.compile(r"\[(.+)\]")
    with open(sim_path) as fp, open(output_path, 'w') as wfp:
        for i in fp:
            i = i.strip()
            src_feature_id, dst_feature_id, score = i.split(" ")
            src_original_text = feature_id_to_features[src_feature_id].aux["originalText"].replace("\t", " ").replace(
                "\n", " ")
            dst_original_text = feature_id_to_features[dst_feature_id].aux["originalText"].replace("\t", " ").replace(
                "\n", " ")
            src_trigger = trigger_re.findall(src_original_text)[0]
            dst_trigger = trigger_re.findall(dst_original_text)[0]
            wfp.write(
                "{}\t{}\t{}\t{}\t{}\n".format(score, src_trigger, dst_trigger, src_original_text, dst_original_text))


if __name__ == "__main__":
    # sim_path = "/nfs/raid88/u10/users/hqiu_ad/repos/Hume/expts/covid_2000_pilot.081821/dumping/dumper_1/0/COVID-19/sim"
    # feature_list_path = "/nfs/raid88/u10/users/hqiu_ad/repos/Hume/expts/covid_2000_pilot.081821/dumping/dumper_1/features.list"
    # output_path = "/home/hqiu/tmp/a.log"
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sim_path", type=str, required=True)
    parser.add_argument("--feature_list_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    args = parser.parse_args()
    main(args.sim_path, args.feature_list_path, args.output_path)
