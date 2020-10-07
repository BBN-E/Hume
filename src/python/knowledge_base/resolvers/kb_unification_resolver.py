import sys, os, re, codecs
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver
import collections
from elements.kb_group import KBEventGroup, KBEntityGroup, KBRelationGroup
from elements.kb_relation import KBRelation
from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention
from enum import IntEnum
from elements.kb_event_mention import KBEventMention




class GroupEventBasedOn(IntEnum):
    LastTokenOfEventMention = 1
    EventTypeGroundingWithScoreCutoff = 2


# @hqiu. One switches
group_event_based_on = GroupEventBasedOn.LastTokenOfEventMention


class KbUnificationResolver(KBResolver):
    def __init__(self):

        self.eventgroup2eventgroupid = {}
        self.eventgroupid2eventgroup = {}

        self.event2eventid = {}
        self.eventid2event = {}

        self.entity2entityid = {}
        self.entityid2entity = {}

        self.relations_eventgroup2eventgroup = set()
        self.relations_eventgroup2event = set()
        self.relations_event2entity = set()

        pass

    def resolve(self, kb):
        print("KbUnificationResolver RESOLVE")
        resolved_kb = KnowledgeBase()

        super(KbUnificationResolver, self).copy_all(resolved_kb, kb)

        self.kb = kb

        # event mention to event dict
        self.kb_event_mention_to_kb_event = dict()
        for kb_event_id, kb_event in self.kb.evid_to_kb_event.items():
            for kb_event_mention in kb_event.event_mentions:
                self.kb_event_mention_to_kb_event[kb_event_mention] = kb_event

        for kb_relation_id, kb_relation in self.kb.relid_to_kb_relation.items():
            if kb_relation.argument_pair_type == "event-event":
                relation_type = kb_relation.relation_type
                for kb_relation_mention in kb_relation.relation_mentions:
                    left_mention = kb_relation_mention.left_mention
                    assert isinstance(left_mention,KBEventMention)
                    right_mention = kb_relation_mention.right_mention
                    assert isinstance(right_mention, KBEventMention)

                    # add to event groups
                    if group_event_based_on is GroupEventBasedOn.LastTokenOfEventMention:
                        left_event_group_id = left_mention.trigger.lower()
                        right_event_group_id = right_mention.trigger.lower()
                    elif group_event_based_on is GroupEventBasedOn.EventTypeGroundingWithScoreCutoff:
                        passed_confident_filter = True
                        if left_mention.event_type.lower() in {"Event".lower()}:
                            passed_confident_filter = False
                        left_event_group_id = left_mention.event_type


                        if right_mention.event_type.lower() in {"Event".lower()}:
                            passed_confident_filter = False
                        right_event_group_id = right_mention.event_type
                    else:
                        raise NotImplemented

                    if group_event_based_on is GroupEventBasedOn.LastTokenOfEventMention or (group_event_based_on is GroupEventBasedOn.EventTypeGroundingWithScoreCutoff and passed_confident_filter is True):
                        if left_event_group_id not in resolved_kb.evgroupid_to_kb_event_group:
                            resolved_kb.evgroupid_to_kb_event_group[left_event_group_id]=KBEventGroup(left_event_group_id)
                        resolved_kb.evgroupid_to_kb_event_group[left_event_group_id].members.append(self.kb_event_mention_to_kb_event[left_mention])
                        if right_event_group_id not in resolved_kb.evgroupid_to_kb_event_group:
                            resolved_kb.evgroupid_to_kb_event_group[right_event_group_id]=KBEventGroup(right_event_group_id)
                        resolved_kb.evgroupid_to_kb_event_group[right_event_group_id].members.append(self.kb_event_mention_to_kb_event[right_mention])
                        relation_group_id = left_event_group_id + "-" + relation_type + "-" + right_event_group_id
                        if relation_group_id not in resolved_kb.relgroupid_to_kb_relation_group:
                            # Add new relation group
                            resolved_kb.relgroupid_to_kb_relation_group[relation_group_id] = KBRelationGroup(
                                relation_group_id, relation_type, left_event_group_id, right_event_group_id)

                        kb_relation_group = resolved_kb.relgroupid_to_kb_relation_group[relation_group_id]
                        if kb_relation not in kb_relation_group.members:
                            kb_relation_group.members.append(kb_relation)

                        # print (
                                    # "kb_relation_group=" + kb_relation_group.id + ", left_event_group_id=" + kb_relation_group.left_argument_id + ", right_event_group_id=" + kb_relation_group.right_argument_id)

                        self.add_event_arguments(resolved_kb, left_mention)
                        self.add_event_arguments(resolved_kb, right_mention)

#                   resolved_kb.relgroupid_to_kb_relation_group[relation_group_id].members.append(KBRelation(relation_group_id, "event-event", relation_type, left_event_group_id, right_event_group_id))



        # remove redundandy
        # TODO

        return resolved_kb

    def add_event_arguments(self, resolved_kb, kb_event_mention):
        for kb_arg_role in kb_event_mention.arguments:
            args_for_role = kb_event_mention.arguments[kb_arg_role]
            if type(args_for_role[0]) == list:
                args_for_role = args_for_role[0]
            for kb_argument in args_for_role:
                # get argument mention text
                if isinstance(kb_argument, KBValueMention):
                    mention_text = kb_argument.value_mention_text
                else:
                    mention_text = kb_argument.mention_text

                if kb_argument in self.kb.kb_mention_to_entid:
                    arg_entity_id = self.kb.kb_mention_to_entid[kb_argument]
                    arg_entity = self.kb.entid_to_kb_entity[arg_entity_id]

                    for entity_type_info_key in arg_entity.entity_type_to_confidence.keys():
                        entity_type_info = entity_type_info_key.split(".")
                        entity_type = entity_type_info[0]
                        entity_subtype = entity_type_info[1]
                        if arg_entity.canonical_name is not None and kb_event_mention.trigger is not None:
                            relation_type = kb_arg_role.encode('utf-8')
                            arg_entity_str = entity_type + "-" + entity_subtype + "-"\
                                             + arg_entity.canonical_name.encode('utf-8').strip()

                            entity_group_id = arg_entity_str
                            if entity_group_id not in resolved_kb.entgroupid_to_kb_entity_group:
                                resolved_kb.entgroupid_to_kb_entity_group[entity_group_id] = KBEntityGroup(
                                    entity_group_id, arg_entity_str, None)
                            resolved_kb.entgroupid_to_kb_entity_group[entity_group_id].members.append(
                                resolved_kb.entid_to_kb_entity[arg_entity_id])
