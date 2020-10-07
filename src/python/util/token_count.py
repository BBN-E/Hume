import glob

def folder_to_token_acc_count(p):
    acc_cnt_cnt = dict()
    for path in glob.glob(p):
        with open(path) as fp:
             for i in fp:
                 i = i.strip()
                 space_cnt = i.count(" ")
                 for s in range(space_cnt // 10+1):
                     acc_cnt_cnt[s] = acc_cnt_cnt.get(s,0)+1
    return acc_cnt_cnt

def main():
    serif_p = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/hume_test.032120.v1/bert/00000/tmp/tokens/*.input_token"
    bert_p = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/hume_test.032120.v1/bert/00000/tmp/tokens/*.bert_token"
    serif_acc_cnt_cnt = folder_to_token_acc_count(serif_p)
    bert_acc_cnt_cnt = folder_to_token_acc_count(bert_p)
    print("### Serif Token")
    print("Have at least number of token | number of sentences")
    print("----------------------------- | -------------------")
    for greater_than in serif_acc_cnt_cnt.keys():
        cnt = serif_acc_cnt_cnt[greater_than]
        print("{} | {}".format(greater_than * 10, cnt))
    print("### BERT token(wordpieces)")
    print("Have at least number of token | number of sentences")
    print("----------------------------- | -------------------")
    for greater_than in bert_acc_cnt_cnt.keys():
        cnt = bert_acc_cnt_cnt[greater_than]
        print("{} | {}".format(greater_than * 10, cnt))

if __name__ == "__main__":
    main()