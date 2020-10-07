import os,sys,json,collections,multiprocessing
import serifxml3

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir,))
sys.path.append(project_root)

from serif_event_mention import get_event_anchor,get_event_arg

Instance = collections.namedtuple('Instance',['trigger','arg_role','arg_text','sentence'])

def single_document_hanlder(serif_path):
    serif_doc = serifxml3.Document(serif_path)

    entries = list()
    for sent_idx,sentence in enumerate(serif_doc.sentences):
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set:
            sentence_text = " ".join(i.text for i in sentence_theory.token_sequence).replace("\n"," ").replace("\t"," ")
            event_anchor = get_event_anchor(event_mention,sentence_theory.token_sequence).replace("\n"," ").replace("\t"," ")
            event_args= get_event_arg(event_mention)
            for event_arg in event_args:
                entries.append(Instance(event_anchor,event_arg[0],event_arg[1].replace("\n"," ").replace("\t"," "),sentence_text))
    return entries

def main(serif_list,prefix):
    event_arguments_all = list()

    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(serif_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_hanlder,args=(i,)))
        for idx,i in enumerate(workers):
            i.wait()
            entries = i.get()
            event_arguments_all.extend(entries)

    for i in sorted(event_arguments_all,key=lambda x:(x.trigger,x.arg_role)):
        print("{}\tEventArgument\t{}\t{}\t{}\t{}".format(prefix,i.trigger,i.arg_role,i.arg_text,i.sentence))


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
