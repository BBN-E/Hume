import sys
import multiprocessing
import serifxml3


def get_anchor_offset(serif_em):
    # Get from anchor
    anchor_node = serif_em.anchor_node
    serif_em_semantic_phrase_char_start = anchor_node.start_token.start_char
    serif_em_semantic_phrase_char_end = anchor_node.end_token.end_char

    # Reset from semantic phrase info if it exists
    if serif_em.semantic_phrase_start is not None and serif_em.semantic_phrase_end is not None:
        serif_em_semantic_phrase_char_start = serif_em.owner_with_type('Sentence').token_sequence[int(serif_em.semantic_phrase_start)].start_char
        serif_em_semantic_phrase_char_end = serif_em.owner_with_type('Sentence').token_sequence[int(serif_em.semantic_phrase_end)].end_char
    return serif_em_semantic_phrase_char_start,serif_em_semantic_phrase_char_end

def get_all_good_event_type_from_serif_em(serif_em):
    good_event_types = set()
    if serif_em.event_type != "Event":
        good_event_types.add(serif_em.event_type)
    for event_type in serif_em.event_types:
        if event_type.event_type != "Event":
            good_event_types.add(event_type.event_type)
    for factor_type in serif_em.factor_types:
        if factor_type.event_type != "Event":
            good_event_types.add(factor_type.event_type)
    return good_event_types

def get_marked_up_sentence(left_span,right_span,serif_sentence):
    s = ""
    for off,c in enumerate(serif_sentence.text):
        if left_span[0] - serif_sentence.start_char == off:
            s += "["
        if right_span[0] - serif_sentence.start_char == off:
            s += "{"
        s += c
        if left_span[1] - serif_sentence.start_char == off:
            s += "]"
        if right_span[1] - serif_sentence.start_char == off:
            s += "}"
    s = s.replace("\n"," ").replace("\r"," ").replace("\t"," ")
    return s

def single_document_eer_dumper_both_end_must_typed(serifxml_path):
    serif_doc = serifxml3.Document(serifxml_path)

    semantic_span_to_ems = dict()
    eerm_pairs = set()

    for serif_eerm in serif_doc.event_event_relation_mention_set or ():
        serif_em_arg1 = None
        serif_em_arg2 = None
        relation_type = serif_eerm.relation_type
        confidence = serif_eerm.confidence
        if serif_eerm.model != "nlplingo":
            continue
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.role == "arg1":
                serif_em_arg1 = arg.event_mention
            if arg.role == "arg2":
                serif_em_arg2 = arg.event_mention
            if serif_em_arg1 is not None and serif_em_arg2 is not None:
                left_em_span = get_anchor_offset(serif_em_arg1)
                right_em_span = get_anchor_offset(serif_em_arg2)
                semantic_span_to_ems.setdefault(left_em_span,set()).add(serif_em_arg1)
                semantic_span_to_ems.setdefault(right_em_span,set()).add(serif_em_arg2)
                eerm_pairs.add((left_em_span,relation_type,right_em_span))
    ret = list()
    for left_em_span,relation_type,right_em_span in eerm_pairs:
        good_left_types = set()
        good_right_types = set()
        example_em = None
        for serif_em in semantic_span_to_ems[left_em_span]:
            good_left_types.update(get_all_good_event_type_from_serif_em(serif_em))
            example_em = serif_em
        for serif_em in semantic_span_to_ems[right_em_span]:
            good_right_types.update(get_all_good_event_type_from_serif_em(serif_em))
            example_em = serif_em
        if len(good_left_types) > 0 and len(good_right_types) > 0:
            for left_type in good_left_types:
                for right_type in good_right_types:
                    ret.append((left_type,relation_type,right_type,get_marked_up_sentence(left_em_span,right_em_span,example_em.owner_with_type("Sentence"))))

    return ret

def single_document_eer_dumper_untyped(serifxml_path):
    serif_doc = serifxml3.Document(serifxml_path)

    semantic_span_to_ems = dict()
    eerm_pairs = set()

    for serif_eerm in serif_doc.event_event_relation_mention_set or ():
        serif_em_arg1 = None
        serif_em_arg2 = None
        relation_type = serif_eerm.relation_type
        confidence = serif_eerm.confidence
        if serif_eerm.model!="nlplingo":
            continue
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.role == "arg1":
                serif_em_arg1 = arg.event_mention
            if arg.role == "arg2":
                serif_em_arg2 = arg.event_mention
            if serif_em_arg1 is not None and serif_em_arg2 is not None:
                left_em_span = get_anchor_offset(serif_em_arg1)
                right_em_span = get_anchor_offset(serif_em_arg2)
                semantic_span_to_ems.setdefault(left_em_span,set()).add(serif_em_arg1)
                semantic_span_to_ems.setdefault(right_em_span,set()).add(serif_em_arg2)
                eerm_pairs.add((left_em_span,relation_type,right_em_span))

    ret = list()
    for left_em_span, relation_type, right_em_span in eerm_pairs:
        left_em = list(semantic_span_to_ems[left_em_span])[0]
        right_em = list(semantic_span_to_ems[right_em_span])[0]
        ret.append((left_em.event_type, relation_type, right_em.event_type,
                    get_marked_up_sentence(left_em_span, right_em_span, left_em.owner_with_type("Sentence"))))
    return ret


def main_multiprocessing():
    input_serif_list = "/d4m/ears/expts/48076.cord19.full.021621.v1/expts/test_pl/doctheory_resolver/serif.list"
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(input_serif_list) as fp:
            for i in fp:
                i = i.strip()
                # workers.append(pool.apply_async(single_document_eer_dumper_both_end_must_typed, args=(i,)))
                workers.append(pool.apply_async(single_document_eer_dumper_untyped, args=(i,)))
        for idx, i in enumerate(workers):
            i.wait()
            eerms = i.get()
            for left_type,relation_type,right_type,sentence_markedup in eerms:
                print(left_type,relation_type,right_type,sentence_markedup)

def main(running_mode,input_serif_list,output_path):
    with open(input_serif_list) as fp,open(output_path,'w') as wfp:
        for i in fp:
            i = i.strip()
            if running_mode.strip().lower() == "untyped":
                eerms = single_document_eer_dumper_untyped(i)
            elif running_mode.strip().lower() == "both_end_typed":
                eerms = single_document_eer_dumper_both_end_must_typed(i)
            else:
                raise ValueError("Unsupported {}".format(running_mode))
            for left_type, relation_type, right_type, sentence_markedup in eerms:
                wfp.write("{}\t{}\t{}\t{}\n".format(left_type,relation_type,right_type,sentence_markedup))

if __name__ == "__main__":
    main(sys.argv[1],sys.argv[2],sys.argv[3])
