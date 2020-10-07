import sys, os, codecs
from knowledge_base import KnowledgeBase
from resolvers.kb_resolver import KBResolver
from elements.kb_group import KBEventGroup

class RedundantEventResolver(KBResolver):
    def __init__(self):
        pass
    
    def resolve(self, kb): 
        print("RedundantEventResolver RESOLVE")

        resolved_kb = KnowledgeBase()
        super(RedundantEventResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_events_relations_and_groups()

        # Organize events by sentence
        sentence_to_event_mention_list = dict()
        event_mention_to_event = dict()
        for evid, event in kb.get_events():
            for event_mention in event.event_mentions:
                event_mention_to_event[event_mention] = event
                if event_mention.model == "ACCENT":
                    continue
                sentence = event_mention.sentence
                if sentence not in sentence_to_event_mention_list:
                    sentence_to_event_mention_list[sentence] = []
                sentence_to_event_mention_list[sentence].append(event_mention)

        event_mentions_to_remove = set()
        for sentence, event_mention_list in sentence_to_event_mention_list.items():
            # Looking at event mentions for a particular sentence
            for em1 in event_mention_list:
                for em2 in event_mention_list:
                    if em1 == em2:
                        continue

                    if em1.is_similar_and_better_than(em2):
                        #print "Throwing out: " + em2.id + " because it is worse than " + em1.id
                        event_mentions_to_remove.add(em2)

        bad_event_ids = set()
        for evid, event in kb.get_events():
            found_good_event_mention = False
            for event_mention in event.event_mentions:
                if not event_mention in event_mentions_to_remove: 
                    found_good_event_mention = True
                    break
            if found_good_event_mention:
                resolved_kb.add_event(event)
            else:
                bad_event_ids.add(evid)
                
        for relid, relation in kb.get_relations():
            if relation.left_argument_id not in bad_event_ids and relation.right_argument_id not in bad_event_ids:
                resolved_kb.add_relation(relation)

        # add event group to event mapping:
        for evgid, event_group in kb.get_event_groups():
            ev_group = KBEventGroup(event_group.id)
            for event in event_group.members:
                if event.id not in bad_event_ids:
                    ev_group.members.append(event)
            if len(ev_group.members) > 0:
                resolved_kb.add_event_group(ev_group)

        return resolved_kb

    
