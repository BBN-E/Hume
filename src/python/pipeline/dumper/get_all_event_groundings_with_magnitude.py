import os,sys,json,collections,multiprocessing
import serifxml3

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir,))
sys.path.append(project_root)

from serif_event_mention import get_event_anchor,get_event_arg

Instance = collections.namedtuple('Instance',['type','score','magnitude','trigger','sentence'])

def single_document_hanlder(serif_path):
    serif_doc = serifxml3.Document(serif_path)

    event_type_groundings = []
    event_types_groundings = []
    factor_types_groundings = []

    for sent_idx,sentence in enumerate(serif_doc.sentences):
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set:
            sentence_text = " ".join(i.text for i in sentence_theory.token_sequence).replace("\n"," ").replace("\t"," ")
            event_anchor = get_event_anchor(event_mention,sentence_theory.token_sequence).replace("\n"," ").replace("\t"," ")
            # event_type_groundings.append(Instance(event_mention.event_type,event_mention.score,event_anchor,sentence_text))
            for event_type in event_mention.event_types:
                event_types_groundings.append(Instance(event_type.event_type,event_type.score,None,event_anchor,sentence_text))
            for event_type in event_mention.factor_types:
                factor_types_groundings.append(Instance(event_type.event_type,event_type.score,event_type.magnitude,event_anchor,sentence_text))
    return event_type_groundings,event_types_groundings,factor_types_groundings

def main(serif_list,prefix):
    event_type_groundings_all = list()
    event_types_groundings_all = list()
    factor_types_groundings_all = list()

    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(serif_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_hanlder,args=(i,)))
        for idx,i in enumerate(workers):
            i.wait()
            event_type_groundings,event_types_groundings,factor_types_groundings = i.get()
            event_type_groundings_all.extend(event_type_groundings)
            event_types_groundings_all.extend(event_types_groundings)
            factor_types_groundings_all.extend(factor_types_groundings)
    print("#############")
    for i in sorted(event_type_groundings_all,key=lambda x:(x.type,-x.score)):
        print("{}\tEventType\t{}\t{}\t{}\t{}\t{}".format(prefix,i.type,i.score,i.magnitude,i.trigger,i.sentence))
    print("#############")
    for i in sorted(event_types_groundings_all,key=lambda x:(x.type,-x.score)):
        print("{}\tEventTypes\t{}\t{}\t{}\t{}\t{}".format(prefix,i.type,i.score,i.magnitude,i.trigger,i.sentence))
    print("#############")
    for i in sorted(factor_types_groundings_all,key=lambda x:(x.type,-x.score)):
        print("{}\tFactorTypes\t{}\t{}\t{}\t{}\t{}".format(prefix,i.type,i.score,i.magnitude,i.trigger,i.sentence))

if __name__ == "__main__":
    # expt_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/causeex_sams_expt1.120419.regtest.170doc.120519.v1"

    main("/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/pg_test.121419.internal_lcc/grounded_serifxml.list","[PG]")
    # import argparse
    # parser= argparse.ArgumentParser()
    # parser.add_argument("--expt_root",required=True)
    # args = parser.parse_args()
    # expt_root = args.expt_root
    # if os.path.isfile(os.path.join(expt_root,"serif_serifxml.list")):
    #     prefix = "[serif]"
    #     print("##Serif stage")
    #     main(os.path.join(expt_root,"serif_serifxml.list"),prefix)
    # if os.path.isfile(os.path.join(expt_root,"kbp_serifxml.list")):
    #     print("##kbp stage")
    #     prefix = "[kbp]"
    #     main(os.path.join(expt_root,"kbp_serifxml.list"),prefix)
    # if os.path.isfile(os.path.join(expt_root,"generic_events_serifxml_out.list")):
    #     print("##generic event stage")
    #     prefix = "[generic-event]"
    #     main(os.path.join(expt_root,"generic_events_serifxml_out.list"),prefix)
    # if os.path.isfile(os.path.join(expt_root,"learnit_decoding_event_and_event_arg.list")):
    #     print("##LearnIt event and event arg stage")
    #     prefix = "[learnit-event-and-eventarg]"
    #     main(os.path.join(expt_root,"learnit_decoding_event_and_event_arg.list"),prefix)
    # if os.path.isfile(os.path.join(expt_root,"nn_events_serifxml.list")):
    #     print("##nn event stage")
    #     prefix = "[nn-events]"
    #     main(os.path.join(expt_root,"nn_events_serifxml.list"),prefix)
    # if os.path.isfile(os.path.join(expt_root,"event_consolidation_serifxml_out.list")):
    #     print("##event consolidation stage")
    #     prefix = "[event-consolidation]"
    #     main(os.path.join(expt_root,"event_consolidation_serifxml_out.list"),prefix)
    # if os.path.isfile(os.path.join(expt_root,"grounded_serifxml.list")):
    #     print("##probablistic grounding stage")
    #     prefix = "[probablistic-grounding]"
    #     main(os.path.join(expt_root,"grounded_serifxml.list"),prefix)