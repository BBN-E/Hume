import sys, os, codecs

from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention

sys.path.append(os.path.join(os.environ['SVN_PROJECT_ROOT'], 'SERIF', 'python'))
#sys.path.append(os.path.join('/nfs/raid84/u12/ychan/Active/Projects', 'SERIF', 'python'))
import serifxml

class GenericEventReader:
    def __init__(self):
        pass

    def read(self, kb, serifxml_dir, generic_event_filelist):
        print "Generic events"
        # read the filepaths of generic event info
        generic_event_files = dict()
        with open(generic_event_filelist, 'r') as f:
            for line in f:
                line = line.strip()
                docid = os.path.basename(line)
                generic_event_files[docid] = line
        
        serifxml_files = []
        for filename in os.listdir(serifxml_dir):
            docid = filename
            if filename.endswith(".serifxml"):
                docid = filename[0:-(len(".serifxml"))]
            else:
                docid = None
            if docid is None:
                print "Skipping file: " + filename
                continue
            serifxml_files.append((docid, os.path.join(serifxml_dir, filename),))

        files_length = len(serifxml_files)
        count = 0
        for docid, serifxml_file in serifxml_files:
            count += 1
            print "GenericEventReader producing events in: " + docid + " (" + str(count) + "/" + str(files_length) + ")"
            event_info_file = generic_event_files[docid]
            serif_doc = serifxml.Document(serifxml_file)

            event_info = []
            with codecs.open(event_info_file, 'r', encoding='utf-8') as f:
                for line in f:
                    tokens = line.strip().split()
                    classname = 'Class-' + tokens[1]
                    anchor_text = tokens[2]
                    start_char = int(tokens[3])
                    end_char = int(tokens[4])
                    event_info.append((classname, anchor_text, start_char, end_char))

            kb_document = kb.docid_to_kb_document[docid]
            sent_no = -1
            for s in serif_doc.sentences:
                sent_no += 1
                st = s.sentence_theories[0]
                if len(st.token_sequence) > 0:
                    st_start = st.token_sequence[0].start_char
                    st_end = st.token_sequence[-1].end_char
                    for (classname, anchor_text, start_char, end_char) in event_info:
                        if st_start <= start_char and end_char <= st_end:
                            snippet = self.get_snippet(serif_doc, st)
                            event_id = KBEvent.generate_id(docid)
                            event_mention_id = KBEventMention.generate_id(docid)
                            kb_event = KBEvent(event_id, classname)
                            kb_event_mention = KBEventMention(event_mention_id, kb_document, classname, anchor_text, start_char, end_char, snippet, kb_document.sentences[sent_no], "GENERIC")
                            kb_event.add_event_mention(kb_event_mention)
                            kb.add_event(kb_event)

    def get_snippet(self, serif_doc, sentence_theory):
        sentence_start = sentence_theory.token_sequence[0].start_char
        sentence_end = sentence_theory.token_sequence[-1].end_char

        return serif_doc.get_original_text_substring(sentence_start, sentence_end), sentence_start, sentence_end
