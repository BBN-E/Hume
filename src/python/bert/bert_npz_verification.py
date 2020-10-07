import os,sys,json,gzip

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def create_doc_id_to_path(file_list, extension):
    docid_to_path = dict()
    with open(file_list) as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i).replace(extension, "")
            docid_to_path[docid] = i
    return docid_to_path

def main():
    left_npz_path = "/nfs/raid80/u14/users/rbock/git/aida.for_carl/experiments/doc_processing/expts/LDC2020E11.20200916/bert/batch_104/old.list"
    # left_npz_path = "/home/hqiu/ld100/better/experiments/extract_mbert/expts/bert/embed.list"
    right_npz_path = "/nfs/ld100/u10/hqiu/Hume_pipeline_int/Hume/expts/bert_test.091820.after.v6/bert/bert_npz.list"

    doc_id_to_left_npz_d = create_doc_id_to_path(left_npz_path,".npz")
    doc_id_to_right_npz_d = create_doc_id_to_path(right_npz_path,".npz")

    print("Left has extra: {}".format(set(doc_id_to_left_npz_d.keys()).difference(set(doc_id_to_right_npz_d.keys()))))
    print("Right has extra: {}".format(set(doc_id_to_right_npz_d.keys()).difference(set(doc_id_to_left_npz_d.keys()))))

    for doc_id in set(doc_id_to_left_npz_d.keys()).intersection(set(doc_id_to_right_npz_d.keys())):
        with np.load(doc_id_to_left_npz_d[doc_id],
                     allow_pickle=True) as fp2:
            left_embeddings = fp2['embeddings']
            left_token_map = fp2['token_map']

        with np.load(doc_id_to_right_npz_d[doc_id],
                     allow_pickle=True) as fp2:
            right_embeddings = fp2['embeddings']
            right_token_map = fp2['token_map']

        try:
            assert len(left_embeddings) == len(left_token_map)
        except:
            continue
        assert len(right_embeddings) == len(right_token_map)

        if len(left_embeddings) != len(right_embeddings):
            print("doc: {} has left: {}, right: {}".format(doc_id,len(left_embeddings),len(right_embeddings)))
            continue
        test_pass = True
        for sent_id in range(len(left_embeddings)):
            if len(left_embeddings[sent_id]) != len(right_embeddings[sent_id]):
                print("doc: {} sent: {} error".format(doc_id, sent_id))
                test_pass = False
                continue
            for token_id in range(len(left_embeddings[sent_id])):

                if cosine_similarity(left_embeddings[sent_id][token_id].reshape(1, -1),right_embeddings[sent_id][token_id].reshape(1, -1)) < 0.95:
                    print("doc: {} sent: {} token: {} error".format(doc_id,sent_id,token_id))
                    test_pass = False
            if test_pass is True:
                print("doc: {} sent: {} passed".format(doc_id, sent_id))



if __name__ == "__main__":
    main()





