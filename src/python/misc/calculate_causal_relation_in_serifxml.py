import collections

import serifxml3


EventEventRelation = collections.namedtuple('EventEventRelation',['docid','left_start','left_end','relation','right_start','right_end'])



def generate_eer_set(file_list):
    with open(file_list) as fp:
        for i in fp:
            i = i.strip()
            serif_doc = serifxml3.Document(i)
            for event_event_relation in serif_doc.event_event_relation_mention_set or list():
                arguments = event_event_relation.event_mention_relation_arguments
                left_event_mention = None
                right_event_mention = None
                for argument in arguments:
                    if argument.role == "arg1":
                        left_event_mention = argument.event_mention
                    elif argument.role == "arg2":
                        right_event_mention = argument.event_mention
                    else:
                        pass
                # for left_anchor in left_event_mention.anchors:
                #     left_anchor_node = left_anchor.anchor_node
                #     for right_anchor in right_event_mention.anchors:
                #         right_anchor_node = right_anchor.anchor_node
                #         print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                #             left_anchor_node.text,
                #             event_event_relation.relation_type,
                #             right_anchor_node.text,
                #             serif_doc.docid,
                #             left_anchor_node.start_char,
                #             left_anchor_node.end_char,
                #             right_anchor_node.start_char,
                #             right_anchor_node.end_char))
                print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                    left_event_mention.anchor_node.text,
                    event_event_relation.relation_type,
                    right_event_mention.anchor_node.text,
                    serif_doc.docid,
                    left_event_mention.anchor_node.start_char,
                    left_event_mention.anchor_node.end_char,
                    right_event_mention.anchor_node.start_char,
                    right_event_mention.anchor_node.end_char))


def main():
    file_list = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/eer_test.092919.before/event_event_relations_serifxml.list"
    generate_eer_set(file_list)
    # print("#######################")
    # file_list = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/eer_test.092919.after/event_event_relations_serifxml.list"
    # generate_eer_set(file_list)


if __name__ == "__main__":
    main()