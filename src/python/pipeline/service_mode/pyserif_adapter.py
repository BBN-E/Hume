import os,sys,json,io,pickle
import tempfile
import serifxml3

import numpy as np
import requests



def handler(serif_doc_fp,aux=None):
    if aux is None:
        aux = dict()
    aux_buf = tempfile.TemporaryFile()
    pickle.dump(aux,aux_buf)
    aux_buf.seek(0)

    r = requests.post("http://afrl101:5000/v1/process_serifxml", files={
        "aux": aux_buf,
        "serifxml": serif_doc_fp
    })
    if r.status_code < 400:
        return r.content
    else:
        raise RuntimeError(r.json())

if __name__ == "__main__":
    serif_path = "/nfs/ld100/u10/hqiu/Hume_pipeline_int/Hume/expts/hume_test.080420.cx.v4/pyserif/pyserif_eer/25/output/ENG_NW_WM_cb208a4d26f71e8be51268b3790853c6_4.xml"
    npz_list_path = "/nfs/raid88/u10/users/hqiu/regtest/results/1596150001/hume_test.041420.cx.v1/expts/bert/bert_npz.list.modified"
    doc_id_to_npz = dict()
    with open(npz_list_path) as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i)
            docid = docid[:-len(".npz")]
            doc_id_to_npz[docid] = i
    with open(serif_path,'rb') as fp:
        npz_path = doc_id_to_npz[os.path.basename(serif_path)[:-len(".xml")]]
        bert_p = np.load(npz_path, allow_pickle=True)
        resolved = handler(fp,{"bert_npz":dict(bert_p.items())})
        print(resolved.decode("utf-8"))