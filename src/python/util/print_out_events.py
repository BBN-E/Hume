import sys, os, codecs, re, json
from datetime import datetime

sys.path.append('/nfs/ld100/u10/bmin/repo_clean_for_exp_causeex/Hume/src/python/knowledge_base/')
sys.path.append(os.path.join(os.environ['SVN_PROJECT_ROOT'], 'SERIF', 'python'))

from elements.kb_entity import KBEntity
from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention
from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from elements.kb_document import KBDocument
from elements.kb_sentence import KBSentence
from elements.kb_group import KBEntityGroup, KBEventGroup, KBRelationGroup
# sys.path.append(os.path.join('/nfs/raid84/u12/ychan/Active/Projects', 'SERIF', 'python'))
import serifxml


def get_snippet(serif_doc, sentence_theory):
    sentence_start = sentence_theory.token_sequence[0].start_char
    sentence_end = sentence_theory.token_sequence[-1].end_char

    return serif_doc.get_original_text_substring(sentence_start, sentence_end)


#serifxml_dir = "/nfs/raid87/u12/hqiu/runjob/expts/Hume/causeex_scs_sampled_100.v2/event_consolidation_serifxml_out/"
serifxml_dir = sys.argv[1]

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

files_length = len(serifxml_files)
count = 0

actor_id_to_entity_group = dict()

for docid, serifxml_file in serifxml_files:
    mention_map = dict()  # maps serif mention to KBMention
    event_map = dict()  # maps serif event mention (or icews event mention) to (KBEvent, KBEventMention, SentenceTheory)

    count += 1
    print "SerifXMLReader producing KB objects in: " + docid + " (" + str(count) + "/" + str(files_length) + ")"

    serif_doc = serifxml.Document(serifxml_file)

    for serif_event in serif_doc.event_set:
        event_type = serif_event.event_type

        print ("=== Event: " + event_type) # + "\ttense: " + serif_event.tense.value + " genericity: " + serif_event.genericity.value + " modality: " + serif_event.modality.value + " polarity: " + serif_event.polarity.value)

        for argument in serif_event.arguments:
            if argument.entity is not None:
                canonical_name = "NA"
                if argument.entity.canonical_name is not None:
                    canonical_name = argument.entity.canonical_name
                print ("    -" + str(argument.role) + ": " + argument.entity.entity_type + "\t" + canonical_name.encode('ascii', 'ignore'))
            elif argument.value is not None:
                print ("    -" + str(argument.role) + ": " + argument.value.value_type + "\t" + argument.value.value_mention.text.encode('ascii', 'ignore'))

        idx=0
        for serif_em in serif_event.event_mentions:
            s = serif_doc.sentences[serif_em.anchor_node.sent_no]
            st = s.sentence_theories[0]
            snippet = get_snippet(serif_doc, st)
            em_type = serif_em.event_type
            em_anchor_text = serif_em.anchor_node.text

            idx=idx+1
            print ("  " + str(idx) + " Event mention: " + em_type + "\t" + em_anchor_text.encode('ascii', 'ignore') + "\t" + snippet.replace("\n", " ").replace("\r", " ").encode('ascii', 'ignore'))
            # "\ttense: " + serif_em.tense.value + " genericity: " + serif_em.genericity.value + " modality: " + serif_em.modality.value + " polarity: " + serif_em.polarity.value)
            # print ("    " )

            for argument in serif_em.arguments:
                mention_or_value_mention = None
                if argument.mention is not None:
                    m = argument.mention
                    print ("      -" + str(argument.role) + ": " + m.entity_type + "\t" + m.text.encode('ascii', 'ignore'))

                if argument.value_mention is not None:
                    vm = argument.value_mention
                    print ("      -" + str(argument.role) + ": " + vm.value_type + "\t" + vm.text.encode('ascii', 'ignore'))


def get_normalized_time(self, serif_doc, value_mention):
    for value in serif_doc.value_set:
        if value.value_mention == value_mention:
            return value.timex_val
    return None
