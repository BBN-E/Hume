import os,sys,json,collections

import serifxml3,multiprocessing

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir,))
sys.path.append(project_root)

from serif_event_mention import get_event_anchor

Instance = collections.namedtuple('Instance',['left_mention','left_type','relation','right_mention','rigit_type','score','sentence'])

def single_document_handler(serif_path):
    serif_doc = serifxml3.Document(serif_path)
    entries = list()
    event_mention_to_sentence_theory = dict()
    for sent_idx,sentence in enumerate(serif_doc.sentences):
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set:
            event_mention_to_sentence_theory[event_mention] = sentence_theory
    for serif_eerm in serif_doc.event_event_relation_mention_set or []:
        serif_em_arg1 = None
        serif_em_arg2 = None
        relation_type = serif_eerm.relation_type
        confidence = serif_eerm.confidence
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.role == "arg1":
                serif_em_arg1 = arg.event_mention
            if arg.role == "arg2":
                serif_em_arg2 = arg.event_mention
        if serif_em_arg1 is not None and serif_em_arg2 is not None:
            left_em_text = get_event_anchor(serif_em_arg1,event_mention_to_sentence_theory[serif_em_arg1].token_sequence).replace("\t"," ").replace("\n"," ")
            right_em_text = get_event_anchor(serif_em_arg2,event_mention_to_sentence_theory[serif_em_arg2].token_sequence).replace("\t"," ").replace("\n"," ")
            sentence_text = " ".join(i.text for i in event_mention_to_sentence_theory[serif_em_arg1].token_sequence).replace("\n"," ").replace("\t"," ")
            if len(serif_em_arg1.factor_types) < 1:
                entries.append(left_em_text)
            if len(serif_em_arg2.factor_types) < 1:
                entries.append(right_em_text)
        else:
            raise ValueError
    return entries

def main(serif_list,prefix):
    eer_list = list()
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(serif_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_handler,args=(i,)))
        for idx,i in enumerate(workers):
            i.wait()
            entries = i.get()
            eer_list.extend(entries)
    for i in eer_list:
        print("{}".format(i))

if __name__ == "__main__":
    # expt_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/causeex_sams_expt1.120419.regtest.170doc.120519.v1"
    # import argparse
    # parser= argparse.ArgumentParser()
    # parser.add_argument("--expt_root",required=True)
    # args = parser.parse_args()
    # expt_root = args.expt_root
    # if os.path.isfile(os.path.join(expt_root,"event_event_relations_serifxml.list")):
    #     print("##event event relations stage")
    #     prefix = "[event-event-relation]"
    #     main(os.path.join(expt_root,"event_event_relations_serifxml.list"),prefix)
    main("/d4m/ears/expts/466823_v1_CX/expts/cx_estonia.040320.cx.v2/doc_consolidation/pyserif_files.list","[event-event-relation]")