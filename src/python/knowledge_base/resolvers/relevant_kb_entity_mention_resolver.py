from knowledge_base import KnowledgeBase
from elements.kb_mention import KBMention
from elements.kb_entity import KBEntity
from elements.kb_group import KBEntityGroup
from resolvers.kb_resolver import KBResolver

class RelevantKBEntityMentionResolver(KBResolver):

    def __init__(self):
        super(RelevantKBEntityMentionResolver,self).__init__()


    def mark_from_bottom_to_top(self,kb_element):
        if kb_element in self.marked_kb_elements:
            return
        if isinstance(kb_element,KBMention):
            kb_element.is_referred_in_kb = True
            self.marked_kb_elements.add(kb_element)
            self.mark_from_bottom_to_top(self.kb_entity_mention_to_kb_entity[kb_element])
        elif isinstance(kb_element,KBEntity):
            kb_element.is_referred_in_kb = True
            self.marked_kb_elements.add(kb_element)
            # Mark the canonical KBMention of this KBEntity
            if "canonical_mention" in kb_element.properties:
                kb_element.properties["canonical_mention"].is_referred_in_kb = True
                self.marked_kb_elements.add(kb_element.properties["canonical_mention"])
            self.mark_from_bottom_to_top(self.kb_entity_to_kb_entity_group[kb_element])
        elif isinstance(kb_element,KBEntityGroup):
            kb_element.is_referred_in_kb = True
            self.marked_kb_elements.add(kb_element)
            # If this KBEntityGroup is a component of another entity group, mark the other group as well
            if "component_of_actor_ids" in kb_element.properties:
                for actor_id in kb_element.properties["component_of_actor_ids"]:
                    if actor_id in self.actor_id_to_kb_entity_group:
                        self.actor_id_to_kb_entity_group[actor_id].is_referred_in_kb = True
                        self.marked_kb_elements.add(self.actor_id_to_kb_entity_group[actor_id])
        else:
            raise ValueError("{} Cannot be handled".format(type(kb_element)))

    def resolve(self, kb):
        print("RelevantKBEntityMentionResolver RESOLVE")

        resolved_kb = KnowledgeBase()

        super(RelevantKBEntityMentionResolver, self).copy_all(resolved_kb, kb)


        self.kb_entity_mention_to_kb_entity = dict()
        self.kb_entity_to_kb_entity_group = dict()
        self.actor_id_to_kb_entity_group = dict()

        self.marked_kb_elements = set()

        for entgroupid, kb_entity_group in resolved_kb.entgroupid_to_kb_entity_group.items():
            kb_entity_group.is_referred_in_kb = False
            for kb_entity in kb_entity_group.members:
                kb_entity.is_referred_in_kb = False
                self.kb_entity_to_kb_entity_group[kb_entity] = kb_entity_group
                for kb_entity_mention in kb_entity.mentions:
                    kb_entity_mention.is_referred_in_kb = False
                    self.kb_entity_mention_to_kb_entity[kb_entity_mention] = kb_entity
            if kb_entity_group.actor_id is not None:
                self.actor_id_to_kb_entity_group[kb_entity_group.actor_id] = kb_entity_group

        start_searching_points = set()

        for evt_id,kb_event in resolved_kb.evid_to_kb_event.items():
            for kb_event_mention in kb_event.event_mentions:
                for arg_role,args in kb_event_mention.arguments.items():
                    for arg,score in args:
                        if isinstance(arg, KBMention):
                            self.mark_from_bottom_to_top(arg)
                            start_searching_points.add(self.kb_entity_mention_to_kb_entity[arg])
        OUT_DEGREE = 2

        while OUT_DEGREE > 0:
            alternative_searching_points = set()
            for relid, kb_relation in resolved_kb.relid_to_kb_relation.items():
                if kb_relation.argument_pair_type == "entity-entity":
                    left_entity = resolved_kb.entid_to_kb_entity[kb_relation.left_argument_id]
                    right_entity = resolved_kb.entid_to_kb_entity[kb_relation.right_argument_id]
                    if left_entity in start_searching_points:
                        if right_entity not in start_searching_points and right_entity.is_referred_in_kb is False:
                            alternative_searching_points.add(right_entity)
                        self.mark_from_bottom_to_top(right_entity)
                    if right_entity in start_searching_points:
                        if left_entity not in start_searching_points and left_entity.is_referred_in_kb is False:
                            alternative_searching_points.add(left_entity)
                        self.mark_from_bottom_to_top(left_entity)
            OUT_DEGREE -= 1
            start_searching_points = alternative_searching_points

        return resolved_kb
