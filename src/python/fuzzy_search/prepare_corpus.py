import os,sys,json
import re

import serifxml3

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir))
sys.path.append(project_root)

from causal_factor_structure import EntityMentionGenerator

def create_segment(document_id,doc_text):
    return """
<SEGMENT>
    <CLEANED_RAW_SOURCE></CLEANED_RAW_SOURCE>
    <CLEANED_RAW_SOURCE_ALIGNMENT></CLEANED_RAW_SOURCE_ALIGNMENT>
    <CLEANED_RAW_TARGET></CLEANED_RAW_TARGET>
    <CLEANED_RAW_TARGET_ALIGNMENT></CLEANED_RAW_TARGET_ALIGNMENT>
    <CLEANED_TOKENIZED_SOURCE>{}</CLEANED_TOKENIZED_SOURCE>
    <CLEANED_TOKENIZED_SOURCE_ALIGNMENT></CLEANED_TOKENIZED_SOURCE_ALIGNMENT>
    <CLEANED_TOKENIZED_TARGET></CLEANED_TOKENIZED_TARGET>
    <CLEANED_TOKENIZED_TARGET_ALIGNMENT></CLEANED_TOKENIZED_TARGET_ALIGNMENT>
    <COLLECTION></COLLECTION>
    <DOCUMENT_ID>{}</DOCUMENT_ID>
    <GUID>[CAUSEEX][{}][1]</GUID>
    <METADATA_GENRE_ID></METADATA_GENRE_ID>
    <RAW_SOURCE></RAW_SOURCE>
    <RAW_TARGET></RAW_TARGET>
    <SEGMENT_INDEX></SEGMENT_INDEX>
    <STEMMED_CLEANED_RAW_TARGET></STEMMED_CLEANED_RAW_TARGET>
    <STEMMED_CLEANED_RAW_TARGET_ALIGNMENT></STEMMED_CLEANED_RAW_TARGET_ALIGNMENT>
    <STEMMED_CLEANED_TOKENIZED_TARGET></STEMMED_CLEANED_TOKENIZED_TARGET>
    <STEMMED_CLEANED_TOKENIZED_TARGET_ALIGNMENT></STEMMED_CLEANED_TOKENIZED_TARGET_ALIGNMENT>
    <TOKENIZED_SOURCE></TOKENIZED_SOURCE>
    <TOKENIZED_TARGET></TOKENIZED_TARGET>
</SEGMENT>
    """.format(doc_text, document_id, document_id)


whitespace_re = re.compile(r"\s+")

def my_escaper(dirty_string):
    ret_str = ""
    for c in dirty_string:
        if c == "\t" or c == "\n" or c == "\r":
            ret_str += ""
        elif c in {"-", "'", ",""."}:
            ret_str += c
        elif c.isalnum() and ((c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'z') or (c >= '0' and c <= '9')):
            ret_str += c
        else:
            ret_str += ""
    return ret_str.strip()



def single_document_worker(serif_path,should_care_entities):
    serif_doc = serifxml3.Document(serif_path)
    segments = list()

    all_possible_words = set()
    event_type_to_mentions = dict()
    evt_cnt = 1

    mention_to_entity = dict()

    entity_to_canonical_name = EntityMentionGenerator._entity_to_canonical_name(serif_doc)

    for serif_entity in serif_doc.entity_set:
        for serif_mention in serif_entity.mentions:
            mention_to_entity[serif_mention] = serif_entity

    for sent_idx,sentence in enumerate(serif_doc.sentences):
        for sentence_theory in sentence.sentence_theories:
            if len(sentence_theory.token_sequence) < 1:
                continue
            for serif_em in sentence_theory.event_mention_set:
                event_text = list()
                argument_text = list()
                event_type_text = set()
                for anchor in serif_em.anchors:
                    anchor_node = anchor.anchor_node
                    event_text.extend([my_escaper(i).lower() for i in anchor_node.text.split(" ")])
                # for argument in serif_em.arguments:
                #     if argument.mention != None:
                #         if entity_to_canonical_name.get(mention_to_entity.get(argument.mention, None),
                #                                         None) is not None:
                #             argument_text.extend(my_escaper(i) for i in
                #                                  entity_to_canonical_name.get(mention_to_entity[argument.mention],
                #                                                               None).split(" "))
                #         else:
                #             argument_text.extend(my_escaper(i) for i in argument.mention.atomic_head.text.split(" "))
                # for event_type in serif_em.event_types:
                #     event_type_text.add("EVENT-{}".format(event_type.event_type))
                canonical_name_in_evt_argument = set()
                for argument in serif_em.arguments:
                    if argument.mention != None:
                        if entity_to_canonical_name.get(mention_to_entity.get(argument.mention,None),None) is not None:
                            canonical_name_in_evt_argument.add(entity_to_canonical_name.get(mention_to_entity.get(argument.mention,None),None))
                if len(canonical_name_in_evt_argument) > 0 and len(should_care_entities) > 0 and len(should_care_entities.intersection(canonical_name_in_evt_argument)) < 1:
                    continue
                all_possible_words.update(event_text)
                all_possible_words.update(argument_text)
                all_possible_words.update(event_type_text)

                event_mention_str = "{}".format(" ".join(event_text))
                if argument_text:
                    event_mention_str += " {}".format(" ".join(argument_text))

                for event_type in serif_em.event_types:
                    event_type_to_mentions.setdefault(event_type.event_type, set()).add(event_mention_str)
                mention_id = "{}-{}-{}-{}".format(serif_doc.docid, sentence.start_char,serif_em.anchor_node.start_char,
                                               event_mention_str.replace(" ", "_"))

                # mention_id = "[{}][{}][{}]".format("CAUSEEX",serif_doc.docid,evt_cnt)
                evt_cnt += 1
                segment = create_segment(mention_id, event_mention_str)
                segments.append(segment)
    # with open(os.path.join(output_corpus_dir,serif_doc.docid+".extracted_clir_doc.xml"),'w') as fp:
    #     for i in segments:
    #         fp.write(i)

    all_possible_words.discard("")
    return all_possible_words, event_type_to_mentions, segments



def main(input_serif_list,output_dir,canonical_name_set_in_query):
    all_possible_words = set()
    all_event_type_to_mentions = dict()
    all_segments = list()
    with open(input_serif_list) as fp:
        for i in fp:
            i = i.strip()
            possible_words, event_type_to_mentions, segments = single_document_worker(i,canonical_name_set_in_query)
            all_possible_words.update(possible_words)
            for event_type,mentions in event_type_to_mentions.items():
                all_event_type_to_mentions.setdefault(event_type,set()).update(mentions)
            all_segments.extend(segments)

    with open(os.path.join(output_dir, 'segments'), 'w') as fp:
        for i in all_segments:
            fp.write(i)

    with open(os.path.join(output_dir,'word.list'),'w') as fp:
        for i in all_possible_words:
            fp.write("{}\n".format(i.replace(" ", "\n")))
    with open(os.path.join(output_dir,'query.tsv'),'w') as fp:
        fp.write("{}\t{}\t{}\n".format("query_id","query_string","domain_id"))
        for event_type,mentions in all_event_type_to_mentions.items():
            idx = 0
            for mention in mentions:
                if " " in mention:
                    fp.write("{}\t\"{}\"\t{}\n".format(mention.replace(" ", "_"), mention.strip(), "TBD"))
                else:
                    fp.write("{}\t{}\t{}\n".format(mention.replace(" ", "_"), mention.strip(), "TBD"))
                idx += 1
                if idx > 5:
                    break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_serif_list', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--input_structure_query_json', required=True)
    args = parser.parse_args()
    should_care_entities = set()
    with open(args.input_structure_query_json) as fp:
        query_dict = json.load(fp)
    for en in query_dict:
        entities = set(i['canonical_name'] for i in en['entity_mentions'])
        should_care_entities.update(entities)
    main(args.input_serif_list,args.output_dir,should_care_entities)