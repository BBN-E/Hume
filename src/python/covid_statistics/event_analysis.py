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

def get_marked_up_sentence(left_span,serif_sentence):
    s = ""
    for off,c in enumerate(serif_sentence.text):
        if left_span[0] - serif_sentence.start_char == off:
            s += "["
        s += c
        if left_span[1] - serif_sentence.start_char == off:
            s += "]"
    s = s.replace("\n"," ").replace("\r"," ").replace("\t"," ")
    return s

def single_document_event(serifxml_path):
    serif_doc = serifxml3.Document(serifxml_path)

    span_to_ems = dict()

    for sentence in serif_doc.sentences:
        for serif_em in sentence.event_mention_set:
            span = get_anchor_offset(serif_em)

            span_to_ems.setdefault(span,set()).add(serif_em)

    ret = list()
    for span,ems in span_to_ems.items():
        groundings = set()
        example_em = None
        for serif_em in ems:
            groundings.update(get_all_good_event_type_from_serif_em(serif_em))
            example_em = serif_em
        for grounding in groundings:
            ret.append((grounding,get_marked_up_sentence(span,example_em.owner_with_type("Sentence"))))
    return ret



def main_multiprocessing():
    input_serif_list = "/d4m/ears/expts/48076.aylien.full.021621.v1/expts/test_pl/doctheory_resolver/serif.list.10p"
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(input_serif_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_event, args=(i,)))
        for idx, i in enumerate(workers):
            i.wait()
            ems = i.get()
            for left_type,sentence_markedup in ems:
                print(left_type,sentence_markedup)

def main(input_serif_list,output_path):
    with open(input_serif_list) as fp,open(output_path,'w') as wfp:
        for i in fp:
            i = i.strip()
            ems = single_document_event(i)
            for left_type,sentence_markedup in ems:
                wfp.write("{}\t{}\n".format(left_type,sentence_markedup))

if __name__ == "__main__":
    main(sys.argv[1],sys.argv[2])