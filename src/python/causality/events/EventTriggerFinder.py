import codecs
import os
import sys
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
import argparse

import nltk
from nltk.corpus import wordnet as wn

from util.python.causality.events.OntoNotesSenseInventory import OntoNotesSenseInventory
from util.python.causality.events.FrameNetUtil import FrameNetUtil
from util.python.causality.events.TriggerClassifier import TriggerClassifier

# change these two directories
nltk.data.path.append('/nfs/mercury-04/u42/bmin/applications/nltk_data/')
sys.path.append(os.path.join('/nfs/mercury-04/u42/bmin/repositories/svn/source/Active/Projects/', 'SERIF', 'python'))

import serifxml


class EventTriggerFinder:

    def __init__(self, use_framenet=False):
        print('Initializing EventTriggerFinder.')
        self.use_framenet = use_framenet
        if self.use_framenet:
            self.framenet_util = FrameNetUtil()
        self.ontoNotesSenseInventory = OntoNotesSenseInventory()
        self.triggerClassifier = TriggerClassifier(use_positive=False)

    def get_tokenized_text(self, sentence_theory):
        tokens = []
        offsets = []
        for token in sentence_theory.token_sequence:
            tokens.append(token.text)
            offsets.append((token.start_char, token.end_char))
        return (tokens, offsets)


    def run_ims(self, in_file):
        out_file = NamedTemporaryFile('w', delete=False)
        out_file.close()

        ims_dir = '/nfs/ld100/u10/bmin/repositories/IMS/ims_0.9.2/'

        cmd = [ims_dir + 'testPlain.bash']
        cmd.append(ims_dir + 'models')
        cmd.append(in_file)
        cmd.append(out_file.name)
        cmd.append('/nfs/ld100/u10/bmin/repositories/IMS/WordNet-2.1/dict/index.sense')
        cmd.append('1 1 0')  # is sentence splitted and tokenised

        print(' '.join(cmd))
        this_ims = Popen(' '.join(cmd), stdin=None, stdout=None, stderr=PIPE, shell=True, cwd=ims_dir)
        return_code = this_ims.wait()
        sentences_tagged = []
        if return_code != 0:
            print>> sys.stderr, 'Error with IMS at', ims_dir
            print>> sys.stderr, this_ims.stderr.read()
        else:
            f_in = open(out_file.name, 'r')
            for line in f_in:
                sentences_tagged.append(line.decode('utf-8').strip())
            f_in.close()

        return out_file.name, sentences_tagged

    def extractSentences(self, serifXmlPath):
        self.sentenceFile = NamedTemporaryFile('w', delete = False)
        self.sentenceFile.close()

        o = codecs.open(self.sentenceFile.name, 'w', encoding='utf8')

        serif_doc = serifxml.Document(serifXmlPath)

        doc_tokens = []
        doc_offsets = []
        for s in serif_doc.sentences:
            st = s.sentence_theories[0]
            (tokens, offsets) = self.get_tokenized_text(st)
            doc_tokens.append(tokens)
            doc_offsets.append(offsets)
            o.write(' '.join(tokens) + "\n")

        o.close()

        #return self.sentenceFile.name
        return (self.sentenceFile.name, doc_tokens, doc_offsets)


    def findTriggers(self, serifXmlPath):
        self.serifXmlPath = serifXmlPath
        (self.sentenceFile, doc_tokens, doc_offsets) = self.extractSentences(serifXmlPath)
        # doc_tokens: list of list[str]
        # doc_offsets: list of list[(start_char, end_char)]

        # IMS
        self.out_file, self.sentences_tagged = self.run_ims(self.sentenceFile)
        assert len(self.sentences_tagged) == len(doc_offsets)

        meta_lines = []
        list_sentence_triggers = []
        for sent_index, sentence_tagged in enumerate(self.sentences_tagged):
            sentence_triggers = []
            tokens = []

            words_and_synsets = self.extract_primary_word_sense(sentence_tagged)
            assert len(words_and_synsets) == len(doc_offsets[sent_index])
   
            for token_index, word_and_synset in enumerate(words_and_synsets):
                str_synset = str(word_and_synset[1])
                isTrigger = False
                if '.n.' in str_synset or '.v.' in str_synset: # only noun and verb can be event triggers
                    if self.ontoNotesSenseInventory.hasOntoNotesSenseForWnSense(str_synset):
                        isTrigger = True
                        offset = doc_offsets[sent_index][token_index]
                        meta_lines.append(doc_tokens[sent_index][token_index] + ' ' + str(offset[0]) + ' ' +  str(offset[1]))

                sentence_triggers.append((word_and_synset[0], isTrigger))
                tokens.append(word_and_synset[0])

            if self.use_framenet:
                # FrameNet
                try :
                    token_and_pos_and_isTriggers = self.framenet_util.getEventTriggersWithPosAndIndex(tokens)
                except:
                    print("Invalid POS for tokens: " + str(tokens))

            # merge in FrameNet trigers
            merged_sentence_triggers = []
            for index in range(0, len(sentence_triggers)):
                # filter by the trigger classifier (currently a list)
                is_valid_by_classifier = self.triggerClassifier.isValidEventTrigger(sentence_triggers[index][0])

                if self.use_framenet:
                    merged_sentence_triggers.append((sentence_triggers[index][0],
                                                     is_valid_by_classifier and (sentence_triggers[index][1] or token_and_pos_and_isTriggers[index][2])))
                else:
                    merged_sentence_triggers.append((sentence_triggers[index][0],
                                                     is_valid_by_classifier and sentence_triggers[index][1]))

            list_sentence_triggers.append(merged_sentence_triggers)

        return (list_sentence_triggers, meta_lines)

    def extract_lemma_and_top_sense(self, string_xml):
        # Example: <x length="1 guard%1:06:00::|0.24333712378769684 guard%1:18:01::|0.2534142359403768 guard%1:18:03::|0.26029268291162844 guard%1:07:00::|0.2429559573602979">Guard</x>

        index_end_senses = string_xml.rfind("\"")
        token = string_xml[index_end_senses+2:string_xml.rfind("</x")]

        string_xml = string_xml[0:index_end_senses]
        items = string_xml.split(" ")

        best_sense_key = "NA"
        best_prob = 0
        for item in items[2:]:
            sense_key = item[0:item.find("|")]
            prob = float(item[item.find("|")+1:])
            if prob > best_prob:
                best_sense_key = sense_key
                best_prob = prob

        def get_synset_from_sense_key(sense_key):
            try:
                lemma = wn.lemma_from_key(sense_key)
            except:
                # print("no synset found for: " + sense_key)
                return "NA"
            return str(lemma.synset())

        wn_sysset = get_synset_from_sense_key(best_sense_key)

        return (token, wn_sysset, best_prob)


    def extract_primary_word_sense(self, sentence_tagged):
        token_and_tags = []

        # print("=============")

        while sentence_tagged != '':
            # print (sentence_tagged)
            index_x_left = sentence_tagged.find("<x")
            if index_x_left == -1: # no tag
                for token in sentence_tagged.strip().split(' '):
                    if token != '':
                        token_and_tags.append((token, "NA"))
                break
            else:
                text_seq_before_x_tag = sentence_tagged[0:index_x_left]
                sentence_tagged = sentence_tagged[index_x_left:]
                index_x_right = sentence_tagged.strip().find("/x>")
                string_xml = sentence_tagged[0:index_x_right+4]
                sentence_tagged = sentence_tagged[index_x_right+4:].strip()

                # tokens to the left of "<x"
                for token in text_seq_before_x_tag.strip().split(' '):
                    if token != '':
                        token_and_tags.append((token, "NA"))

                (token, wn_synset, best_prob) = self.extract_lemma_and_top_sense(string_xml)
                token_and_tags.append((token, wn_synset))

        return token_and_tags

    def write_text_and_ann(self, list_sentence_triggers):
        file_text = self.serifXmlPath + ".txt"
        file_ann = self.serifXmlPath + ".ann"

        out_text = codecs.open(file_text, 'w', encoding='utf8')
        out_ann = codecs.open(file_ann, 'w', encoding='utf8')

        eid=1
        doc_text = ''
        for sentence_triggers in list_sentence_triggers:
            for token_trigger in sentence_triggers:
                token = token_trigger[0]
                is_trigger = token_trigger[1]

                char_start = len(doc_text)
                doc_text += token + ' '
                char_end = len(doc_text)-1

                if is_trigger:
                    eid+=1
                    trigger_id = "T" + str(eid)
                    event_id = "E" + str(eid)
                    out_ann.write(trigger_id + "\t" + "Event " + str(char_start) + " " + str(char_end) + "\t" + token + '\n')
                    out_ann.write(event_id + "\t" + "Event:" + trigger_id + '\n')

            doc_text += '\n'

        out_text.write(doc_text)

        out_text.close()
        out_ann.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--serifxml')		# the SerifXML on which you want to find generic triggers
    parser.add_argument('--offset_output')	# as we find triggers, we write them (text, char-offsets) to this file
    parser.add_argument('--print_trigger', action='store_true')
    args = parser.parse_args()

    eventTriggerFinder = EventTriggerFinder()
    #serifxmlPath = '/nfs/mercury-04/u10/resources/ACE2004/data.eng/NYT_ENG_20030403.0008.sgm.xml'
    serifxmlPath = args.serifxml

    (list_sentence_triggers, meta_lines) = eventTriggerFinder.findTriggers(serifxmlPath)

    eventTriggerFinder.write_text_and_ann(list_sentence_triggers)

    with open(args.offset_output, 'w') as f:
        f.write('\n'.join(meta_lines) + '\n')

    if args.print_trigger:
        for sentence_triggers in list_sentence_triggers:
            print("=======================")
            tokens_marked = []
            for token_trigger in sentence_triggers:
                if token_trigger[1]:
                    tokens_marked.append("**" + token_trigger[0] + "**")
                else:
                    tokens_marked.append(token_trigger[0])
            print(' '.join(tokens_marked))

