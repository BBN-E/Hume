import sys, os, codecs, json

if len(sys.argv) != 3:
    print "Usage: " + sys.argv[0] + " input-serifxml-dir output-json-dir"
    sys.exit(1)

sys.path.append(os.path.join('/nfs/mercury-04/u42/bmin/repositories/svn/source/Active/Projects/', 'SERIF', 'python'))
import serifxml

def get_snippet_remove_newlines(serif_doc, sentence_theory):
    sentence_start = sentence_theory.token_sequence[0].start_char
    sentence_end = sentence_theory.token_sequence[-1].end_char

    return serif_doc.get_original_text_substring(sentence_start, sentence_end).replace('\n', ' ')

input_dir, output_dir = sys.argv[1:]
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

for filename in os.listdir(input_dir):
    print("docid: " + filename)
    docid = filename
    if filename.endswith(".txt.xml"):
        docid = filename[0:-(len(".txt.xml"))]
    elif filename.endswith(".serifxml"):
        docid = filename[0:-(len(".serifxml"))]
    elif filename.endswith(".sgm.xml"):
        docid = filename[0:-(len(".sgm.xml"))]
    else:
        docid = None

    if docid is None:
        continue

    outfile = os.path.join(output_dir, docid + ".txt")
    o = codecs.open(outfile, 'w', encoding='utf8')
    
    serif_doc = serifxml.Document(os.path.join(input_dir, filename))

    for s in serif_doc.sentences:
        st = s.sentence_theories[0]
        # text = st.token_sequence
        snippet = get_snippet_remove_newlines(serif_doc, st)
        # print("sent: " + snippet)
        o.write(snippet+"\n")
        
    o.close()
    
