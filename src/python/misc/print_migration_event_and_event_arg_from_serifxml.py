import os,sys,json

import serifxml3


def get_event_mention_semantic_phrase_info(serif_em,serif_sentence_tokens):
    serif_em_semantic_phrase_char_start = serif_sentence_tokens[int(serif_em.semantic_phrase_start)].start_char
    serif_em_semantic_phrase_char_end = serif_sentence_tokens[int(serif_em.semantic_phrase_end)].end_char
    serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[int(serif_em.semantic_phrase_start):int(serif_em.semantic_phrase_end)+1])
    return serif_em_semantic_phrase_text, serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end

def single_document_handler(serif_path):
    serif_doc = serifxml3.Document(serif_path)
    for sentence in serif_doc.sentences:
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set:
            if event_mention.event_type in {"Migration"}:
                print ("--------------------------------------------")
                print ("sentence: " + sentence.text.replace("\n",""))
                serif_em_semantic_phrase_text, serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end = get_event_mention_semantic_phrase_info(event_mention,sentence_theory.token_sequence)
                print ("trigger: " + serif_em_semantic_phrase_text.replace("\n",""))
                for argument in event_mention.arguments:
                    if isinstance(argument.mention,serifxml3.Mention):
                        print("Argument role: {}".format(argument.role))
                        print(argument.mention.text)
                        print("#############################")
                    if isinstance(argument.value_mention,serifxml3.ValueMention):
                        print("Argument role: {}".format(argument.role))
                        print(argument.value_mention.text)
                        print("#############################")


if __name__ == "__main__":
    root_folder = "/home/hqiu/ld100/hume_pipeline_read_only/Hume/expts/wm_dart.082919/learnit_decoding_event_and_event_arg/EventAndEventArgument/serifxml"
    for root,dirs,files in os.walk(root_folder):
        for file in files:
            if file.endswith(".xml"):
                single_document_handler(os.path.join(root,file))