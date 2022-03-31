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


def get_marked_up_string_for_event(kb_event):
    marked_up_starting_points_to_cnt = dict()
    marked_up_ending_points_to_cnt = dict()
    kb_sentence = None
    for kb_event_mention in kb_event.event_mentions:
        if kb_sentence is None:
            kb_sentence = kb_event_mention.sentence
        else:
            # Only within sentence event please
            assert kb_sentence == kb_event_mention.sentence
        start_char_off = kb_event_mention.trigger_start - kb_sentence.start_offset
        end_char_off = kb_event_mention.trigger_end - kb_sentence.start_offset
        marked_up_starting_points_to_cnt[start_char_off] = marked_up_starting_points_to_cnt.get(start_char_off, 0) + 1
        marked_up_ending_points_to_cnt[end_char_off] = marked_up_ending_points_to_cnt.get(end_char_off, 0) + 1

    ret = ""
    for c_idx, c in enumerate(kb_sentence.text):
        s = ""
        for _ in range(marked_up_starting_points_to_cnt.get(c_idx, 0)):
            s = "<span class=\"slot0\">" + s
        s = s + c
        for _ in range(marked_up_ending_points_to_cnt.get(c_idx, 0)):
            s = s + "</span>"
        ret = ret + s
    return ret


class Node(object):
    def __init__(self, node_id):
        self.node_id = node_id
        self._cnt = 0
        self.examples = set()

    @property
    def node_name(self):
        return self._node_name

    @node_name.setter
    def node_name(self, val):
        self._node_name = val

    @property
    def node_type(self):
        return self._node_type

    @node_type.setter
    def node_type(self, val):
        self._node_type = val

    @property
    def cnt(self):
        return self._cnt

    def increse_cnt(self):
        self._cnt += 1

    def put_example(self, example, max_examples_per_elem):
        if len(self.examples) < max_examples_per_elem:
            self.examples.add(example)

    def to_dict(self):
        return {
            "node_name": self._node_name,
            "node_type": self._node_type,
            "cnt": self._cnt,
            "node_id": self.node_id,
            "examples": list(self.examples)
        }


class Edge(object):
    def __init__(self, left_node, right_node, edge_name, edge_type):
        self.left_node = left_node
        self.right_node = right_node
        self.edge_name = edge_name
        self.edge_type = edge_type
        self._cnt = 0
        self.examples = set()

    @property
    def cnt(self):
        return self._cnt

    def increse_cnt(self):
        self._cnt += 1

    def to_dict(self):
        return {
            "left_node_id": self.left_node.node_id,
            "right_node_id": self.right_node.node_id,
            "edge_name": self.edge_name,
            "edge_type": self.edge_type,
            "cnt": self._cnt,
            "examples": list(self.examples)
        }

    def put_example(self, example, max_examples_per_elem):
        if len(self.examples) < max_examples_per_elem:
            self.examples.add(example)


class VisualizationSerializer:
    location_properties = {"state", "best_location_method"}
    time_properties = {"best_month", "best_month_method"}

    def __init__(self):
        self.max_examples_per_elem = 10

    def handle_eer(self, left_em_types, relation_type, right_em_types, trigger_node_left, trigger_node_right, node_type,
                   edge_type, unification_link, unification_relation_type, unification_type, left_kb_evt, right_kb_evt,
                   kb_relation):
        # Process event type correctly
        for left_em_type in left_em_types:
            for right_em_type in right_em_types:
                left_node_id = "{}_{}".format(node_type, left_em_type)
                node_for_left = self.node_id_to_nodes.setdefault(left_node_id,
                                                                 Node(left_node_id))
                node_for_left.node_name = left_em_type
                node_for_left.node_type = "{}".format(node_type)
                node_for_left.increse_cnt()
                node_for_left.put_example(get_marked_up_string_for_event(left_kb_evt), self.max_examples_per_elem)

                right_node_id = "{}_{}".format(node_type, right_em_type)
                node_for_right = self.node_id_to_nodes.setdefault(right_node_id,
                                                                  Node(right_node_id))
                node_for_right.node_name = right_em_type
                node_for_right.node_type = "{}".format(node_type)
                node_for_right.increse_cnt()
                node_for_right.put_example(get_marked_up_string_for_event(right_kb_evt), self.max_examples_per_elem)

                edge = self.edge_id_to_edges.setdefault((node_for_left, node_for_right, relation_type, edge_type),
                                                        Edge(node_for_left, node_for_right, relation_type, edge_type))
                edge.increse_cnt()
                edge.put_example(get_marked_up_string_for_event_event_relation(kb_relation, left_kb_evt, right_kb_evt),
                                 self.max_examples_per_elem)

                # Build Unify edge
                if unification_link is True:
                    unify_left = self.edge_id_to_edges.setdefault(
                        (node_for_left, trigger_node_left, unification_relation_type, unification_type),
                        Edge(node_for_left, trigger_node_left, unification_relation_type, unification_type))
                    unify_left.increse_cnt()
                    unify_left.put_example(get_marked_up_string_for_event(left_kb_evt), self.max_examples_per_elem)

                    unify_right = self.edge_id_to_edges.setdefault(
                        (node_for_right, trigger_node_right, unification_relation_type, unification_type),
                        Edge(node_for_right, trigger_node_right, unification_relation_type, unification_type))
                    unify_right.increse_cnt()
                    unify_right.put_example(get_marked_up_string_for_event(right_kb_evt), self.max_examples_per_elem)

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
                                logger.warning("Illegal assumed time {} {} {}".format(year,month,1))
                                continue
                        else:
                            assumed_time = None
                    assumed_source = list()
                    for conceiver_entity, _ in kb_event_mention.conceivers:
                        if type(conceiver_entity) is KBEntity:
                            if conceiver_entity.conceiver_entity_links is not None:
                                assumed_source.extend(conceiver_entity.conceiver_entity_links)
                        elif type(conceiver_entity) is str:
                            assumed_source.append(conceiver_entity)  # "AUTHOR_NODE"
                        else:
                            raise TypeError(type(conceiver_entity))

                    if assumed_time is not None and assumed_us_state is not None:
                        assumed_us_state_names = list(set(state_tuple[0] for state_tuple in assumed_us_state))
                        state_spans = list(set((state_tuple[1], state_tuple[2]) for state_tuple in assumed_us_state))
                        # event_type
                        for event_type, score in kb_event_mention.external_ontology_sources:
                            event_frame_json = {
                                "event_mention_id": "{}_{}".format(kb_event_mention.id, event_type),
                                "doc_id": kb_event_mention.document.id,
                                "sentence_id": kb_event_mention.sentence.id,
                                "sentence_start_char_off": kb_event_mention.sentence.start_offset,
                                "sentence_end_char_off": kb_event_mention.sentence.end_offset,
                                "sentence_original_text": kb_event_mention.sentence.original_text,
                                "event_type": event_type,
                                "event_mention_start_char_off": kb_event_mention.trigger_start,
                                "event_mention_end_char_off": kb_event_mention.trigger_end,
                                "assumed_time": assumed_time.timestamp(),
                                "assumed_location": assumed_us_state_names,
                                "assumed_time_method": kb_event_mention.properties.get("best_month_method", None),
                                "assumed_location_method": kb_event_mention.properties.get("best_location_method",
                                                                                           None),
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
                        # factor_type
                        for kb_causal_factor in kb_event_mention.causal_factors:
                            event_frame_json = {
                                "event_mention_id": "{}_{}".format(kb_event_mention.id, kb_causal_factor.factor_class),
                                "doc_id": kb_event_mention.document.id,
                                "sentence_id": kb_event_mention.sentence.id,
                                "sentence_start_char_off": kb_event_mention.sentence.start_offset,
                                "sentence_end_char_off": kb_event_mention.sentence.end_offset,
                                "sentence_original_text": kb_event_mention.sentence.original_text,
                                "event_type": kb_causal_factor.factor_class,
                                "event_mention_start_char_off": kb_event_mention.trigger_start,
                                "event_mention_end_char_off": kb_event_mention.trigger_end,
                                "assumed_time": assumed_time.timestamp(),
                                "assumed_location": assumed_us_state_names,
                                "assumed_time_method": kb_event_mention.properties.get("best_month_method", None),
                                "assumed_location_method": kb_event_mention.properties.get("best_location_method",
                                                                                           None),
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
        self.node_id_to_nodes = dict()
        self.edge_id_to_edges = dict()
        for relid, kb_relation in self.kb.relid_to_kb_relation.items():
            if kb_relation.argument_pair_type == "event-event":
                relation_type = kb_relation.relation_type
                left_kb_evt = self.kb.evid_to_kb_event[kb_relation.left_argument_id]
                right_kb_evt = self.kb.evid_to_kb_event[kb_relation.right_argument_id]
                for left_kb_em in left_kb_evt.event_mentions:
                    for right_kb_em in right_kb_evt.event_mentions:
                        # Create phrase phrase relation
                        # left_trigger = left_kb_em.trigger
                        # right_trigger = right_kb_em.trigger
                        # left_node_id = "trigger_{}".format(left_trigger)
                        # node_for_left = self.node_id_to_nodes.setdefault(left_node_id,Node(left_node_id))
                        # node_for_left.node_name = left_trigger
                        # node_for_left.node_type = "trigger"
                        # node_for_left.increse_cnt()
                        # node_for_left.put_example(get_marked_up_string_for_event(left_kb_evt),self.max_examples_per_elem)
                        #
                        # right_node_id = "trigger_{}".format(right_trigger)
                        # node_for_right = self.node_id_to_nodes.setdefault(right_node_id,Node(right_node_id))
                        # node_for_right.node_name = right_trigger
                        # node_for_right.node_type = "trigger"
                        # node_for_right.increse_cnt()
                        # node_for_right.put_example(get_marked_up_string_for_event(right_kb_evt),self.max_examples_per_elem)
                        #

                        # edge = self.edge_id_to_edges.setdefault((node_for_left,node_for_right,relation_type,"trigger_trigger_relation"),Edge(node_for_left,node_for_right,relation_type,"trigger_trigger_relation"))
                        # edge.increse_cnt()
                        # edge.put_example(get_marked_up_string_for_event_event_relation(kb_relation,left_kb_evt,right_kb_evt),self.max_examples_per_elem)

                        # Create grounding grounding relation
                        self.handle_eer((i[0] for i in left_kb_em.external_ontology_sources), relation_type,
                                        (i[0] for i in right_kb_em.external_ontology_sources), None, None,
                                        "event_grounding", "event_grounding_event_grounding_relation", False, "unifies",
                                        "unifies", left_kb_evt, right_kb_evt, kb_relation)
                        self.handle_eer((i.factor_class for i in left_kb_em.causal_factors), relation_type,
                                        (i.factor_class for i in right_kb_em.causal_factors), None, None,
                                        "factor_grounding", "factor_grounding_factor_grounding_relation", False,
                                        "unifies", "unifies", left_kb_evt, right_kb_evt, kb_relation)
        self.write_eer_graph(os.path.join(output_dir, 'output_eer.json'))
        self.serialize_event_frames(os.path.join(output_dir, 'output_event_frame.ljson'))
        return

    def write_eer_graph(self, output_graph_file):
        nodes = [node.to_dict() for node in self.node_id_to_nodes.values()]
        edges = [edge.to_dict() for edge in self.edge_id_to_edges.values()]
        with open(output_graph_file, 'w') as fp:
            json.dump({"nodes": nodes, "edges": edges}, fp, indent=4, sort_keys=True, ensure_ascii=False)
