import json
import logging
import serifxml3

logger = logging.getLogger(__name__)


def get_event_span(serif_em_arg1):
    doc_id = serif_em_arg1.document.docid
    sent_id = serif_em_arg1.sentence.sent_no
    start, end = None, None
    if serif_em_arg1.semantic_phrase_start is not None:
        start = serif_em_arg1.semantic_phrase_start
        end = serif_em_arg1.semantic_phrase_end
    else:
        start = serif_em_arg1.anchor_node.start_token.index()
        end = serif_em_arg1.anchor_node.end_token.index()
    return doc_id, sent_id, start, end


def mark_event_mention_pairs(serif_em_arg1, serif_em_arg2, slot0_left_mark="[", slot1_left_mark="{",
                             slot0_right_mark="]", slot1_right_mark="}"):
    _, _, arg1_start, arg1_end = get_event_span(serif_em_arg1)
    _, _, arg2_start, arg2_end = get_event_span(serif_em_arg2)
    marked_tokens = list()
    for idx, token in enumerate(serif_em_arg1.sentence.token_sequence):
        c = ""
        if idx == arg1_start:
            c = slot0_left_mark + c
        if idx == arg2_start:
            c = slot1_left_mark + c
        c += token.text.strip()
        if idx == arg2_end:
            c = c + slot1_right_mark
        if idx == arg1_end:
            c = c + slot0_right_mark
        marked_tokens.append(c)
    return " ".join(marked_tokens)


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


def serialize_eerm_fillable(src_event_mention, relation_type, tgt_event_mention):
    left_doc_id, left_sent_no, left_start_token_idx, left_end_token_idx = get_event_span(src_event_mention)
    right_doc_id, right_sent_no, right_start_token_idx, right_end_token_idx = get_event_span(tgt_event_mention)
    marked_up_string_eerm = mark_event_mention_pairs(src_event_mention, tgt_event_mention,
                                                     slot0_left_mark="<span class=\"slot0\">",
                                                     slot0_right_mark="</span>",
                                                     slot1_left_mark="<span class=\"slot1\">",
                                                     slot1_right_mark="</span>")
    return [
        "{}#{}#{}#{}".format(left_doc_id, left_sent_no, left_start_token_idx,
                             left_end_token_idx), relation_type,
        "{}#{}#{}#{}".format(right_doc_id, right_sent_no, right_start_token_idx,
                             right_end_token_idx),
        marked_up_string_eerm
    ]


def single_document_handler(input_serif_path):
    serif_doc = serifxml3.Document(input_serif_path)
    mentioned_in_eerm_event_mention = set()
    eerm_event_mention_pairs = set()
    for serif_eerm in serif_doc.event_event_relation_mention_set or ():
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.role == "arg1":
                serif_em_arg1 = arg.event_mention
            if arg.role == "arg2":
                serif_em_arg2 = arg.event_mention
        eerm_event_mention_pairs.add(
            (get_event_span(serif_em_arg1), serif_eerm.relation_type, get_event_span(serif_em_arg2)))
        mentioned_in_eerm_event_mention.add(serif_em_arg1)
        mentioned_in_eerm_event_mention.add(serif_em_arg2)
    event_mention_to_cluster = dict()
    for focus_event_mention in mentioned_in_eerm_event_mention:
        event_mention_to_cluster.setdefault(focus_event_mention, set()).add(focus_event_mention)
        serif_sent = focus_event_mention.sentence
        for candiate_event_mention in serif_sent.event_mention_set or ():
            if candiate_event_mention == focus_event_mention:
                continue
            ## Logic 1 common ancestor contains less than 5 tokens
            ancestor = find_lowest_common_ancestor(focus_event_mention.anchor_node, candiate_event_mention.anchor_node)
            if ancestor is not None:
                num_of_tokens = ancestor.end_token.index() - ancestor.start_token.index() + 1
                if num_of_tokens < 5:
                    logger.info("Logic 1 with {} fired and result: {}".format(num_of_tokens, mark_event_mention_pairs(
                        focus_event_mention, candiate_event_mention)))
                    event_mention_to_cluster.setdefault(focus_event_mention, set()).add(candiate_event_mention)
            ## Logic 2 if the anchor node distance is less than 5
            anchor_node_distance = min(
                abs(
                    focus_event_mention.anchor_node.start_token.index() - candiate_event_mention.anchor_node.end_token.index()),
                abs(
                    focus_event_mention.anchor_node.end_token.index() - candiate_event_mention.anchor_node.start_token.index()))
            if anchor_node_distance < 3:
                logger.info("Logic 2 with {} fired and result: {}".format(anchor_node_distance,
                                                                          mark_event_mention_pairs(focus_event_mention,
                                                                                                   candiate_event_mention)))
                event_mention_to_cluster.setdefault(focus_event_mention, set()).add(candiate_event_mention)
    ret = list()
    outputed_eerm_tuple = set()
    for serif_eerm in serif_doc.event_event_relation_mention_set or ():
        relation_type = serif_eerm.relation_type
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.role == "arg1":
                serif_em_arg1 = arg.event_mention
            if arg.role == "arg2":
                serif_em_arg2 = arg.event_mention
        # Serialize original eerm pair as it is
        ret.append(serialize_eerm_fillable(serif_em_arg1, relation_type, serif_em_arg2))
        outputed_eerm_tuple.add((get_event_span(serif_em_arg1), relation_type, get_event_span(serif_em_arg2)))
        # Applying logics above
        for projected_serif_em_arg1 in event_mention_to_cluster.get(serif_em_arg1, ()):
            event_arg1_span = get_event_span(projected_serif_em_arg1)
            for projected_serif_em_arg2 in event_mention_to_cluster.get(serif_em_arg2, ()):
                event_arg2_span = get_event_span(projected_serif_em_arg2)
                if event_arg1_span != event_arg2_span and (
                event_arg1_span, relation_type, event_arg2_span) not in outputed_eerm_tuple and (
                        event_arg1_span, relation_type, event_arg2_span) not in eerm_event_mention_pairs and (
                        event_arg2_span, relation_type, event_arg1_span) not in eerm_event_mention_pairs:
                    logger.info("Outputting new eerm {}: {}".format(relation_type,
                                                                    mark_event_mention_pairs(projected_serif_em_arg1,
                                                                                             projected_serif_em_arg2)))
                    ret.append(serialize_eerm_fillable(projected_serif_em_arg1, relation_type, projected_serif_em_arg2))
                    outputed_eerm_tuple.add((event_arg1_span, relation_type, event_arg2_span))
    return ret


def main(input_serifxml_list, output_fillable_eer_path):
    logging.basicConfig(level=logging.INFO)
    with open(input_serifxml_list) as fp, open(output_fillable_eer_path, 'w') as wfp:
        for i in fp:
            i = i.strip()
            output_frames = single_document_handler(i)
            for out_frame in output_frames:
                wfp.write("{}\n".format(json.dumps(out_frame, ensure_ascii=False)))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input_serifxml_list")
    parser.add_argument("--output_fillable_eer_path")
    args = parser.parse_args()
    main(args.input_serifxml_list, args.output_fillable_eer_path)
