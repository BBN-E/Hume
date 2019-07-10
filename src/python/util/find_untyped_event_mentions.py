import sys, os, codecs, re, json
from datetime import datetime

sys.path.append("/nfs/ld100/u10/bmin/repositories/svn/TextGroup/Active/Projects/SERIF/python/")
# sys.path.append(os.path.join('/nfs/raid84/u12/ychan/Active/Projects', 'SERIF', 'python'))
import serifxml

def read(serifxml_dir):
    print "Reading from: " + serifxml_dir
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
            print "Skipping file: " + filename
            continue
        serifxml_files.append((docid, os.path.join(serifxml_dir, filename),))

    for docid, serifxml_file in serifxml_files:
        print ("Reading " + serifxml_file)

        serif_doc = serifxml.Document(serifxml_file)

        for s in serif_doc.sentences:
            st = s.sentence_theories[0]

            for serif_em in st.event_mention_set:
                event_type=serif_em.event_type
                anchor_text=serif_em.anchor_node.text
                confidence = serif_em.score

                #if "." not in event_type:
                print "em\t" + event_type + "\t" + anchor_text + "\t" + str(confidence)


if __name__ == "__main__":
    serifxml_dir="/nfs/ld100/u10/bmin/repo_clean_for_exp_causeex/Hume/expts/causeex_scs.v1/event_consolidation_serifxml_out"
    read(serifxml_dir)


