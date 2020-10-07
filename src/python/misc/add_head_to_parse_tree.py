import os
import serifxml3

def main(serif_list_path,output_dir):

    serif_list = list()
    with open(serif_list_path) as fp:
        for i in fp:
            i = i.strip()
            serif_list.append(i)
    for p in serif_list:
        serif_doc = serifxml3.Document(p)
        for sentence in serif_doc.sentences:
            if sentence.sentence_theory.parse is not None:
                sentence.sentence_theory.parse.add_heads()
        serif_doc.save(os.path.join(output_dir,"{}.xml".format(serif_doc.docid)))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_list")
    parser.add_argument("--output_dir")
    args = parser.parse_args()
    main(args.input_list,args.output_dir)