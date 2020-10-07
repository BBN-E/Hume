import os,sys,json
import enum
import serifxml3

def get_event_anchor(serif_em:serifxml3.EventMention,serif_sentence_tokens:serifxml3.TokenSequence):
    if serif_em.semantic_phrase_start is not None:
        serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[int(serif_em.semantic_phrase_start):int(serif_em.semantic_phrase_end)+1])
        return serif_em_semantic_phrase_text
    elif len(serif_em.anchors) > 0:
        return " ".join(i.anchor_node.text for i in serif_em.anchors)
    else:
        return serif_em.anchor_node.text
class SerifEventMentionTypingField(enum.Enum):
    event_type = "event_type"
    event_types = "event_types"
    factor_types = "factor_types"

def get_event_type(serif_em:serifxml3.EventMention,typing_field:SerifEventMentionTypingField):
    if typing_field == SerifEventMentionTypingField.event_type:
        return [[serif_em.event_type,serif_em.score]]
    ret = list()
    if typing_field == SerifEventMentionTypingField.event_types:
        for event_type in serif_em.event_types:
            ret.append([event_type.event_type,event_type.score])
    elif typing_field == SerifEventMentionTypingField.factor_types:
        for event_type in serif_em.factor_types:
            ret.append([event_type.event_type,event_type.score])
    else:
        raise NotImplementedError
    return ret

def assembley_event_frame(serif_em:serifxml3.EventMention):
    sentence = serif_em.owner_with_type(serifxml3.Sentence)
    sentence_theory = sentence.sentence_theory
    # sentence_text = " ".join(i.text for i in sentence_theory.token_sequence).replace("\n", " ").replace("\t", " ")
    event_anchor = get_event_anchor(serif_em, sentence_theory.token_sequence).replace("\n", " ").replace("\t", " ")
    factor_types_groundings = []
    for event_type in serif_em.factor_types:
        factor_types_groundings.append("factor_types: {} , trend: {}".format(event_type.event_type.split("#")[-1], event_type.trend))
    pattern_id = "polarity: {}".format(serif_em.polarity)
    buf = "\nAnchor: {}\n{}\n{}".format(event_anchor,pattern_id,"\n".join(factor_types_groundings))
    return buf



def single_document_hanlder(serif_doc):

    for serif_eerm in serif_doc.event_event_relation_mention_set or []:
        serif_em_arg1 = None
        serif_em_arg2 = None
        relation_type = serif_eerm.relation_type
        polarity = serif_eerm.polarity
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.role == "arg1":
                serif_em_arg1 = arg.event_mention
            if arg.role == "arg2":
                serif_em_arg2 = arg.event_mention
        if serif_em_arg1 is not None and serif_em_arg2 is not None:
            sentence = serif_em_arg1.owner_with_type(serifxml3.Sentence)
            sentence_theory = sentence.sentence_theory
            if "factor_types:" in assembley_event_frame(serif_em_arg1) and "factor_types:" in assembley_event_frame(serif_em_arg2):
                print("docid:{} sent: {}".format(serif_doc.docid,sentence.text))
                print(assembley_event_frame(serif_em_arg1))
                print()
                print("CF: {} polarity: {} conf: {}".format(relation_type,polarity,serif_eerm.confidence))
                print(assembley_event_frame(serif_em_arg2))
                print("#########################")

if __name__ == "__main__":
    d = "/nfs/raid88/u10/users/hqiu/regtest/results/1596063603/hume_test.041420.cx.v1/expts/pyserif/pyserif_confidence_calibration/27/output/ENG_NW_WM_efca0689465beb45bde9494e05ca8cd3_2.xml"
    # file_list = [os.path.join(d,i) for i in os.listdir(d)]
    file_list = [d]
    for f in file_list:
        serif_doc = serifxml3.Document(f)
        single_document_hanlder(serif_doc)