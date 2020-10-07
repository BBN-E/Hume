import os

def main(f):

    s_triple = dict()
    p_triple = dict()
    o_triple = dict()

    with open(f) as fp:
         for i in fp:
             i = i.strip()
             if len(i)<1 or i.startswith("####"):
                 continue
             s,p,*rest = i.split(" ")
             # s,p,o,*rest = i.split("\t")
             o = " ".join(rest)[:-2]
             triple = tuple((s,p,o))
             s_triple.setdefault(s,list()).append(triple)
             p_triple.setdefault(p,list()).append(triple)
             o_triple.setdefault(o,list()).append(triple)
    causal_ids = set()
    for p in p_triple.keys():
        if "CauseEffect#has_effect" in p:
            causal_ids.update([i[0] for i in p_triple[p]])
    for causal_id in causal_ids:
        src_evt = None
        dst_evt = None
        polarity = None
        ca_type = None
        for s,p,o in s_triple[causal_id]:
            if "CauseEffect#has_effect" in p:
                dst_evt = o
            if p.split("/")[-1].split(">")[0] in {"CauseEffect#has_cause","CauseEffect#has_mitigating_factor","CauseEffect#has_catalyst","CauseEffect#has_precondition","CauseEffect#has_preventative"}:
                src_evt = o
                ca_type = p
            if "polarity" in p:
                polarity = o
        src_icm = list()
        dst_icm = list()
        src_polarity = None
        dst_polarity = None
        left_event_desc = None
        right_event_desc = None
        for s,p,o in s_triple[src_evt]:
            if "#description" in p:
                left_event_desc = o
            if "ICM#has_factor" in p:
                trend = None
                icm_type = None
                for s,p,o in s_triple[o]:
                    if "has_trend" in p:
                        trend = o
                    if "#has_factor_type" in p:
                        icm_type = o
                src_icm.append([icm_type,trend])
            if "has_polarity" in p:
                src_polarity = o
        for s,p,o in s_triple[dst_evt]:
            if "#description" in p:
                right_event_desc = o
            if "ICM#has_factor" in p:
                trend = None
                icm_type = None
                for s,p,o in s_triple[o]:
                    if "has_trend" in p:
                        trend = o
                    if "#has_factor_type" in p:
                        icm_type = o
                dst_icm.append([icm_type,trend])
            if "has_polarity" in p:
                dst_polarity = o
        if len(src_icm) > 0 and len(dst_icm) > 0:
            # print("CA polarity: {}".format(polarity))
            print("CA type: {}".format(ca_type))
            print("Left: {} polarity: {}".format(left_event_desc,src_polarity))
            for i in src_icm:
                print("type: {} trend: {}".format(i[0],i[1]))
            print("Right {} polarity: {}".format(right_event_desc,dst_polarity))
            for i in dst_icm:
                print("type: {} trend: {}".format(i[0],i[1]))
            print("#####################")

if __name__ == "__main__":
    # f = "/d4m/ears/expts/47837.072720.v2/expts/hume_test.041420.cx.v1/serialization/2940cffcd9bf2689dd51f3ef2aa26248/output.nt"
    # f = "/home/hqiu/isi2.nt"
    # f = "/home/hqiu/lcc.nt"
    f = "/home/hqiu/bbn.nt"
    for root,dirs,files in os.walk("/home/hqiu/ld100/Hume_pipeline_int/Hume/expts/hume_test.073120.cx.v3/serialization"):
    # for root,dirs,files in os.walk("/home/hqiu/tmp/serialization_test/"):
        for file in files:
            if file.endswith(".nt"):
                main(os.path.join(root,file))