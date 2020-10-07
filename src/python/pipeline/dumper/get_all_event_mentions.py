import os,sys,json,collections,multiprocessing
import serifxml3

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir,))
sys.path.append(project_root)


Instance = collections.namedtuple('Instance',['type','score','trigger','sentence'])

total_events_count=0
total_events_count_with_cf=0


def get_event_anchor(serif_em:serifxml3.EventMention,serif_sentence_tokens:serifxml3.TokenSequence):
    semantic_phrase = ""
    anchors = []
    anchor = ""
    if serif_em.semantic_phrase_start is not None:
        serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[int(serif_em.semantic_phrase_start):int(serif_em.semantic_phrase_end)+1])
        semantic_phrase = serif_em_semantic_phrase_text
    if len(serif_em.anchors) > 0:
        anchors =  [i.anchor_node.text for i in serif_em.anchors]
    anchor =  serif_em.anchor_node.text

    return anchor,anchors,semantic_phrase

def get_event_arg(serif_em:serifxml3.EventMention):
    ret = list()
    for argument in serif_em.arguments:
        if isinstance(argument.mention,serifxml3.Mention):
            ret.append([argument.role,argument.mention.text])
        elif isinstance(argument.value_mention,serifxml3.ValueMention):
            ret.append([argument.role,argument.value_mention.text])
        else:
            raise NotImplementedError
    return ret

def get_event_type(serif_em:serifxml3.EventMention):

    event_type_12 = [[serif_em.event_type,serif_em.score,serif_em.direction_of_change]]

    event_types = []
    for event_type in serif_em.event_types:
        event_types.append([event_type.event_type,event_type.score, event_type.magnitude])
    factor_types = []
    for event_type in serif_em.factor_types:
        factor_types.append([event_type.event_type,event_type.score,event_type.magnitude])

    return event_type_12,event_types,factor_types

def get_string_for_event_mention(serif_em:serifxml3.EventMention,serif_sentence_tokens):
    ret = ""
    anchor,anchors,semantic_phrase = get_event_anchor(serif_em,serif_sentence_tokens)
    ret += "Anchor:\t{}\nAnchors:\t{}\nSemanticPhrase:\t{}\n".format(anchor,anchors,semantic_phrase)
    event_type,event_types,factor_types = get_event_type(serif_em)

    for factor_type in factor_types:
        if factor_type[2]!=0.5:
            print("===\t" + semantic_phrase + "\t" + str(factor_type) + "\t" + str(serif_em.direction_of_change))

    if "Unspecified" not in str(serif_em.direction_of_change):
        print("===\t" + semantic_phrase + "\t" + str(serif_em.direction_of_change))

    ret += "EvType:\t{}\nEvTypes:\t{}\nCfTypes:\t{}\n".format(event_type,event_types,factor_types)
    args = get_event_arg(serif_em)
    for arg in args:
        ret += "Arg:\t{}\t{}\n".format(arg[0],arg[1])

#    if len(factor_types)>0:
#        total_events_count_with_cf+=1
#    total_events_count+=1

    return ret

def single_document_hanlder(serif_path):
    serif_doc = serifxml3.Document(serif_path)

    event_type_groundings = []
    event_types_groundings = []
    factor_types_groundings = []

    ret = ""

    for sent_idx,sentence in enumerate(serif_doc.sentences):
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set:
            # print("######")
            sentence_text = " ".join(i.text for i in sentence_theory.token_sequence).replace("\n"," ").replace("\t"," ")
            # print("Sentence:\t" + sentence_text)
            # print(get_string_for_event_mention(event_mention,sentence_theory.token_sequence))
            ret += "######\nSentence:\t{}\n{}\n".format(sentence_text,get_string_for_event_mention(event_mention,sentence_theory.token_sequence))

    return ret

def main(serif_list):
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(serif_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_hanlder,args=(i,)))
        for idx,i in enumerate(workers):
            i.wait()
            print(i.get())
            # print(i.get())

if __name__ == "__main__":
    # expt_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/causeex_sams_expt1.120419.regtest.170doc.120519.v1"
    # main("/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/wm_thanksgiving.121019.regtest.small.121319/grounded_serifxml.list")

    #main("/nfs/raid88/u10/users/bmin/temp/cx_estonia_eer.serifxml.100doc.list")
    # main("/nfs/raid88/u10/users/bmin/temp/wm_dec19_eer.v2.serifxml.100doc.list")
    main("/tmp/list1")