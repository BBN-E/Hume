import os
import serifxml3
import multiprocessing

def single_document_fixer(serifxml_path, output_serifxml_dir):
    serif_doc = serifxml3.Document(serifxml_path)
    event_mention_set = set()
    dropped_event_cnt = 0
    dropped_eer_cnt = 0
    for sentence in serif_doc.sentences:
        sentence_event_set = set()
        for event_mention in sentence.event_mention_set or ():
            if event_mention.anchor_node is not None:
                event_mention_set.add(event_mention)
                sentence_event_set.add(event_mention)
            else:
                dropped_event_cnt += 1
        if sentence.event_mention_set is not None:
            sentence.event_mention_set._children.clear()
            sentence.event_mention_set._children.extend(sentence_event_set)
    old_eerm_list = list()
    for serif_eerm in serif_doc.event_event_relation_mention_set or ():
        all_args_are_valid = True
        for arg in serif_eerm.event_mention_relation_arguments:
            if arg.event_mention not in event_mention_set:
                all_args_are_valid = False
                break
        if all_args_are_valid is True:
            old_eerm_list.append(serif_eerm)
        else:
            dropped_eer_cnt += 1
    serif_eerm_set = serif_doc.add_new_event_event_relation_mention_set()
    for old_eerm in old_eerm_list:
        eerm = serif_eerm_set.add_new_event_event_relation_mention(
            old_eerm.relation_type, 1.0, "LDC")
        for arg in old_eerm.event_mention_relation_arguments:
            eerm.add_new_event_mention_argument(arg.role,arg.event_mention)
    print("{} dropped {} events {} eers".format(serif_doc.docid,dropped_event_cnt,dropped_eer_cnt))
    serif_doc.save(os.path.join(output_serifxml_dir, "{}.xml".format(serif_doc.docid)))


def main():
    input_list = "/nfs/raid88/u10/users/hqiu_ad/serifxml_corpus/gigaword_eer_training.v1.list"
    output_dir = "/nfs/raid88/u10/users/hqiu_ad/serifxml_corpus/gigaword_eer_training.v2/"
    manager = multiprocessing.Manager()
    with manager.Pool(multiprocessing.cpu_count()) as pool:
        workers = list()
        with open(input_list) as fp:
            for i in fp:
                i = i.strip()
                workers.append(pool.apply_async(single_document_fixer, args=(i,output_dir,)))
            for idx, i in enumerate(workers):
                print("Waiting {}".format(idx))
                i.wait()
                buf = i.get()


if __name__ == "__main__":
    main()
