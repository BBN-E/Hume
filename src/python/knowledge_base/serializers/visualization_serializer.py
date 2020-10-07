
import json

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
    for c_idx,c in enumerate(kb_sentence.text):
        s = ""
        for _ in range(left_marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "<span class=\"slot0\">" + s
        for _ in range(right_marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "<span class=\"slot1\">" + s
        s = s + c
        for _ in range(left_marked_up_ending_points_to_cnt.get(c_idx,0)):
            s = s + "</span>"
        for _ in range(right_marked_up_ending_points_to_cnt.get(c_idx,0)):
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
        start_char_off = kb_event_mention.trigger_start-kb_sentence.start_offset
        end_char_off = kb_event_mention.trigger_end-kb_sentence.start_offset
        marked_up_starting_points_to_cnt[start_char_off] = marked_up_starting_points_to_cnt.get(start_char_off,0)+1
        marked_up_ending_points_to_cnt[end_char_off] = marked_up_ending_points_to_cnt.get(end_char_off,0)+1

    ret = ""
    for c_idx,c in enumerate(kb_sentence.text):
        s = ""
        for _ in range(marked_up_starting_points_to_cnt.get(c_idx,0)):
            s = "<span class=\"slot0\">" + s
        s = s + c
        for _ in range(marked_up_ending_points_to_cnt.get(c_idx,0)):
            s = s + "</span>"
        ret = ret + s
    return ret

class Node(object):
    def __init__(self,node_id):
        self.node_id = node_id
        self._cnt = 0
        self.examples = set()

    @property
    def node_name(self):
        return self._node_name

    @node_name.setter
    def node_name(self,val):
        self._node_name = val

    @property
    def node_type(self):
        return self._node_type

    @node_type.setter
    def node_type(self,val):
        self._node_type = val

    @property
    def cnt(self):
        return self._cnt

    def increse_cnt(self):
        self._cnt += 1

    def put_example(self,example,max_examples_per_elem):
        if len(self.examples) < max_examples_per_elem:
            self.examples.add(example)

    def to_dict(self):
        return {
            "node_name":self._node_name,
            "node_type":self._node_type,
            "cnt":self._cnt,
            "node_id":self.node_id,
            "examples":list(self.examples)
        }

class Edge(object):
    def __init__(self,left_node,right_node,edge_name,edge_type):
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
            "left_node_id":self.left_node.node_id,
            "right_node_id":self.right_node.node_id,
            "edge_name":self.edge_name,
            "edge_type":self.edge_type,
            "cnt":self._cnt,
            "examples":list(self.examples)
        }

    def put_example(self,example,max_examples_per_elem):
        if len(self.examples) < max_examples_per_elem:
            self.examples.add(example)

class VisualizationSerializer:

    def __init__(self):
        self.max_examples_per_elem = 10


    def handle_eer(self,left_em_types,relation_type,right_em_types,trigger_node_left,trigger_node_right,node_type,edge_type,unification_link,unification_relation_type,unification_type,left_kb_evt,right_kb_evt,kb_relation):
        # Process event type correctly
        for left_em_type in left_em_types:
            for right_em_type in right_em_types:
                left_node_id = "{}_{}".format(node_type,left_em_type)
                node_for_left = self.node_id_to_nodes.setdefault(left_node_id,
                                                                 Node(left_node_id))
                node_for_left.node_name = left_em_type
                node_for_left.node_type = "{}".format(node_type)
                node_for_left.increse_cnt()
                node_for_left.put_example(get_marked_up_string_for_event(left_kb_evt), self.max_examples_per_elem)

                right_node_id = "{}_{}".format(node_type,right_em_type)
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
                    unify_left = self.edge_id_to_edges.setdefault((node_for_left,trigger_node_left,unification_relation_type,unification_type),Edge(node_for_left,trigger_node_left,unification_relation_type,unification_type))
                    unify_left.increse_cnt()
                    unify_left.put_example(get_marked_up_string_for_event(left_kb_evt),self.max_examples_per_elem)

                    unify_right = self.edge_id_to_edges.setdefault((node_for_right,trigger_node_right,unification_relation_type,unification_type),Edge(node_for_right,trigger_node_right,unification_relation_type,unification_type))
                    unify_right.increse_cnt()
                    unify_right.put_example(get_marked_up_string_for_event(right_kb_evt),self.max_examples_per_elem)




    def serialize(self, kb, output_graph_file):
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
                        left_trigger = left_kb_em.trigger
                        right_trigger = right_kb_em.trigger
                        left_node_id = "trigger_{}".format(left_trigger)
                        node_for_left = self.node_id_to_nodes.setdefault(left_node_id,Node(left_node_id))
                        node_for_left.node_name = left_trigger
                        node_for_left.node_type = "trigger"
                        node_for_left.increse_cnt()
                        node_for_left.put_example(get_marked_up_string_for_event(left_kb_evt),self.max_examples_per_elem)

                        right_node_id = "trigger_{}".format(right_trigger)
                        node_for_right = self.node_id_to_nodes.setdefault(right_node_id,Node(right_node_id))
                        node_for_right.node_name = right_trigger
                        node_for_right.node_type = "trigger"
                        node_for_right.increse_cnt()
                        node_for_right.put_example(get_marked_up_string_for_event(right_kb_evt),self.max_examples_per_elem)


                        edge = self.edge_id_to_edges.setdefault((node_for_left,node_for_right,relation_type,"trigger_trigger_relation"),Edge(node_for_left,node_for_right,relation_type,"trigger_trigger_relation"))
                        edge.increse_cnt()
                        edge.put_example(get_marked_up_string_for_event_event_relation(kb_relation,left_kb_evt,right_kb_evt),self.max_examples_per_elem)

                        # Create grounding grounding relation
                        self.handle_eer((i[0] for i in left_kb_em.external_ontology_sources),relation_type,(i[0] for i in right_kb_em.external_ontology_sources),node_for_left,node_for_right,"event_grounding","event_grounding_event_grounding_relation",True,"unifies","unifies",left_kb_evt,right_kb_evt,kb_relation)
                        self.handle_eer((i.factor_class for i in left_kb_em.causal_factors),relation_type,(i.factor_class for i in right_kb_em.causal_factors),node_for_left,node_for_right,"factor_grounding","factor_grounding_factor_grounding_relation",True,"unifies","unifies",left_kb_evt,right_kb_evt,kb_relation)
        self.write_graph(output_graph_file)
        return

    def write_graph(self, output_graph_file):
        nodes = [node.to_dict() for node in self.node_id_to_nodes.values()]
        edges = [edge.to_dict() for edge in self.edge_id_to_edges.values()]
        with open(output_graph_file,'w') as fp:
            json.dump({"nodes":nodes,"edges":edges},fp,indent=4,sort_keys=True,ensure_ascii=False)