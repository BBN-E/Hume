import serifxml3
import multiprocessing

def single_documet_processor(serif_path):
    token_to_cnt = dict()
    serif_doc = serifxml3.Document(serif_path)
    for sentence in serif_doc.sentences:
        for token in sentence.sentence_theory.token_sequence:
            text = token.text
            token_to_cnt[text] = token_to_cnt.get(text,0)+1
    return token_to_cnt

def main():
    f_list = "/nfs/raid68/u15/ears/expts/47859.25k.approach.a.073120/expts/hume_test.041420.cx.v1/serif_serifxml.list"
    manager = multiprocessing.Manager()
    word_count_global = dict()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(f_list) as fp:
            for idx,i in enumerate(fp):
                i = i.strip()
                workers.append(pool.apply_async(single_documet_processor,args=(i,)))
                if idx > 4000:
                    break
            for i in workers:
                i.wait()
                word_cnt_local = i.get()
                for word,cnt in word_cnt_local.items():
                    word_count_global[word] = word_count_global.get(word,0)+cnt
    for word,cnt in sorted(word_count_global.items(),key=lambda x:x[1],reverse=True):
        print("{} : {}".format(word,cnt))
if __name__ == "__main__":
    main()
