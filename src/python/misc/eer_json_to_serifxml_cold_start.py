import os,ast,json,logging,multiprocessing,re,datetime
logger = logging.getLogger(__name__)

import serifxml3
from serif.model.impl.sentence_splitter.newline_sentence_splitter import NewlineSentenceSplitter
from serif.model.impl.parser.benepar_parser import BeneparParser
from serif.model.impl.mention.noun_phrase_mention_model import NounPhraseMentionModel


def find_lowest_common_ancestor(syn_node_1, syn_node_2):
    # https://www.hrwhisper.me/algorithm-lowest-common-ancestor-of-a-binary-tree
    assert isinstance(syn_node_1, serifxml3.SynNode)
    assert isinstance(syn_node_2, serifxml3.SynNode)
    visited = set()
    while syn_node_1 is not None and syn_node_2 is not None:
        if syn_node_1 is not None:
            if syn_node_1 in visited:
                return syn_node_1
            visited.add(syn_node_1)
            syn_node_1 = syn_node_1.parent
        if syn_node_2 is not None:
            if syn_node_2 in visited:
                return syn_node_2
            visited.add(syn_node_2)
            syn_node_2 = syn_node_2.parent
    return None


def list_spliter_by_batch_size(my_list, batch_size):
    return [my_list[i * batch_size:(i + 1) * batch_size] for i in range((len(my_list) + batch_size - 1) // batch_size)]


def list_spliter_by_num_of_batches(my_list, num_of_batches):
    k, m = divmod(len(my_list), num_of_batches)
    return list(my_list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(num_of_batches))

def txt_to_serif_doc(s,docid):
    logger.info("Creating a SERIF XML document")
    new_doc = serifxml3.Document.construct(docid)
    new_doc.language = "English"
    new_doc.construct_original_text(s, 0, len(s) - 1)
    new_doc.construct_regions(0, len(s) - 1)
    new_doc.construct_segments()
    new_doc.construct_metadata(0, len(s) - 1, "RegionSpan", "TEXT")
    return new_doc



def my_tokenizer(serif_doc,sent_idx,eer_json_en):
    sentence = serif_doc.sentences[sent_idx]
    token_sequence = sentence.add_new_token_sequence(0.7)
    tokens = eer_json_en['token']
    cursor = 0
    for i in tokens:
        start_char_off = sentence.text.find(i,cursor)
        assert start_char_off != -1
        end_char_off = start_char_off + len(i) - 1
        token_sequence.add_new_token(start_char_off,end_char_off,i)
        cursor = end_char_off + 1



def find_or_add_em(serif_doc,sent_idx,eer_json_en,h_or_t):
    en = None
    if h_or_t == 'h':
        en = eer_json_en['h']
    else:
        en = eer_json_en['t']
    if serif_doc.sentences[sent_idx].sentence_theory.parse is None or serif_doc.sentences[sent_idx].sentence_theory.parse.root is None:
        return None
    pre_terminals = serif_doc.sentences[sent_idx].sentence_theory.parse.root.preterminals
    head_node = pre_terminals[en['pos'][0]]
    tail_node = pre_terminals[en['pos'][-1]-1]
    event_mention_set = serif_doc.sentences[sent_idx].sentence_theory.event_mention_set
    if event_mention_set is None:
        event_mention_set = serif_doc.sentences[sent_idx].add_new_event_mention_set()
    syn_node_to_em = dict()
    for event_mention in serif_doc.sentences[sent_idx].sentence_theory.event_mention_set:
        syn_node_to_em[event_mention.anchor_node] = event_mention
    anchor_node = find_lowest_common_ancestor(head_node,tail_node)
    if anchor_node in syn_node_to_em:
        return syn_node_to_em[anchor_node]
    new_em = event_mention_set.add_new_event_mention("GIGAWORD_EVENT", anchor_node, 1.0)
    return new_em

def find_or_add_eer(serif_doc,sent_idx,eer_json_en):
    serif_eerm_set = serif_doc.event_event_relation_mention_set
    if serif_eerm_set is None:
        serif_eerm_set = serif_doc.add_new_event_event_relation_mention_set()
    left_em = find_or_add_em(serif_doc,sent_idx,eer_json_en,'h')
    right_em = find_or_add_em(serif_doc,sent_idx,eer_json_en,'t')
    if left_em is None or right_em is None:
        logger.critical("Skipping {}".format(eer_json_en))
    eerm = serif_eerm_set.add_new_event_event_relation_mention(
        eer_json_en['relation'], 1.0, "LDC")
    eerm.add_new_event_mention_argument("arg1", left_em)
    eerm.add_new_event_mention_argument("arg2", right_em)

def pipeline(input_list,seq_num,output_dir):
    sent_splitter = NewlineSentenceSplitter()
    benepar_model = BeneparParser("/nfs/raid87/u10/shared/Hume/common/nltk_data/models/benepar_en",add_heads=True)
    noun_mention_model = NounPhraseMentionModel()
    eer_json_ens = list()
    with open(input_list) as fp:
        for idx,i in enumerate(fp):
            if idx % 10000 == 0:
                logger.info("Parsing {}".format(idx))
            eer_json_ens.append(ast.literal_eval(i))
    buckets = [eer_json_ens]

    for idx,bucket in enumerate(buckets):
        logger.info("Processing {}/{}".format(idx,len(bucket)))
        txt = "\n".join(" ".join(i['token']) for i in bucket)
        serif_doc = txt_to_serif_doc(txt,"ENG_NW_GIGAWORD_SENT_{}_{}".format(seq_num,idx))
        sent_splitter.process(serif_doc)
        for sent_idx,sent in enumerate(serif_doc.sentences):
            my_tokenizer(serif_doc,sent_idx,bucket[sent_idx])
        benepar_model.process(serif_doc)
        noun_mention_model.process(serif_doc)
        for sent_idx, sent in enumerate(serif_doc.sentences):
            find_or_add_eer(serif_doc,sent_idx,bucket[sent_idx])
        serif_doc.save(os.path.join(output_dir,"{}.xml".format(serif_doc.docid)))
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_list")
    parser.add_argument("--seq_num",type=int)
    parser.add_argument("--output_dir")
    args = parser.parse_args()
    pipeline(args.input_list,args.seq_num,args.output_dir)