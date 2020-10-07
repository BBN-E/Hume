import os,sys


def write_with_bert_embeddings(file_handle, serif, bert):
    file_handle.write("SERIF:{} EMBEDDING:{}\n".format(serif, bert))


def write_without_bert_embeddings(file_handle, serif, bert):
    file_handle.write("SERIF:{}\n".format(serif))


def main(serif_list_file,bert_list_file,output_list_file):

    doc_id_to_serif_path = dict()
    doc_id_to_npz_path = dict()

    with open(serif_list_file) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id.replace(".sgm","").replace(".xml","").replace(".serifxml","")
            doc_id_to_serif_path[doc_id] = i

    if bert_list_file == "NONE":
        write_line = write_without_bert_embeddings
    else:
        write_line = write_with_bert_embeddings
        with open(bert_list_file) as fp:
            for i in fp:
                i = i.strip()
                doc_id = os.path.basename(i)
                doc_id = doc_id.replace(".npz","")
                doc_id_to_npz_path[doc_id] = i

    with open(output_list_file,'w') as wfp:
        for doc_id in doc_id_to_serif_path.keys():
            write_line(wfp,
                       doc_id_to_serif_path[doc_id],
                       doc_id_to_npz_path.get(doc_id))


if __name__ == "__main__":
    main(sys.argv[1],sys.argv[2],sys.argv[3])
