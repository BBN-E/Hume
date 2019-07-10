import sys, os, codecs, re, json
from datetime import datetime

sys.path.append("/nfs/ld100/u10/bmin/repositories/svn/TextGroup/Active/Projects/SERIF/python/")
# sys.path.append(os.path.join('/nfs/raid84/u12/ychan/Active/Projects', 'SERIF', 'python'))
import serifxml

def read(serifxml_dir):
    serifxml_files = []
    for filename in os.listdir(serifxml_dir):
        docid = filename
        if filename.endswith(".serifxml"):
            docid = filename[0:-(len(".serifxml"))]
        elif filename.endswith(".xml"):
            docid = filename[0:-(len(".xml"))]
        else:
            docid = None
        if docid is None:
            print("Skipping file: " + filename)
            continue
        serifxml_files.append((docid, os.path.join(serifxml_dir, filename),))

    for docid, serifxml_file in serifxml_files:
        print ("==== " + serifxml_file)

        serif_doc = serifxml.Document(serifxml_file)

        for s in serif_doc.sentences:
            st = s.sentence_theories[0]

            for serif_em in st.event_mention_set:
                event_type=serif_em.event_type
                anchor_text=serif_em.anchor_node.text
                confidence = serif_em.score

                print(event_type)
                print(sanitize(anchor_text))
                print(sanitize(get_snippet(serif_doc, st)))

def get_snippet(serif_doc, sentence_theory):
    sentence_start = sentence_theory.token_sequence[0].start_char
    sentence_end = sentence_theory.token_sequence[-1].end_char

    return serif_doc.get_original_text_substring(sentence_start, sentence_end)

def sanitize(text):
    return text.replace("\n", " ").replace("\r", " ")

if __name__ == "__main__":
    serifxml_dir="/nfs/raid87/u11/users/hqiu/runjob/expts/Hume/causeex_scs.v1.051719.final.0425/event_event_relations/serifxml_output/"
    read(serifxml_dir)


