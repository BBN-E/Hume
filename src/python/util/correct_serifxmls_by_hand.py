import os,sys,json
import enum
import serifxml3

from print_eerm_polarity_trend import single_document_hanlder as print_function

def get_event_anchor(serif_em:serifxml3.EventMention,serif_sentence_tokens:serifxml3.TokenSequence):
    if serif_em.semantic_phrase_start is not None:
        serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[int(serif_em.semantic_phrase_start):int(serif_em.semantic_phrase_end)+1])
        return serif_em_semantic_phrase_text
    elif len(serif_em.anchors) > 0:
        return " ".join(i.anchor_node.text for i in serif_em.anchors)
    else:
        return serif_em.anchor_node.tex
def em_handler(serif_em):
    sentence = serif_em.owner_with_type(serifxml3.Sentence)
    sentence_theory = sentence.sentence_theory
    sentence_text = " ".join(i.text for i in sentence_theory.token_sequence).replace("\n", " ").replace("\t", " ")
    event_anchor = get_event_anchor(serif_em, sentence_theory.token_sequence).replace("\n", " ").replace("\t", " ")
    if ("The 2019 drought caused the recession in Nigeria." in sentence.text or "The Nigerian president said that the drought caused the recession." in sentence.text) and event_anchor == "the recession":
        ef_type = serifxml3.EventMentionFactorType(owner=serif_em)
        ef_type.event_type = "http://ontology.causeex.com/ontology/odps/ICM#DomesticMarketHealth"
        ef_type.magnitude = 0.5
        ef_type.trend = serifxml3.Trend.Unspecified
        serif_em.factor_types.append(ef_type)
    for event_type in serif_em.factor_types:
        if "FoodAndNutritionLevel" in event_type.event_type and event_anchor == "food" and "The drought prevented a rise in food production." in sentence.text:
            event_type.trend = serifxml3.Trend.Increase
        if event_anchor == "production" and "The drought prevented a rise in food production." in sentence.text:
            event_type.trend = serifxml3.Trend.Increase
        if event_anchor == "The drought" and "The drought increased food production." in sentence.text:
            event_type.trend = serifxml3.Trend.Unspecified
        if event_anchor == "production" and "The drought caused food production to not rise." in sentence.text:
            event_type.trend = serifxml3.Trend.Stable
        if event_anchor == "the recession" and "The drought caused the recession to end." in sentence.text:
            event_type.trend = serifxml3.Trend.Increase
        if event_anchor == "the recession" and "The Nigerian president said that the drought caused the recession." in sentence.text:
            event_type.trend = serifxml3.Trend.Decrease
        if event_anchor == "the recession" and "The 2019 drought caused the recession in Nigeria.":
            event_type.trend = serifxml3.Trend.Decrease


def single_document_hanlder(serif_doc):
    modified_eerm = []
    trigger = False
    for sentence in serif_doc.sentences:
        if "The drought didn't cause a decrease in food production." in sentence.text and trigger is False:
            # token = sentence.sentence_theory.token_sequence[9]
            # assert isinstance(token,serifxml3.Token)
            # syn_node = token.syn_node.preterminal
            # assert isinstance(syn_node,serifxml3.SynNode)
            # event_mention = sentence.sentence_theory.event_mention_set.add_new_event_mention("http://ontology.causeex.com/ontology/odps/Event#Event", syn_node, 0.8)
            # anchor = event_mention.add_new_event_mention_anchor(syn_node)
            # event_mention.semantic_phrase_start = 9
            # event_mention.semantic_phrase_end = 9
            # event_mention.direction_of_change = serifxml3.DirectionOfChange.Decrease
            # ef_type = serifxml3.EventMentionFactorType(owner=event_mention)
            # ef_type.event_type = "http://ontology.causeex.com/ontology/odps/ICM#EconomicAgriculturalCapability"
            # ef_type.magnitude = 0.5
            # ef_type.trend = serifxml3.Trend.Decrease
            # event_mention.factor_types.append(ef_type)

            # serif_doc.event_set.add_new_event([event_mention], "http://ontology.causeex.com/ontology/odps/Event#Event")

            # for event_mention_left in sentence.sentence_theory.event_mention_set:
            #     if get_event_anchor(event_mention_left,sentence.sentence_theory.token_sequence) == "The drought":
            #         eerm = serif_doc.event_event_relation_mention_set.add_new_event_event_relation_mention(
            #             "Cause-Effect", 0.8, "LearnIt")
            #         eerm.add_new_event_mention_argument("arg1", event_mention_left)
            #         eerm.add_new_event_mention_argument("arg2", event_mention)
            #         eerm.polarity = serifxml3.Polarity.Negative
            arg1 = None
            arg2 = None
            for event_mention in sentence.sentence_theory.event_mention_set:
                if get_event_anchor(event_mention,sentence.sentence_theory.token_sequence) == "The drought":
                    arg1 = event_mention
                if get_event_anchor(event_mention,sentence.sentence_theory.token_sequence) == "production":
                    arg2 = event_mention
            eerm = serif_doc.event_event_relation_mention_set.add_new_event_event_relation_mention(
                "Cause-Effect", 0.8, "LearnIt")
            eerm.add_new_event_mention_argument("arg1", arg1)
            eerm.add_new_event_mention_argument("arg2", arg2)
            eerm.polarity = serifxml3.Polarity.Negative
            trigger = True

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
            em_handler(serif_em_arg1)
            em_handler(serif_em_arg2)
        if "The drought didn't cause a decrease in food production." in sentence.text and relation_type == "MitigatingFactor-Effect":
            continue
        elif "food" == get_event_anchor(serif_em_arg2,sentence_theory.token_sequence):
            continue
        else:
            if "The drought didn't cause a decrease in food production." in sentence.text:
                serif_eerm.polarity = serifxml3.Polarity.Negative
            modified_eerm.append(serif_eerm)
    serif_doc.event_event_relation_mention_set._children = modified_eerm
    return serif_doc


if __name__ == "__main__":
    d = "/d4m/ears/expts/47837.072320.v2/expts/hume_test.041420.cx.v1/pyserif/pyserif_confidence_calibration/0/output"
    file_list = [os.path.join(d,i) for i in os.listdir(d)]
    save_dir = "/nfs/raid88/u10/users/hqiu/serifxml_corpus/canonical_polarity3"
    for f in file_list:
        serif_doc = serifxml3.Document(f)
        resolved = single_document_hanlder(serif_doc)
        print_function(resolved)
        resolved.save(os.path.join(save_dir,"{}.xml".format(resolved.docid)))