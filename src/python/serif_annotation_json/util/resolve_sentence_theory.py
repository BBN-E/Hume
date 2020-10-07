import multiprocessing
import typing

import serifxml3


def single_document_worker(doc_path: str, sent_offsets: typing.Set[typing.Tuple[int, int]]):
    serif_doc = serifxml3.Document(doc_path)
    sent_off_to_sentence_theory = dict()
    for sent_idx, sentence in enumerate(serif_doc.sentences):
        for sentence_theory in sentence.sentence_theories:
            if len(sentence_theory.token_sequence) < 1:
                continue
            sent_start, sent_end = sentence_theory.token_sequence[0].start_char, sentence_theory.token_sequence[
                -1].end_char
            sent_off_to_sentence_theory[(sent_start, sent_end)] = sentence_theory
    ret_offset_to_sentence_theory = dict()
    for sent_offset in sent_offsets:
        ret_offset_to_sentence_theory[sent_offset] = sent_off_to_sentence_theory[sent_offset]
    return {'doc_id': serif_doc.docid, 'sent_span_to_sent_theory': ret_offset_to_sentence_theory}


def get_relevant_sentence_theory(doc_id_to_doc_path: dict,
                                 doc_id_to_sent_offsets: typing.Dict[str, typing.Set[typing.Tuple[int, int]]]):
    manager = multiprocessing.Manager()
    job_list = list()
    doc_id_to_sent_span_to_sent_theory = dict()
    with manager.Pool() as pool:
        for doc_id, sent_spans in doc_id_to_sent_offsets.items():
            job_list.append(pool.apply_async(single_document_worker(doc_id_to_doc_path[doc_id], sent_spans)))

        for idx, i in enumerate(job_list):
            i.wait()
            en = i.get()
            doc_id_to_sent_span_to_sent_theory[en['doc_id']] = en['sent_span_to_sent_theory']

    return doc_id_to_sent_span_to_sent_theory
