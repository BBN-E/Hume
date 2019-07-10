import sys, os, codecs
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from unidecode import unidecode

class RedundantRelationResolver(KBResolver):
    def __init__(self):
        pass

    def resolve(self, kb):
        print "RedundantRelationResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(RedundantRelationResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_relations_and_relation_groups()

        # Organize old relation mentions by sentence
        sentences_to_relation_mention_list = dict()
        relation_mention_to_relation = dict()
        for relid, relation in kb.get_relations():
            if relation.argument_pair_type != "event-event":
                continue
            
            for relation_mention in relation.relation_mentions:
                relation_mention_to_relation[relation_mention] = relation
                left_sentence = relation_mention.left_mention.sentence
                right_sentence = relation_mention.right_mention.sentence
                k = (left_sentence, right_sentence,)
                if k not in sentences_to_relation_mention_list:
                    sentences_to_relation_mention_list[k] = []
                sentences_to_relation_mention_list[k].append(relation_mention)

        relation_mentions_to_remove = set()
        for sentence_pair, relation_mention_list in sentences_to_relation_mention_list.iteritems():
            # Essentially looking at the relations mentions for a particular sentence here
            for rm1 in relation_mention_list:
                for rm2 in relation_mention_list:
                    if rm1 == rm2:
                        continue

                    r1 = relation_mention_to_relation[rm1]
                    r2 = relation_mention_to_relation[rm2]
                    
                    if rm1.is_similar_and_better_than(rm2, r1.relation_type, r2.relation_type):
                        #print "Throwing out: " + rm2.id + " because it's worse than: " + rm1.id
                        relation_mentions_to_remove.add(rm2)

        for relid, relation in kb.get_relations():
            found_good_relation_mention = False
            for relation_mention in relation.relation_mentions:
                if relation_mention not in relation_mentions_to_remove:
                    found_good_relation_mention = True
                    break
            if found_good_relation_mention:
                resolved_kb.add_relation(relation)

        return resolved_kb

    # DEBUG PRINTING FUNCTIONS
    def output_remaining_relation_mentions(self, kb, o, relations_to_remove):
        sentences_to_relation_mention_list = dict()
        relation_mention_to_relation = dict()
        for relid, relation in kb.get_relations():
            if relation.argument_pair_type != "event-event":
                continue
            if relation in relations_to_remove:
                continue
            
            for relation_mention in relation.relation_mentions:
                relation_mention_to_relation[relation_mention] = relation
                left_sentence = relation_mention.left_mention.sentence
                right_sentence = relation_mention.right_mention.sentence
                k = (left_sentence, right_sentence,)
                if k not in sentences_to_relation_mention_list:
                    sentences_to_relation_mention_list[k] = []
                sentences_to_relation_mention_list[k].append(relation_mention)
       
        for sentence_pair, relation_mention_list in sentences_to_relation_mention_list.iteritems():
            o.write("------------------------------------------------------------\n")
            num_relation_mentions = len(relation_mention_list)
            
            o.write(sentence_pair[0].id + " " + sentence_pair[1].id  + "\n" + str(num_relation_mentions) + "\n")

            o.write(unidecode(sentence_pair[0].text) + "\n")
            if sentence_pair[1] != sentence_pair[0]:
                o.write(unidecode(sentence_pair[1].text) + "\n")

            for relation_mention in relation_mention_list:
                relation = relation_mention_to_relation[relation_mention]
                self.output_relation_mention_info(relation_mention, relation, o)
                if relation_mention != relation_mention_list[-1]:
                    o.write("-----------\n")
    def output_relation_mention_info(self, relation_mention, relation, o):
        o.write(relation_mention.properties["model"] + "." + relation.relation_type + " " +
                relation_mention.left_mention.model + "." +
                relation_mention.left_mention.event_type + " / " +
                relation_mention.right_mention.model + "." +
                relation_mention.right_mention.event_type + "\n")
        o.write(relation_mention.id + "\n")
        o.write(str(relation_mention.left_mention.trigger) + " / " + str(relation_mention.right_mention.trigger) + "\n")

                    
    # Currently not used because this should be the job of patterns not to
    # output relations where one is the reverse of another
    def reverse_relation_test_discard(self, relation_mention, rm_list):
        matching_order = [relation_mention]
        reverse_order = []

        left_trigger = relation_mention.left_mention.trigger
        right_trigger = relation_mention.right_mention.trigger

        if left_trigger is None or right_trigger is None:
            return False
        
        for rm in rm_list:
            if rm == relation_mention:
                continue
            if left_trigger == rm.left_mention.trigger and right_trigger == rm.right_mention.trigger:
                matching_order.append(rm)
            if left_trigger == rm.right_mention.trigger and right_trigger == rm.left_mention.trigger:
                reverse_order.append(rm)

        return len(reverse_order) > len(matching_order)
        
