import os,sys,json,collections,multiprocessing
import serifxml3

def get_event_mention_semantic_phrase_info(serif_em,serif_sentence_tokens):
    serif_em_semantic_phrase_char_start = serif_sentence_tokens[int(serif_em.semantic_phrase_start)].start_char
    serif_em_semantic_phrase_char_end = serif_sentence_tokens[int(serif_em.semantic_phrase_end)].end_char
    serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[int(serif_em.semantic_phrase_start):int(serif_em.semantic_phrase_end)+1])
    return serif_em_semantic_phrase_text, serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end

Instance = collections.namedtuple("Instance",['score','trigger','sentence'])

def single_document_handler(serif_path):
    type_to_ins = dict()
    serif_doc = serifxml3.Document(serif_path)
    for sentence in serif_doc.sentences:
        sentence_theory = sentence.sentence_theory
        sentence_text = " ".join(i.text for i in sentence_theory.token_sequence)
        for event_mention in sentence_theory.event_mention_set:
            serif_em_semantic_phrase_text, serif_em_semantic_phrase_char_start, serif_em_semantic_phrase_char_end = get_event_mention_semantic_phrase_info(event_mention,sentence_theory.token_sequence)

            for factor_type in event_mention.factor_types:
                type_to_ins.setdefault(factor_type.event_type,set()).add(Instance(factor_type.score,serif_em_semantic_phrase_text,sentence_text))
    return type_to_ins

if __name__ == "__main__":
    type_to_ins = dict()
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open("/home/hqiu/ld100/Hume_pipeline/Hume/expts/causeex_collab2_0913a_m24_shaved_dataset.regtest.500.120419/grounded_serifxml.list") as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_handler,args=(i,)))
        for idx,i in enumerate(workers):
            i.wait()
            partial = i.get()
            for factor_type,ens in partial.items():
                type_to_ins.setdefault(factor_type,set()).update(ens)
    for factor_type,ens in type_to_ins.items():
        for en in sorted(ens,key=lambda x:x.score,reverse=True):
            print("{}\t{}\t{}\t{}".format(factor_type,en.score,en.trigger,en.sentence))
        print("#########################################################################")