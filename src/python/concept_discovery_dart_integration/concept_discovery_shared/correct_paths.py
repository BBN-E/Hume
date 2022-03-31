import os,sys,re

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.append(project_root)
hume_repo_root = os.path.realpath(os.path.join(project_root, os.path.pardir, os.path.pardir, os.path.pardir))


def correct_paths_in_sequence(repo_mirror_path, sequence_path):
    resolved_strs = list()
    replaced_cnt = 0
    with open(sequence_path) as fp:
        for i in fp:
            if "#BBN_MAGIC1" in i:
                i = "$hume_repo_root = \"{}\";\n".format(hume_repo_root)
                replaced_cnt += 1
            if "#BBN_MAGIC2" in i:
                i = "$textopen_root = \"{}\";\n".format(os.path.join(repo_mirror_path, 'text-open'))
                replaced_cnt += 1
            if "#BBN_MAGIC3" in i:
                i = "unshift(@INC, \"{}/lib\");\n".format(os.path.join(repo_mirror_path, 'runjobs'))
                replaced_cnt += 1
            resolved_strs.append(i)
    if replaced_cnt != 3:
        print("Input error")
    with open(sequence_path, 'w') as wfp:
        for i in resolved_strs:
            wfp.write(i)


def main(repo_mirror_path):
    # Correct Hume repo path
    original_sequence_path = os.path.join(hume_repo_root, "sequences/cbc_clustering.pl")
    ontology_sequence_path = os.path.join(hume_repo_root, "sequences/cbc_cluster_to_ontology_mapping.pl")
    correct_paths_in_sequence(repo_mirror_path, original_sequence_path)
    correct_paths_in_sequence(repo_mirror_path, ontology_sequence_path)


if __name__ == "__main__":
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--repo_mirror_path', required=True)
    args = arg_parser.parse_args()
    main(args.repo_mirror_path)