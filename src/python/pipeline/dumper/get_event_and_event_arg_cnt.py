import os,sys,json
import serifxml3,multiprocessing

def single_document_hanlder(serif_path):
    serif_doc = serifxml3.Document(serif_path)

    event_mention_cnt = 0
    event_type_cnt = dict()
    event_types_cnt = dict()
    factor_types_cnt = dict()
    arg_role_cnt = dict()

    for sent_idx,sentence in enumerate(serif_doc.sentences):
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set:
            event_mention_cnt+=1
            event_type_cnt[event_mention.event_type] = event_type_cnt.get(event_mention.event_type,0)+1
            for event_type in event_mention.event_types:
                event_types_cnt[event_type.event_type] = event_types_cnt.get(event_type.event_type,0)+1
            for event_type in event_mention.factor_types:
                factor_types_cnt[event_type.event_type] = factor_types_cnt.get(event_type.event_type,0)+1
            for argument in event_mention.arguments:
                arg_role_cnt[argument.role] = arg_role_cnt.get(argument.role,0)+1
    return event_mention_cnt,event_type_cnt,event_types_cnt,factor_types_cnt,arg_role_cnt

def main(serif_list,prefix):
    event_mention_cnt_all = 0
    event_type_cnt_all = dict()
    event_types_cnt_all = dict()
    factor_types_cnt_all = dict()
    arg_role_cnt_all = dict()
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(serif_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_hanlder,args=(i,)))
        for idx,i in enumerate(workers):
            i.wait()
            event_mention_cnt,event_type_cnt,event_types_cnt,factor_types_cnt,arg_role_cnt = i.get()
            event_mention_cnt_all += event_mention_cnt
            for event_type,cnt in event_type_cnt.items():
                event_type_cnt_all[event_type] = event_type_cnt_all.get(event_type,0)+cnt
            for event_type,cnt in event_types_cnt.items():
                event_types_cnt_all[event_type] = event_types_cnt_all.get(event_type,0)+cnt
            for event_type,cnt in factor_types_cnt.items():
                factor_types_cnt_all[event_type] = factor_types_cnt_all.get(event_type,0)+cnt
            for arg_role,cnt in arg_role_cnt.items():
                arg_role_cnt_all[arg_role] = arg_role_cnt_all.get(arg_role,0)+cnt
    print("#############")
    print("{}\tNumber of event_mention: {}".format(prefix,event_mention_cnt_all))
    print("#############")
    for event_type,cnt in sorted(event_type_cnt_all.items(),key=lambda x:x[1],reverse=True):
        print("{}\tEventType: {}\t{}".format(prefix,event_type,cnt))
    print("#############")
    for event_type,cnt in sorted(event_types_cnt_all.items(),key=lambda x:x[1],reverse=True):
        print("{}\tEventTypes: {}\t{}".format(prefix,event_type,cnt))
    print("#############")
    for event_type,cnt in sorted(factor_types_cnt_all.items(),key=lambda x:x[1],reverse=True):
        print("{}\tFactorTypes: {}\t{}".format(prefix,event_type,cnt))
    print("#############")
    for arg_role,cnt in sorted(arg_role_cnt_all.items(),key=lambda x:x[1],reverse=True):
        print("{}\tArgRole: {}\t{}".format(prefix,arg_role,cnt))
    print("#############")

if __name__ == "__main__":
    # expt_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/causeex_sams_expt1.120419.regtest.170doc.120519.v1"
    import argparse
    parser= argparse.ArgumentParser()
    parser.add_argument("--expt_root",required=True)
    args = parser.parse_args()
    expt_root = args.expt_root
    if os.path.isfile(os.path.join(expt_root,"serif_serifxml.list")):
        prefix = "[serif]"
        print("##Serif stage")
        main(os.path.join(expt_root,"serif_serifxml.list"),prefix)
    if os.path.isfile(os.path.join(expt_root,"kbp_serifxml.list")):
        print("##kbp stage")
        prefix = "[kbp]"
        main(os.path.join(expt_root,"kbp_serifxml.list"),prefix)
    if os.path.isfile(os.path.join(expt_root,"generic_events_serifxml_out.list")):
        print("##generic event stage")
        prefix = "[generic-event]"
        main(os.path.join(expt_root,"generic_events_serifxml_out.list"),prefix)
    if os.path.isfile(os.path.join(expt_root,"learnit_decoding_event_and_event_arg.list")):
        print("##LearnIt event and event arg stage")
        prefix = "[learnit-event-and-eventarg]"
        main(os.path.join(expt_root,"learnit_decoding_event_and_event_arg.list"),prefix)
    if os.path.isfile(os.path.join(expt_root,"nn_events_serifxml.list")):
        print("##nn event stage")
        prefix = "[nn-events]"
        main(os.path.join(expt_root,"nn_events_serifxml.list"),prefix)
    if os.path.isfile(os.path.join(expt_root,"event_consolidation_serifxml_out.list")):
        print("##event consolidation stage")
        prefix = "[event-consolidation]"
        main(os.path.join(expt_root,"event_consolidation_serifxml_out.list"),prefix)
    if os.path.isfile(os.path.join(expt_root,"grounded_serifxml.list")):
        print("##probablistic grounding stage")
        prefix = "[probablistic-grounding]"
        main(os.path.join(expt_root,"grounded_serifxml.list"),prefix)
