import argparse
import os
import shutil

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
hume_repo_root = os.path.realpath(os.path.join(project_root, os.path.pardir, os.path.pardir, os.path.pardir))

from utils import read_saliency_list, read_event_mention_instance_identifier_list

cbc_config = """
cbc.calculateRealCentroid: false
cbc.committeeSimilarityMethod: AVERAGE
cbc.committeeThreshold: 0.35
cbc.committees: {}/cbc.committees
cbc.finalClustering: {}/cbc.finalClustering
cbc.outputDirectory: {}/
cbc.residueThreshold: 0.25
cbc.topSimilarMembersThreshold: 10
interMemberSimilarity: {}
targetMembers.list: {}
lemma.noun: {}/resource/concept_discovery/lemma.noun
lemma.verb: {}/resource/concept_discovery/lemma.verb
"""


def main(vocab_path, similarity_path, saliency_path, output_path):
    shutil.rmtree(output_path, ignore_errors=True)
    os.makedirs(output_path, exist_ok=True)
    cbc_param_path = os.path.join(output_path, 'cbc.params')
    new_vocab_path = os.path.join(output_path, 'vocab')
    new_sim_path = os.path.join(output_path, "sim")

    filter_list = set(read_saliency_list(saliency_path).keys())

    # Copy similarity file directly
    shutil.copy(similarity_path, new_sim_path)

    # Copy vocab list directly or filter as needed
    if len(filter_list) == 0:
        shutil.copy(vocab_path, new_vocab_path)
    else:
        filtered_vocab_set = set()
        ems = read_event_mention_instance_identifier_list(vocab_path)
        for em in ems:
            if em.original_text.lower() in filter_list:
                filtered_vocab_set.add(em)

        with open(new_vocab_path, 'w') as wfp:
            for v in filtered_vocab_set:
                wfp.write("{}\n".format(v.to_short_id_str()))

    # Write CBC param file
    with open(cbc_param_path, 'w') as wfp:
        wfp.write(cbc_config.format(output_path, output_path, output_path, new_sim_path, new_vocab_path,hume_repo_root,hume_repo_root))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--vocab', required=True)
    parser.add_argument('--similarities', required=True)
    parser.add_argument('--salient-terms', required=False, default=None)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()

    main(args.vocab, args.similarities, args.salient_terms, args.outdir)
