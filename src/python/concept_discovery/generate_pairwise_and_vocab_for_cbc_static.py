import argparse
import os,sys,shutil

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
sys.path.append(project_root)

from utils import MyStaticCacheDB

cbc_config = """
cbc.calculateRealCentroid: false
cbc.committeeSimilarityMethod: AVERAGE
cbc.committeeThreshold: 0.35
cbc.committees: {}/cbc.committees
cbc.finalClustering: {}/cbc.finalClustering
cbc.outputDirectory: {}/
cbc.residueThreshold: 0.25
cbc.topSimilarMembersThreshold: 10
interMemberSimilarity: {}/sim
lemma.noun: /home/hqiu/ld100/jserif/serif-events/src/main/resources/lemma.noun
lemma.verb: /home/hqiu/ld100/jserif/serif-events/src/main/resources/lemma.verb
targetMembers.list: {}/vocab
"""

def main(corpus_cache_path,output_path):
    static_cache = MyStaticCacheDB(corpus_cache_path)
    shutil.rmtree(output_path,ignore_errors=True)
    os.makedirs(output_path,exist_ok=True)
    vocab_path = os.path.join(output_path,'vocab')
    sim_path = os.path.join(output_path,'sim')
    cbc_param_path = os.path.join(output_path,'cbc.params')

    vocab_set = set()
    with open(sim_path,'w') as wfp:
        for en in static_cache.en_to_annoy_idx.keys():
            src_short_id = en.original_text
            dsts = static_cache.find(en)
            if len(dsts) > 0:
                vocab_set.add(src_short_id)
                for dst_en in dsts:
                    dst_short_id = dst_en['dst'].original_text
                    vocab_set.add(dst_short_id)
                    angular_score = dst_en['score']
                    cosine_similarity = 1 - angular_score * angular_score / 2
                    wfp.write("{} {} {:.3f}\n".format(src_short_id,dst_short_id,cosine_similarity))
    with open(vocab_path,'w') as wfp:
        for v in vocab_set:
            wfp.write("{}\n".format(v))
    with open(cbc_param_path,'w') as wfp:
        wfp.write(cbc_config.format(output_path,output_path,output_path,output_path,output_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus-cache', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()

    #corpus_cache_path = "/nfs/raid88/u10/users/hqiu_ad/wm_concept_discovery_wm_p3_bbn/static"
    #output_path = "/nfs/raid88/u10/users/hqiu_ad/wm_concept_discovery_wm_p3_bbn/cbc_prep_static"
    main(args.corpus_cache, args.outdir)
