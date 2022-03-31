import datetime
import json
import logging
import os
import re

from elements.kb_entity import KBEntity

logger = logging.getLogger(__name__)
whitespace_re = re.compile(r"\s+")


def get_marked_up_string_for_event_event_relation(kb_relation, left_kb_event, right_kb_event):
    relation_type = kb_relation.relation_type
    left_marked_up_starting_points_to_cnt = dict()
    left_marked_up_ending_points_to_cnt = dict()
    right_marked_up_starting_points_to_cnt = dict()
    right_marked_up_ending_points_to_cnt = dict()
    kb_sentence_left = None
    kb_sentence_right = None
    left_trigger = None
    right_trigger = None
    for left_kb_event_mention in left_kb_event.event_mentions:
        if kb_sentence_left is None:
            kb_sentence_left = left_kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence_left == left_kb_event_mention.sentence
        start_char_off = left_kb_event_mention.trigger_start - kb_sentence_left.start_offset
        end_char_off = left_kb_event_mention.trigger_end - kb_sentence_left.start_offset
        left_marked_up_starting_points_to_cnt[start_char_off] = left_marked_up_starting_points_to_cnt.get(
            start_char_off, 0) + 1
        left_marked_up_ending_points_to_cnt[end_char_off] = left_marked_up_ending_points_to_cnt.get(end_char_off, 0) + 1
        left_trigger = left_kb_event_mention.trigger
    for right_kb_event_mention in right_kb_event.event_mentions:
        if kb_sentence_right is None:
            kb_sentence_right = right_kb_event_mention.sentence
        else:
            assert kb_sentence_right == right_kb_event_mention.sentence
        start_char_off = right_kb_event_mention.trigger_start - kb_sentence_right.start_offset
        end_char_off = right_kb_event_mention.trigger_end - kb_sentence_right.start_offset
        right_marked_up_starting_points_to_cnt[start_char_off] = right_marked_up_starting_points_to_cnt.get(
            start_char_off, 0) + 1
        right_marked_up_ending_points_to_cnt[end_char_off] = right_marked_up_ending_points_to_cnt.get(end_char_off,
                                                                                                      0) + 1
        right_trigger = right_kb_event_mention.trigger
    ret = ""
    if kb_sentence_left == kb_sentence_right:
        for c_idx, c in enumerate(kb_sentence_left.text):
            s = ""
            for _ in range(left_marked_up_starting_points_to_cnt.get(c_idx, 0)):
                s = "<span class=\"slot0\">" + s
            for _ in range(right_marked_up_starting_points_to_cnt.get(c_idx, 0)):
                s = "<span class=\"slot1\">" + s
            s = s + c
            for _ in range(left_marked_up_ending_points_to_cnt.get(c_idx, 0)):
                s = s + "</span>"
            for _ in range(right_marked_up_ending_points_to_cnt.get(c_idx, 0)):
                s = s + "</span>"
            ret = ret + s
    else:
        for c_idx, c in enumerate(kb_sentence_left.text):
            s = ""
            for _ in range(left_marked_up_starting_points_to_cnt.get(c_idx, 0)):
                s = "<span class=\"slot0\">" + s
            s = s + c
            for _ in range(left_marked_up_ending_points_to_cnt.get(c_idx, 0)):
                s = s + "</span>"
            ret = ret + s
        for c_idx, c in enumerate(kb_sentence_right.text):
            s = ""
            for _ in range(right_marked_up_starting_points_to_cnt.get(c_idx, 0)):
                s = "<span class=\"slot1\">" + s
            s = s + c
            for _ in range(right_marked_up_ending_points_to_cnt.get(c_idx, 0)):
                s = s + "</span>"
            ret = ret + s
    return ret


def mark_up_sentence_for_event_and_location(original_str, sent_start_char_off, start_offs_to_markings,
                                            end_offs_to_markings):
    ret = ""
    for idx, c in enumerate(original_str):
        s = ""
        if idx + sent_start_char_off in start_offs_to_markings:
            for marking in start_offs_to_markings[idx + sent_start_char_off]:
                s = s + "<span class=\"{}\">".format(marking)
        s = s + c
        if idx + sent_start_char_off in end_offs_to_markings:
            for marking in end_offs_to_markings[idx + sent_start_char_off]:
                s = s + "</span>"
        ret = ret + s
    return ret


class FillableTCAGSerializer:
    location_properties = {"state", "best_location_method"}
    time_properties = {"best_month", "best_month_method"}

    def __init__(self):
        pass

    def serialize_event_frames(self, output_path):
        with open(output_path, 'w') as wfp:
            for evid, kb_event in self.kb.get_events():
                for kb_event_mention in kb_event.event_mentions:
                    # Handle location
                    assumed_us_state = kb_event_mention.properties.get("state", None)
                    best_location_method_is_sentence = True if kb_event_mention.properties.get("best_location_method",
                                                                                               None) == "sentence" else False
                    best_location_method_is_argument = True if kb_event_mention.properties.get("best_location_method",
                                                                                               None) == "argument" else False

                    best_time_method_is_document = True if kb_event_mention.properties.get("best_month_method",
                                                                                           None) == "document" else False
                    best_time_method_is_sentence = True if kb_event_mention.properties.get("best_month_method",
                                                                                           None) == "sentence" else False
                    best_time_method_is_argument = True if kb_event_mention.properties.get("best_month_method",
                                                                                           None) == "argument" else False
                    assumed_time = kb_event_mention.properties.get("best_month", None)
                    if assumed_time is None:
                        if len(kb_event_mention.timexps) > 0:
                            assumed_time = kb_event_mention.timexps[-1][0]  # get immediate parent timex
                            if assumed_time.count("-") != 1:
                                logger.warning("Illegal assumed_time {}".format(assumed_time))
                                assumed_time = None
                    if assumed_time is not None:
                        year, month = assumed_time.split("-")
                        year = int(year)
                        month = int(month)
                        if month >= 1 and month <= 12:
                            try:
                                assumed_time = datetime.datetime(year=year, month=month, day=1)
                            except ValueError as e:
                                logger.warning("Illegal assumed time {} {} {}".format(year, month, 1))
                                continue
                        else:
                            assumed_time = None
                    assumed_source = list()
                    for conceiver_entity, _ in kb_event_mention.conceivers:
                        if type(conceiver_entity) is KBEntity:
                            if conceiver_entity.canonical_name is not None:
                                assumed_source.append(conceiver_entity.canonical_name)
                            else:
                                longest_name = ""
                                for mention in conceiver_entity.mentions:
                                    mention_head_text = mention.mention_head_text
                                    if len(mention_head_text) > len(longest_name):
                                        longest_name = mention_head_text
                                if len(longest_name) > 0:
                                    assumed_source.append(longest_name)
                        elif type(conceiver_entity) is str:
                            assumed_source.append(conceiver_entity)
                        else:
                            raise TypeError(type(conceiver_entity))

                    if assumed_time is not None and assumed_us_state is not None:
                        assumed_us_state_names = list(set(state_tuple[0] for state_tuple in assumed_us_state))
                        state_spans = list(set((state_tuple[1], state_tuple[2]) for state_tuple in assumed_us_state))
                        event_frame_json = {
                            "event_mention_id": "{}".format(kb_event_mention.id),
                            "doc_id": kb_event_mention.document.id,
                            "sentence_start_char_off": kb_event_mention.sentence.start_offset,
                            "sentence_end_char_off": kb_event_mention.sentence.end_offset,
                            "event_mention_start_char_off": kb_event_mention.trigger_start,
                            "event_mention_end_char_off": kb_event_mention.trigger_end,
                            "sentence_original_text": kb_event_mention.sentence.original_text,
                            "sent_no": kb_event_mention.sentence.sent_no,
                            "sentence_start_token_idx": kb_event_mention.trigger_start_token_idx,
                            "sentence_end_token_idx": kb_event_mention.trigger_end_token_idx,
                            "assumed_time": assumed_time.timestamp(),
                            "assumed_location": assumed_us_state_names,
                            "assumed_source": assumed_source,
                            "aux_spans": {
                                "state": state_spans
                            }
                        }
                        start_off_to_mark = dict()
                        end_off_to_mark = dict()
                        start_off_to_mark.setdefault(event_frame_json['event_mention_start_char_off'],
                                                     list()).append("slot0")
                        end_off_to_mark.setdefault(event_frame_json['event_mention_end_char_off'], list()).append(
                            "slot0")
                        for start_char_off, end_char_off in event_frame_json.get("aux_spans", dict()).get("state",
                                                                                                          ()):
                            start_off_to_mark.setdefault(start_char_off, list()).append("statelocation")
                            end_off_to_mark.setdefault(end_char_off, list()).append("statelocation")
                        event_frame_json['sentence_markup_text'] = mark_up_sentence_for_event_and_location(
                            event_frame_json['sentence_original_text'],
                            event_frame_json['sentence_start_char_off'],
                            start_off_to_mark, end_off_to_mark)
                        wfp.write("{}\n".format(json.dumps(event_frame_json, ensure_ascii=False)))

    def serialize(self, kb, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        self.kb = kb
        with open(os.path.join(output_dir, 'output_eer.info'), 'w') as eer_edges:
            for relid, kb_relation in self.kb.relid_to_kb_relation.items():
                if kb_relation.argument_pair_type == "event-event":
                    relation_type = kb_relation.relation_type
                    left_kb_evt = self.kb.evid_to_kb_event[kb_relation.left_argument_id]
                    right_kb_evt = self.kb.evid_to_kb_event[kb_relation.right_argument_id]
                    marked_up_string_eerm = get_marked_up_string_for_event_event_relation(kb_relation, left_kb_evt,
                                                                                          right_kb_evt)
                    for left_kb_em in left_kb_evt.event_mentions:
                        for right_kb_em in right_kb_evt.event_mentions:
                            left_doc_id = left_kb_em.document.id
                            left_sent_no = left_kb_em.sentence.sent_no
                            left_start_token_idx = left_kb_em.trigger_start_token_idx
                            left_end_token_idx = left_kb_em.trigger_end_token_idx

                            right_doc_id = right_kb_em.document.id
                            right_sent_no = right_kb_em.sentence.sent_no
                            right_start_token_idx = right_kb_em.trigger_start_token_idx
                            right_end_token_idx = right_kb_em.trigger_end_token_idx
                            eer_edges.write("{}\n".format(json.dumps([
                                "{}#{}#{}#{}".format(left_doc_id, left_sent_no, left_start_token_idx,
                                                     left_end_token_idx), relation_type,
                                "{}#{}#{}#{}".format(right_doc_id, right_sent_no, right_start_token_idx,
                                                     right_end_token_idx),
                                marked_up_string_eerm
                            ], ensure_ascii=False)))
        self.serialize_event_frames(os.path.join(output_dir, 'output_empty_event_frame.ljson'))
        return
