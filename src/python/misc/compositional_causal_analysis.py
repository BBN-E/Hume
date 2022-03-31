import csv
import logging

import serifxml3

logger = logging.getLogger(__name__)


def dual_span_marking(serif_sentence, left_start_token_idx, left_end_token_idx, right_start_token_idx,
                      right_end_token_idx):
    resolved_tokens = list()
    for token_idx, token in enumerate(serif_sentence.token_sequence):
        c = ""
        if token_idx == left_start_token_idx:
            c += "["
        if token_idx == right_start_token_idx:
            c += "{"
        c += token.text
        if token_idx == right_end_token_idx:
            c += "}"
        if token_idx == left_end_token_idx:
            c += "]"
        resolved_tokens.append(c)
    return " ".join(resolved_tokens)


def event_worker(serif_em):
    theme_strings = list()
    theme_mentions = list()
    property_strings = list()
    property_mentions = list()
    token_sequence = serif_em.owner_with_type('Sentence').token_sequence
    trigger_word = " ".join(
        i.text for i in token_sequence[serif_em.semantic_phrase_start: serif_em.semantic_phrase_end + 1])
    for event_arg in serif_em.arguments:
        if event_arg.role in {"has_theme"}:
            theme_strings.append(event_arg.value.text),
            theme_mentions.append(event_arg.value)
        elif event_arg.role in {"has_property"}:
            property_strings.append(event_arg.value.text)
            property_mentions.append(event_arg.value)
    assert len(theme_strings) < 2 and len(property_strings) < 2
    return {
        "em_id": serif_em.id,
        "trigger": trigger_word,
        "groundings": list(factor.event_type for factor in serif_em.factor_types),
        "theme_mentions": theme_mentions,
        "theme_strings": theme_strings,
        "property_mentions": property_mentions,
        "property_strings": property_strings,
        "theme_joint_grounding": list(
            {"trigger": trigger_word, "type": factor.event_type,
             "theme": theme_strings[0] if len(theme_strings) > 0 else None,
             "property": property_strings[0] if len(property_strings) > 0 else None} for factor in
            serif_em.factor_types)
    }


def causal_relation_worker(serif_eerm):
    serif_em_arg1 = None
    serif_em_arg2 = None
    relation_type = serif_eerm.relation_type
    confidence = serif_eerm.confidence
    for arg in serif_eerm.event_mention_relation_arguments:
        if arg.role == "arg1":
            serif_em_arg1 = arg.event_mention
        if arg.role == "arg2":
            serif_em_arg2 = arg.event_mention
    left_frame = event_worker(serif_em_arg1)
    right_frame = event_worker(serif_em_arg2)
    eerm_text = dual_span_marking(serif_em_arg1.owner_with_type("Sentence"), serif_em_arg1.semantic_phrase_start,
                                  serif_em_arg1.semantic_phrase_end, serif_em_arg2.semantic_phrase_start,
                                  serif_em_arg2.semantic_phrase_end)
    return {
        "eerm_id": serif_eerm.id,
        "relation_type": relation_type,
        "left_event_mention": left_frame,
        "right_event_mention": right_frame,
        "confidence": confidence,
        "groundings": list(
            {"left_type": x, "relation_type": relation_type, "right_type": y, "eerm_text": eerm_text} for x in
            left_frame["theme_joint_grounding"] for y in
            right_frame["theme_joint_grounding"]),
        "text": eerm_text,
        "left_composition": len(left_frame["theme_mentions"]) + len(left_frame["property_mentions"]) > 0,
        "right_composition": len(right_frame["theme_mentions"]) + len(right_frame["property_mentions"]) > 0
    }


def single_document_worker(serif_path, csv_writer):
    serif_doc = serifxml3.Document(serif_path)
    single_end_has_theme = 0
    both_end_has_theme = 0
    no_end_has_theme = 0
    for serif_eerm in serif_doc.event_event_relation_mention_set or ():
        eerm_extracted = causal_relation_worker(serif_eerm)
        if eerm_extracted["left_composition"] and eerm_extracted["right_composition"]:
            both_end_has_theme += 1
            for grounding in eerm_extracted["groundings"]:
                csv_writer.writerow(
                    [serif_path, grounding["eerm_text"], grounding["relation_type"], grounding["left_type"],
                     grounding["right_type"]])
                logger.critical(
                    "{} {}".format(serif_path, grounding))
        elif eerm_extracted["left_composition"] or eerm_extracted["right_composition"]:
            single_end_has_theme += 1
        else:
            no_end_has_theme += 1

    logger.info("Doc: {} both: {} single: {} no: {}".format(serif_doc.docid, both_end_has_theme, single_end_has_theme,
                                                            no_end_has_theme))


def main():
    logging.basicConfig(level=logging.INFO)
    input_serif_list = "/nfs/raid88/u10/users/hqiu_ad/repos/Hume/expts/dsmte.021722.v1/pyserif_after_pg/pyserif_main/serifxml.list"
    debugging_output = "/home/hqiu/tmp/wm_dsmte.021722.csv"
    with open(input_serif_list) as fp, open(debugging_output, 'w') as wfp:
        csv_writer = csv.writer(wfp)
        for i in fp:
            i = i.strip()
            single_document_worker(i, csv_writer)


if __name__ == "__main__":
    main()
