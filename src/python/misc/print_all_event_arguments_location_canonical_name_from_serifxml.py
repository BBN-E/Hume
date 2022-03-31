import os,sys,enum

import serifxml3


def single_document_hanlder(serif_path):
    serif_doc = serifxml3.Document(serif_path)
    ret = list()
    mention_to_entities = dict()
    for entity in serif_doc.entity_set or ():
        for mention in entity.mentions:
            mention_to_entities.setdefault(mention,set()).add(entity)
    entity_to_actor_entity_cache = serif_doc.get_entity_to_actor_entity_cache()
    for sent_idx,sentence in enumerate(serif_doc.sentences):
        sentence_theory = sentence.sentence_theory
        for event_mention in sentence_theory.event_mention_set or ():
            for argument in event_mention.arguments or ():
                if argument.role in {"has_location", "has_origin_location", "has_destination_location", "Place", "Origin", "Destination"}:
                    if isinstance(argument.mention, serifxml3.Mention):
                        canonical_name = None
                        for entity in mention_to_entities.get(argument.mention,()):
                            actor_entity = entity_to_actor_entity_cache.get(entity,None)
                            if actor_entity is not None:
                                canonical_name = actor_entity.actor_name + ""
                                ret.append("{}".format(canonical_name))
                                break
    return ret


def main(serif_list,output_path):
    with open(serif_list) as fp,open(output_path,'w') as wfp:
        for i in fp:
            i = i.strip()
            buf = single_document_hanlder(i)
            for i in buf:
                wfp.write("{}\n".format(i))


if __name__ == "__main__":
    import sys
    main(sys.argv[1],sys.argv[2])
