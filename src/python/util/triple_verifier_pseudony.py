import os,sys

def main(f):

    s_triple = dict()
    p_triple = dict()
    o_triple = dict()

    warning_dict = {
        "Russia",
        "Russian",
        "Russians",
        "Ukraine",
        "Ukrainian",
        "Ukrainians"
    }

    with open(f) as fp:
         for i in fp:
             i = i.strip()
             if len(i)<1 or i.startswith("####"):
                 continue
             s,p,*rest = i.split(" ")
             # s,p,o,*rest = i.split("\t")
             o = " ".join(rest)[:-2]
             triple = tuple((s,p,o))
             for w in warning_dict:
                 if w in s:
                     print((s,p,o))
                 if w in p:
                     print((s,p,o))
                 if w in o:
                     print((s,p,o))

if __name__ == "__main__":
    counter = 0
    for root,dirs,files in os.walk("/nfs/raid68/u15/ears/expts/47859.25k.approach.a.080620.v1/expts/hume_test.080620.cx.v1/serialization"):
        for file in files:
            if file.endswith(".nt"):
                main(os.path.join(root,file))
                counter+=1
                # if counter>400:
                #     exit(0)