import os

hume_root = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir))

def main():
    noun_to_cnt = dict()
    with open("/home/hqiu/tmp/all_mentions.dump") as fp:
        for i in fp:
            i = i.strip()
            i = i.lower()
            for t in i.split(" "):
                t = t.strip()
                if len(t) > 0:
                    noun_to_cnt[t] = noun_to_cnt.get(t,0) + 1
    existed_nouns = set()
    blacked_nouns = set()
    with open(os.path.join(hume_root,"resource/generic_events/generic_event.whitelist.wn-fn.variants")) as fp:
        for i in fp:
            i = i.strip()
            if i.startswith("#") is False:
                existed_nouns.add(i)
            else:
                i = i.replace("#","")
                blacked_nouns.add(i.strip())
    for word, cnt in sorted(noun_to_cnt.items(),key=lambda x:x[1],reverse=True):
        if word not in existed_nouns and word not in blacked_nouns:
            print("{}: {}".format(word, cnt))

if __name__ == "__main__":
    main()