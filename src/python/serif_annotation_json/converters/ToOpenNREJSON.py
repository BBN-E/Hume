import json
import multiprocessing
import os
import shutil
import sys
import typing

import serifxml3

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.insert(0, project_root)

from converters import Converter
from util.read_serif_list import read_doc_list_from_file_list_or_file_list_folder

from models import read_serif_annotation_json, SerifAnnotationData, Span


def get_slot_id_string(event_mention: serifxml3.EventMention):
    if event_mention.pattern_id:
        return event_mention.pattern_id
    else:
        head = event_mention.anchor_node
        while head.head:
            head = head.head
        return head.tokens[0].text


def generate_opennre_json(doc_id: str, left_sentence_theory: serifxml3.SentenceTheory,
                          right_sentence_theory: serifxml3.SentenceTheory, left_event_mention: serifxml3.EventMention,
                          right_event_mention: serifxml3.EventMention, label: str):
    return {
        "sentence": " ".join(i.text for i in left_sentence_theory.token_sequence),
        "head": {
            "word": " ".join(i.text for i in left_event_mention.anchor_node.tokens),
            "id": "{}|{}".format(left_event_mention.event_type, get_slot_id_string(left_event_mention)),
        },
        "tail": {
            "word": " ".join(i.text for i in right_event_mention.anchor_node.tokens),
            "id": "{}|{}".format(right_event_mention.event_type, get_slot_id_string(right_event_mention))
        },
        "relation": label,

        "docid": doc_id,
        "arg1_span_list": [[left_event_mention.anchor_node.start_char, left_event_mention.anchor_node.end_char]],
        "arg1_text": " ".join(i.text for i in left_event_mention.anchor_node.tokens),
        "arg2_span_list": [[right_event_mention.anchor_node.start_char, right_event_mention.anchor_node.end_char]],
        "arg2_text": " ".join(i.text for i in right_event_mention.anchor_node.tokens),
        "connective_text": "",
        "relation_type": label,
        "semantic_class": label,
        "learnit_pattern": [],
        "sent_start_char_off": left_sentence_theory.token_sequence[0].start_char,
        "sent_end_char_off": left_sentence_theory.token_sequence[-1].end_char,
    }


def get_event_mention_from_span(span: Span, sent_off_to_sentence_theory: typing.Dict[
    typing.Tuple[int, int], serifxml3.SentenceTheory]):
    sentence_theory = sent_off_to_sentence_theory[(span.sent_start_char_off, span.sent_end_char_off)]
    for event_mention in sentence_theory.event_mention_set:
        if event_mention.anchor_node.start_token.start_char == span.start_char_off and event_mention.anchor_node.end_token.end_char == span.end_char_off:
            return event_mention
    return None


class OpenNREConverter(Converter):
    def __init__(self, doc_id_to_doc_path: dict, list_serif_annotation_data: typing.List[SerifAnnotationData],
                 output_folder: str):
        super().__init__(doc_id_to_doc_path, list_serif_annotation_data, output_folder)

    @staticmethod
    def single_document_worker(doc_path: str, serif_annotation_data: SerifAnnotationData):
        serif_doc = serifxml3.Document(doc_path)
        sent_off_to_sentence_theory = dict()
        for sent_idx, sentence in enumerate(serif_doc.sentences):
            for sentence_theory in sentence.sentence_theories:
                if len(sentence_theory.token_sequence) < 1:
                    continue
                sent_start, sent_end = sentence_theory.token_sequence[0].start_char, sentence_theory.token_sequence[
                    -1].end_char
                sent_off_to_sentence_theory[(sent_start, sent_end)] = sentence_theory
        opennre_json_list = list()
        word_set = set()
        for event_event_relation_mention in serif_annotation_data.event_event_relation_mentions:
            for annotation_entry in event_event_relation_mention.annotation_entries:
                for marking in annotation_entry.markings:
                    label = marking.label
                    left_sentence_theory = sent_off_to_sentence_theory[(
                        event_event_relation_mention.left_span.sent_start_char_off,
                        event_event_relation_mention.left_span.sent_end_char_off)]
                    right_sentence_theory = sent_off_to_sentence_theory[(
                        event_event_relation_mention.right_span.sent_start_char_off,
                        event_event_relation_mention.right_span.sent_end_char_off)]
                    left_event_mention = get_event_mention_from_span(event_event_relation_mention.left_span,
                                                                     sent_off_to_sentence_theory)
                    right_event_mention = get_event_mention_from_span(event_event_relation_mention.right_span,
                                                                      sent_off_to_sentence_theory)
                    assert left_event_mention is not None
                    assert right_event_mention is not None

                    opennre_json = generate_opennre_json(serif_doc.docid, left_sentence_theory, right_sentence_theory,
                                                         left_event_mention, right_event_mention, label)
                    opennre_json_list.append(opennre_json)
                    for token in left_sentence_theory.token_sequence:
                        word_set.add(token.text)
                    for token in right_sentence_theory.token_sequence:
                        word_set.add(token.text)
        return {'opennre_json_list': opennre_json_list, 'word_set': word_set}

    def convert(self):
        shutil.rmtree(self.output_folder, ignore_errors=True)
        os.makedirs(self.output_folder, exist_ok=True)

        manager = multiprocessing.Manager()
        worker_list = list()

        word_set = set()
        opennre_json_list = list()
        with manager.Pool() as pool:
            for doc_annotation in self.list_serif_annotation_data:
                worker_list.append(pool.apply_async(OpenNREConverter.single_document_worker, args=(
                    self.doc_id_to_doc_path[doc_annotation.doc_id], doc_annotation)))
            for idx, i in enumerate(worker_list):
                i.wait()
                en = i.get()
                word_set.update(en['word_set'])
                opennre_json_list.extend(en['opennre_json_list'])

        with open(os.path.join(self.output_folder, 'data.json'), 'w') as fp:
            json.dump(opennre_json_list, fp, ensure_ascii=False, indent=4, sort_keys=True)
        with open(os.path.join(self.output_folder, 'wordlist.txt'), 'w') as fp:
            for word in word_set:
                fp.write("{}\n".format(word))


def main():
    test_json = "/home/hqiu/ld100/learnit/expts/causeex_m17_test.v4/serialization_out/relation_cause_effect/ENG_NW_NODATE_M15a_9167.json"
    serif_list = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/causeex_m17_5files_test.v1/grounded_serifxml.list"
    output_folder = "/home/hqiu/tmp/opennre_serialization_test"
    doc_id_to_serif_path_map = read_doc_list_from_file_list_or_file_list_folder(serif_list)
    serif_annotation = read_serif_annotation_json(test_json)
    converter = OpenNREConverter(doc_id_to_serif_path_map, [serif_annotation], output_folder)
    converter.convert()


if __name__ == "__main__":
    main()
