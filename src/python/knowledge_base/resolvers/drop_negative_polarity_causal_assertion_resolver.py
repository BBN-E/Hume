import logging
from enum import Enum
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver


logger = logging.getLogger(__name__)

def get_marked_up_string_for_event_event_relation(kb_relation,left_kb_event,right_kb_event):
    relation_type = kb_relation.relation_type
    left_marked_up_starting_points_to_cnt = dict()
    left_marked_up_ending_points_to_cnt = dict()
    right_marked_up_starting_points_to_cnt = dict()
    right_marked_up_ending_points_to_cnt = dict()
    kb_sentence = None
    left_trigger = None
    right_trigger = None
    for left_kb_event_mention in left_kb_event.event_mentions:
        if kb_sentence is None:
            kb_sentence = left_kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence == left_kb_event_mention.sentence
        start_char_off = left_kb_event_mention.trigger_start-kb_sentence.start_offset
        end_char_off = left_kb_event_mention.trigger_end-kb_sentence.start_offset
        left_marked_up_starting_points_to_cnt[start_char_off] = left_marked_up_starting_points_to_cnt.get(start_char_off,0)+1
        left_marked_up_ending_points_to_cnt[end_char_off] = left_marked_up_ending_points_to_cnt.get(end_char_off,0)+1
        left_trigger = left_kb_event_mention.trigger
    for right_kb_event_mention in right_kb_event.event_mentions:
        if kb_sentence is None:
            kb_sentence = right_kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence == right_kb_event_mention.sentence
        start_char_off = right_kb_event_mention.trigger_start-kb_sentence.start_offset
        end_char_off = right_kb_event_mention.trigger_end-kb_sentence.start_offset
        right_marked_up_starting_points_to_cnt[start_char_off] = right_marked_up_starting_points_to_cnt.get(start_char_off,0)+1
        right_marked_up_ending_points_to_cnt[end_char_off] = right_marked_up_ending_points_to_cnt.get(end_char_off,0)+1
        right_trigger = right_kb_event_mention.trigger
    ret = ""
    for c_idx,c in enumerate(kb_sentence.original_text):
        s = ""
        for _ in range(left_marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "[[" + s
        for _ in range(right_marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "[[" + s
        s = s + c
        for _ in range(left_marked_up_ending_points_to_cnt.get(c_idx,0)):
            s = s + "]]"
        for _ in range(right_marked_up_ending_points_to_cnt.get(c_idx,0)):
            s = s + "]]"
        ret = ret + s
    return "left: {} , right: {} , sentence: {}".format(left_trigger,right_trigger,ret)

class DropNegativePolarityCausalAssertionResolver(KBResolver):
    def __init__(self):
        super(DropNegativePolarityCausalAssertionResolver, self).__init__()

    def resolve(self, kb):
        resolved_kb = KnowledgeBase()
        super(DropNegativePolarityCausalAssertionResolver, self).copy_all(resolved_kb, kb)
        new_relid_to_kb_relation = dict()
        for relid,kb_relation in resolved_kb.relid_to_kb_relation.items():
            if kb_relation.argument_pair_type != "event-event":
                new_relid_to_kb_relation[relid] = kb_relation
            elif kb_relation.polarity != "Negative":
                new_relid_to_kb_relation[relid] = kb_relation
            else:
                src_kb_event = resolved_kb.evid_to_kb_event[kb_relation.left_argument_id]
                tar_kb_event = resolved_kb.evid_to_kb_event[kb_relation.right_argument_id]
                logger.debug("NCA Dropping {}".format(get_marked_up_string_for_event_event_relation(kb_relation,src_kb_event,tar_kb_event)))
        resolved_kb.relid_to_kb_relation = new_relid_to_kb_relation
        return resolved_kb