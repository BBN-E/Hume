import argparse
import codecs
import json
import os
import logging
import numpy as np
import collections
import gzip

DocSentId = collections.namedtuple("DocSentId",["doc_id","sent_id"])
FilePathLineIdx = collections.namedtuple("FilePathLineIdx",["file_path","line_idx"])

logger = logging.getLogger(__name__)

def create_docid_to_paths(file_path,enable_suffixs):
    doc_id_to_path = dict()
    with open(file_path) as fp:
        for i in fp:
            i = i.strip()
            for suffix in enable_suffixs:
                if i.endswith(suffix):
                    doc_id = os.path.basename(i)
                    doc_id = doc_id[:-len(suffix)]
                    doc_id_to_path[doc_id] = i
    return doc_id_to_path


def read_embeddings(input_dir):
    doc_sent_id_to_emb = dict()
    for f in os.listdir(input_dir):
        if f.endswith("_sent_info.info"):
            with gzip.open(os.path.join(input_dir,f),'rt') as fp:
                for i in fp:
                    j = json.loads(i)
                    doc_id = j['doc_id']
                    sent_id = j['sent_id']
                    data = j['bert_emb']
                    doc_sent_id = DocSentId(doc_id,sent_id)
                    sentence_vectors = []
                    for token_data in data['features']:
                        values = []
                        for i in range(len(token_data['layers'])):
                            values.extend(token_data['layers'][i]['values'])
                        sentence_vectors.append(np.asarray(values, dtype=np.float32))
                    doc_sent_id_to_emb[doc_sent_id] = np.asarray(sentence_vectors)

    return doc_sent_id_to_emb


def read_token_map(filepath):
    """
    filepath:   file containing mapping of original tokens to bert tokens
    """
    ret = []

    with gzip.open(filepath, 'rt') as f:
        for line in f:
            values = [int(v) for v in line.strip().split()]
            ret.append(np.asarray(values))
    return np.asarray(ret)

def main(batch_dir,token_map_list,outdir):
    os.makedirs(outdir,exist_ok=True)
    doc_id_to_token_map = create_docid_to_paths(token_map_list, {".token_map"})

    doc_sent_id_to_emb = read_embeddings(batch_dir)

    doc_id_to_sent_emb_pair = dict()
    for doc_sent_id,emb in doc_sent_id_to_emb.items():
        doc_id_to_sent_emb_pair.setdefault(doc_sent_id.doc_id,dict())[doc_sent_id.sent_id] = emb

    for doc_id in doc_id_to_sent_emb_pair.keys():
        number_of_sentence = max(doc_id_to_sent_emb_pair[doc_id].keys()) + 1
        token_map = read_token_map(doc_id_to_token_map[doc_id])
        embs = list()
        for idx in range(number_of_sentence):
            emb = doc_id_to_sent_emb_pair[doc_id].get(idx,np.asarray([], dtype=np.float32))
            embs.append(emb)
        npz_file = os.path.join(outdir, doc_id + '.npz')
        assert len(embs) == len(token_map)
        np.savez_compressed(
            npz_file, embeddings=np.asarray(embs), token_map=token_map)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch_dir', required=True)
    parser.add_argument('--token_map_list', required=True)
    parser.add_argument('--outdir', required=True)
    args = parser.parse_args()
    main(args.batch_dir, args.token_map_list, args.outdir)