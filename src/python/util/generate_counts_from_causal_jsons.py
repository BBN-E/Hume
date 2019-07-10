import os,sys,json

reln_type_table = {"catalyst": "Catalyst-Effect",
                   "cause": "Cause-Effect",
                   "mitigating_factor": "MitigatingFactor-Effect",
                   "precondition": "Precondition-Effect",
                   "preventative": "Preventative-Effect"
                   }

triple2sentences = dict()

def main(input_list_json_files):
    list_input_json = list()
    with open(input_list_json_files,'r') as fp:
        for i in fp:
            i = i.strip()
            if ".json" in i:
                print ("Loading " + i)

                with open(i) as i_data:
                    data = i_data.read()

                    objs = json.loads(data)
                    for obj in objs:

                        reln_type = "NA"
                        confidence = 0
                        for type in obj["frame_types"]:
                            reln_type = type
                            confidence = obj["frame_types"][type]

                        left_role = None
                        left_text = None
                        left_type = None

                        right_text = None
                        right_type = None

                        for arg in obj["arguments"]:
                            role = arg["role"]
                            trigger_text = arg["frame"]["evidence"]["trigger"]["text"]

                            event_type = "NA"
                            for t in arg["frame"]["frame_types"]:
                                event_type = t[t.find("#")+1:]

                            if "has_effect" in role:
                                right_text = trigger_text
                                right_type = event_type
                            else:
                                left_role = role[role.find("#has_")+5:]
                                left_text = trigger_text
                                left_type = event_type

                        sentence = obj["evidence"]["sentence"]["text"]

                        reln_type = reln_type_table[left_role]

                        print (str(confidence) + "\t" + left_type + "\t" + right_type + "\t" + get_headword(left_text) + "\t" + reln_type + "\t" + get_headword(right_text) + "\t" + sentence)

                        triple = get_headword(left_text) + "\t" + reln_type + "\t" + get_headword(right_text)

                        triple2sentences.setdefault(triple, set()).add(sentence)

def get_headword(text):
    items = text.strip().split(" ")
    return items[len(items)-1]

if __name__ == "__main__":
    input_list_json_files = "/nfs/ld100/u10/bmin/temp/list_scs_unification_json"
    main(input_list_json_files)
    #
    # key_set = sorted(list(triple2sentences.keys()),key=lambda x:len(triple2sentences[x]),reverse=True)
    # print()
    # print()
    # print("================")
    #
    # for k in key_set:
    #     print()
    #     sentences = triple2sentences[k]
    #     cnt = 0
    #     for sentence in sentences:
    #         print("{}\t{}\t{}".format(len(sentences),k,sentence))
    #         cnt+=1
    #         if cnt>5:
    #             break