import sys, os, codecs
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention
from elements.kb_group import KBEventGroup

class RemovalRule:
    # Essentially a list of (role, entity_type,) tuples
    def __init__(self, relation_or_event_type):
        self.relation_or_event_type = relation_or_event_type
        self.role_type_pairs = []

    def add_role_type_pair(self, pair):
        self.role_type_pairs.append(pair)

    def matches_relation_mention(self, relation_mention, kb):
        for role, entity_type in self.role_type_pairs:
            if role != "left_argument" and role != "right_argument":
                print "WARNING: RemovalByTypeResolver -- Bad relation role in type_removal.txt -- " + role
                return False
            
            if role == "left_argument" and not relation_mention.left_mention:
                return False
            
            if role == "right_argument" and not relation_mention.right_mention:
                return False
            
            if role == "left_argument":
                if not self.type_matches(relation_mention.left_mention, entity_type, kb):
                    return False
            
            if role == "right_argument":
                if not self.type_matches(relation_mention.right_mention, entity_type, kb):
                    return False

        return True

    def matches_event_mention(self, event_mention, kb):
        for role, entity_type in self.role_type_pairs:
            if not self.found_role_with_entity_type(event_mention, role, entity_type, kb):
                return False
        return True

    def found_role_with_entity_type(self, event_mention, role, entity_type, kb):
        arguments = event_mention.arguments.get(role)
        if not arguments:
            return False
        for argument in arguments:
            if self.type_matches(argument, entity_type, kb):
                return True
        return False

    def type_matches(self, mention_or_value_mention, t, kb):
        if isinstance(mention_or_value_mention, KBMention):
            # Does t match mention type (doesn't include subtype)
            if mention_or_value_mention.entity_type == t:
                return True
            # Does t match entity type (does include subtype)
            entid = kb.kb_mention_to_entid[mention_or_value_mention]
            entity = kb.entid_to_kb_entity[entid]
            if t in entity.entity_type_to_confidence:
                return True
            
        if isinstance(mention_or_value_mention, KBValueMention):
            return mention_or_value_mention.value_type == t
        
        return False

class RemovalByTypeResolver(KBResolver):
    def __init__(self):
        self.removal_info = dict() # maps relation/event type to list of RemovalRule objects

        script_dir = os.path.dirname(os.path.realpath(__file__))
        type_removal_file = os.path.join(script_dir, "..", "data_files", "type_removal.txt")

        trf = open(type_removal_file, 'r')
        for line in trf:
            line = line.strip()
            if len(line) == 0 or line.startswith("#"):
                continue
            pieces = line.split()
            t = pieces[0]
            rule = RemovalRule(t)
            for i in range(1, len(pieces), 2):
                #print str(pieces)
                #print str(i)
                tpl = (pieces[i], pieces[i+1],)
                rule.add_role_type_pair(tpl)

            if t not in self.removal_info:
                self.removal_info[t] = []
            self.removal_info[t].append(rule)
            
        trf.close()

    def resolve(self, kb):
        print "RemovalByTypeResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(RemovalByTypeResolver, self).copy_all(resolved_kb, kb)
        resolved_kb.clear_events_relations_and_groups()

        bad_event_ids = set()
        for evid, event in kb.get_events():                
            for event_mention in event.event_mentions:
                rule_list = self.removal_info.get(event_mention.event_type)
                if not rule_list:
                    break
                for rule in rule_list:
                    if rule.matches_event_mention(event_mention, kb):
                        bad_event_ids.add(evid)
                        break

        bad_relation_ids = set()
        for relid, relation in kb.get_relations():
            for relation_mention in relation.relation_mentions:
                rule_list = self.removal_info.get(relation.relation_type)
                if not rule_list:
                    break
                for rule in rule_list:
                    if rule.matches_relation_mention(relation_mention, kb):
                        bad_relation_ids.add(relid)
                        break
                
        # Add in non-bad events to resolved KB
        for evid, event in kb.get_events():
            if evid not in bad_event_ids:
                resolved_kb.add_event(event)
            #else:
            #    print "Removing: " + evid

        # Add in non-bad relations that didn't have an event removed 
        for relid, relation in kb.get_relations():
            if (relid not in bad_relation_ids and
                relation.left_argument_id not in bad_event_ids and
                relation.right_argument_id not in bad_event_ids):
                
                resolved_kb.add_relation(relation)
            #else:
            #    print "Removing: " + relid

        # add event group to event mapping:
        for evgid, event_group in kb.get_event_groups():
            ev_group = KBEventGroup(event_group.id)
            for event in event_group.members:
                if event.id not in bad_event_ids:
                    ev_group.members.append(event)
            if len(ev_group.members) > 0:
                resolved_kb.add_event_group(ev_group)

        return resolved_kb


