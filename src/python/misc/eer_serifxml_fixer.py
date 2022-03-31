import os
import serifxml3
import multiprocessing

def single_document_fixer(serifxml_path, output_serifxml_dir):
    serif_doc = serifxml3.Document(serifxml_path)
    for sentence in serif_doc.sentences:
        sentence_start_char_off = sentence.start_char
        sentence_start_edt = sentence.start_edt
        for token in sentence.token_sequence:
            token.start_char += sentence_start_char_off
            token.end_char += sentence_start_char_off
            token.start_edt += sentence_start_edt
            token.end_edt += sentence_start_edt
    serif_doc.save(os.path.join(output_serifxml_dir, "{}.xml".format(serif_doc.docid)))


def main():
    input_list = "/home/hqiu/ld100/Hume_pipeline_int/Hume/expts/gigaword_eer_json_add_head/serifxml.list"
    output_dir = "/nfs/raid88/u10/users/hqiu_ad/serifxml_corpus/gigaword_eer_training.v1/"
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(input_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_fixer, args=(i,output_dir,)))
            for idx, i in enumerate(workers):
                print("Waiting {}".format(idx))
                i.wait()
                buf = i.get()


if __name__ == "__main__":
    main()
