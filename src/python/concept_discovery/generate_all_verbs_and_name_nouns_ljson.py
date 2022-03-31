import argparse
import json
import logging
import multiprocessing
import multiprocessing.managers
import os
import sys

import serifxml3

# from nltk.corpus import stopwords
from utils import read_saliency_list, build_doc_id_to_path_mapping

logger = logging.getLogger(__name__)
current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
sys.path.append(project_root)

# https://stackoverflow.com/a/50878600/6254393
# Backup original AutoProxy function
backup_autoproxy = multiprocessing.managers.AutoProxy

# Defining a new AutoProxy that handles unwanted key argument 'manager_owned'
def redefined_autoproxy(token, serializer, manager=None, authkey=None,
          exposed=None, incref=True, manager_owned=True):
    # Calling original AutoProxy without the unwanted key argument
    return backup_autoproxy(token, serializer, manager, authkey,
                     exposed, incref)

# Updating AutoProxy definition in multiprocessing.managers package
multiprocessing.managers.AutoProxy = redefined_autoproxy

def legal_token_sequence(tokens):
    for token in tokens:
        for c in token:
            if c.isalpha() is False:
                return False
    return True


def single_serifxml_handler(inbound_queue, output_queue, filter_words):
    """
    filter_words: might be None if we did not supply a filter_wordlist at command line

    The stop signel for mapper should be one None
    """

    try:
        while True:
            serif_path = inbound_queue.get()
            if serif_path is None:  # End of the code
                break
            else:
                logger.info("Handling {}".format(serif_path))
                serif_doc = serifxml3.Document(serif_path)
                ret_triggers = list()
                ret_sentence_infos = list()
                for sentence in serif_doc.sentences:
                    tokens = list()
                    token_spans = list()
                    token_to_token_idx = dict()
                    named_entity_mention_spans = list()
                    event_mention_spans = list()
                    for token_idx, token in enumerate(sentence.token_sequence or []):
                        token_to_token_idx[token] = token_idx
                        tokens.append(token.text)
                        token_spans.append({"key": token.start_edt, "value": token.end_edt})
                    for mention in sentence.mention_set or []:
                        if mention.mention_type.value.lower() == "name":
                            named_entity_mention_spans.append([token_to_token_idx[mention.tokens[0]],
                                                               token_to_token_idx[mention.tokens[-1]],
                                                               mention.entity_type + ""])
                    for event_mention in sentence.event_mention_set or []:
                        # anchor_start_token_idx = int(event_mention.semantic_phrase_start)
                        # anchor_end_token_idx = int(event_mention.semantic_phrase_end)
                        event_type = event_mention.event_type
                        # event_mention_spans.append([-1,-1,event_type])

                    ret_sentence_infos.append({
                        "docId": serif_doc.docid,
                        "docPath": serif_path,
                        "sentenceId": sentence.sent_no,
                        "sentenceInfo": {
                            "token": tokens,
                            "tokenSpan": token_spans,
                            "entities": named_entity_mention_spans,
                            "events": event_mention_spans
                        },
                        "fullSentenceText": " ".join(tokens)
                    })

                    # get POS-tag of each token in this sentence
                    pos_tags = []
                    if sentence.parse and sentence.parse.root:  # we will get the pos-tag from the parse tree
                        root = sentence.parse.root
                        """:type: serifxml.SynNode"""
                        for i, t in enumerate(root.terminals):
                            pos_tags.append(t.parent.tag)
                    elif sentence.pos_sequence is not None:
                        for pos in sentence.pos_sequence:
                            pos_tags.append(pos.tag)

                    added_token_idx = set()
                    existed = set()

                    for i, t in enumerate(sentence.token_sequence or []):
                        if len(filter_words) > 0 and t.text.lower() not in filter_words:
                            continue

                        if i >= len(pos_tags):
                            print('Skipping unigram {} because out of range of pos_tags, len(pos_tags)={}'.format(str(i),
                                                                                                                  str(len(
                                                                                                                      pos_tags))))
                            continue

                        if pos_tags[i].startswith('NN') or pos_tags[i].startswith('VB'):
                            pass
                        else:  # we only accept unigram nouns and verbs
                            continue

                        contains_non_alpha = True
                        for s in t.text:
                            if s.isalpha() is False:
                                contains_non_alpha = False
                                break
                        if contains_non_alpha is False:
                            continue
                        if True:
                            ret_triggers.append({
                                "docId": serif_doc.docid,
                                "sentenceId": sentence.sent_no,
                                "trigger": t.text.lower(),
                                "triggerPosTag": None,
                                "triggerSentenceTokenizedPosition": i,
                                "triggerSentenceTokenizedEndPosition": i,
                                "originalText": t.text
                            })
                            added_token_idx.add(i)
                            existed.add((i, i))

                    # Doing N-gram here
                    n_gram_triples = set()
                    for n_gram in {2}:
                        for cur in range(len(sentence.token_sequence or []) - n_gram + 1):
                            current_s = set(range(cur, cur + n_gram))
                            if len(current_s.intersection(added_token_idx)) > 0:
                                n_gram_triples.add((min(current_s), max(current_s)))

                    for new_trigger_start, new_trigger_end in n_gram_triples:
                        if new_trigger_end >= len(pos_tags):
                            print('Skipping n-gram ({},{}) because out of range of pos_tags, len(pos_tags)={}'.format(
                                str(new_trigger_start), str(new_trigger_end), str(len(pos_tags))))
                            continue

                        only_content_words = True
                        for tag in pos_tags[new_trigger_start: new_trigger_end + 1]:
                            if tag.startswith('JJ') or tag.startswith('NN') or tag.startswith('VB'):
                                pass
                            else:
                                only_content_words = False
                        if not only_content_words:
                            continue

                        token_text = [i.text for i in sentence.token_sequence[new_trigger_start:new_trigger_end + 1]]

                        trigger_text = '_'.join(i.lower() for i in token_text)
                        if len(filter_words) > 0 and trigger_text not in filter_words:
                            continue

                        # if legal_token_sequence(token_text) and len(set(k.lower() for k in token_text).intersection(stopwords.words('english'))) < 1:
                        if legal_token_sequence(token_text):
                            ret_triggers.append({
                                "docId": serif_doc.docid,
                                "sentenceId": sentence.sent_no,
                                "trigger": "_".join((i.lower() for i in token_text)),
                                "triggerPosTag": "NGRAM",
                                "triggerSentenceTokenizedPosition": new_trigger_start,
                                "triggerSentenceTokenizedEndPosition": new_trigger_end,
                                "originalText": "_".join(token_text)
                            })
                output_queue.put((ret_triggers, ret_sentence_infos))
    finally:
        # Signal the writer that mapper has finished
        output_queue.put(None)


def writter_process(output_queue, trigger_info_path, sentence_info_path, n_workers):
    """
    :param output_queue:
    :param trigger_info_path:
    :param sentence_info_path:
    :param n_workers:
    :return:
    The stopping signal for reducer should be n_workers None
    """
    stop_signals_received = 0
    with open(trigger_info_path, 'w') as trig_wfp, open(sentence_info_path, 'w') as sent_wfp:
        while True:
            elem = output_queue.get()
            if elem is None:
                stop_signals_received += 1
                if stop_signals_received >= n_workers:
                    break
            else:
                ret_triggers, ret_sentence_infos = elem
                for trig_info in ret_triggers:
                    trig_wfp.write("{}\n".format(json.dumps(trig_info, ensure_ascii=False)))
                for sent_info in ret_sentence_infos:
                    sent_wfp.write("{}\n".format(json.dumps(sent_info, ensure_ascii=False)))


def main(serif_list_path, output_dir, filter_wordlist_path):
    log_format = '[%(asctime)s] {P%(process)d:%(module)s:%(lineno)d} %(levelname)s - %(message)s'
    try:
        logging.basicConfig(level=logging.getLevelName(os.environ.get('LOGLEVEL', 'INFO').upper()),
                            format=log_format)
    except ValueError as e:
        logging.error(
            "Unparseable level {}, will use default {}.".format(os.environ.get('LOGLEVEL', 'INFO').upper(),
                                                                logging.root.level))
        logging.basicConfig(format=log_format)

    os.makedirs(output_dir, exist_ok=True)
    trigger_info_path = os.path.join(output_dir, "trigger.ljson")
    sentence_info_path = os.path.join(output_dir, "sentence.ljson")
    doc_id_to_doc_path = build_doc_id_to_path_mapping(serif_list_path)
    filter_words = set(read_saliency_list(filter_wordlist_path).keys())

    parallelization = multiprocessing.cpu_count()

    # All together, we need parallelization+1(writer)+1(current) processes
    manager = multiprocessing.Manager()
    inbound_queue = manager.Queue()
    output_queue = manager.Queue()


    # Step 1 put in jobs
    for serif_path in doc_id_to_doc_path.values():
        inbound_queue.put(serif_path)
    # Step 2 put in end job markings
    for _ in range(parallelization):
        inbound_queue.put(None)
    with manager.Pool(parallelization+1) as pool:
        workers = list()
        # Step 3 spawn mappers
        for _ in range(parallelization):
            proc = pool.apply_async(single_serifxml_handler, args=(inbound_queue, output_queue, filter_words,))
            workers.append(proc)
        # Step 4 spawn writer
        proc = pool.apply_async(writter_process,args=(output_queue, trigger_info_path, sentence_info_path, parallelization,))
        workers.append(proc)
        for worker in workers:
            worker.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--serif-list', required=True)
    parser.add_argument('--outdir', required=True)
    parser.add_argument('--filter-wordlist', required=False, default=None)
    args = parser.parse_args()

    main(args.serif_list, args.outdir, args.filter_wordlist)
