from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from elements.kb_mention import KBMention
from elements.kb_entity import KBEntity

import sys, os, re

# Add entity types and subtypes to entities that have mentions
# with certain type, head words and premods. Also add entity types
# and subtypes for the entities that appear in specified events.

class AdditionalEntityTypeResolver(KBResolver):
    def __init__(self):
        self.descriptor_to_entity_type_info = dict() # Maps headword to to list of (old-entity-type new-entity-type.subtype, confidence, premods,)
        self.event_to_entity_type_info = dict() # Maps event-type to list of (role-type, old-entity-type, new-entity-type.subtype, confidence,)
        
        script_dir = os.path.dirname(os.path.realpath(__file__))

        descriptors_to_entity_type_file = os.path.join(script_dir, "..", "data_files", "descriptors_to_entity_type.txt")
        event_to_entity_type_file = os.path.join(script_dir, "..", "data_files", "event_to_entity_type.txt")

        i = open(descriptors_to_entity_type_file)
        for line in i:
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                continue
            pieces = line.split(" ", 4)
            if len(pieces) != 5:
                print "Malformed line: " + line
                sys.exit(1)
            head_word = pieces[0]
            if head_word not in self.descriptor_to_entity_type_info:
                self.descriptor_to_entity_type_info[head_word] = []
            
            self.descriptor_to_entity_type_info[head_word].append((pieces[1], pieces[2], float(pieces[3]), pieces[4],))
        i.close()
        
        i = open(event_to_entity_type_file)
        for line in i:
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                continue
            pieces = line.split(" ")
            if len(pieces) != 5:
                print "Malformed line: " + line
                sys.exit(1)
            event_type = pieces[0]
            if event_type not in self.event_to_entity_type_info:
                self.event_to_entity_type_info[event_type] = []
            
            self.event_to_entity_type_info[event_type].append((pieces[1], pieces[2], pieces[3], float(pieces[4]),))
        i.close()

    def resolve(self, kb):
        print "AdditionalEntityTypeResolver RESOLVE"

        resolved_kb = KnowledgeBase()
        super(AdditionalEntityTypeResolver, self).copy_all(resolved_kb, kb)

        # Apply a second type to some entities as per this resolver's description
        
        for kb_entity_id, kb_entity in resolved_kb.entid_to_kb_entity.iteritems():
            for kb_mention in kb_entity.mentions:
                if kb_mention.mention_type != "desc":
                    continue
                head_word = kb_mention.mention_head_text.lower()                
                if head_word in self.descriptor_to_entity_type_info:
                    for rule in self.descriptor_to_entity_type_info[head_word]:
                        rule_old_entity_type = rule[0]
                        rule_new_entity_type_subtype = rule[1]
                        rule_confidence = rule[2]
                        rule_premods = rule[3]

                        if kb_mention.entity_type == rule_old_entity_type or kb_entity.get_best_entity_type() == rule_old_entity_type:
                            regex = rule_premods + r"\s+" + head_word
                            m = re.search(regex, kb_mention.mention_text, re.I)
                            if m is not None:
                                kb_entity.add_entity_type(rule_new_entity_type_subtype, rule_confidence)
                                
        for kb_event in resolved_kb.evid_to_kb_event.values():
            for kb_event_mention in kb_event.event_mentions:
                event_type = kb_event_mention.event_type
                if event_type in self.event_to_entity_type_info:
                    for rule in self.event_to_entity_type_info[event_type]:
                        rule_role = rule[0]
                        rule_old_entity_type = rule[1]
                        rule_new_entity_type_subtype = rule[2]
                        rule_confidence = rule[3]

                        if rule_role in kb_event_mention.arguments:
                            for argument in kb_event_mention.arguments[rule_role]:
                                if not isinstance(argument, KBMention):
                                    continue
                                kb_mention = argument
                                kb_entid = kb.kb_mention_to_entid[kb_mention]
                                kb_entity = kb.entid_to_kb_entity[kb_entid]
                                
                                if kb_mention.entity_type == rule_old_entity_type or kb_entity.get_best_entity_type() == rule_old_entity_type:
                                    kb_entity_id = kb.kb_mention_to_entid[kb_mention]
                                    kb_entity = kb.entid_to_kb_entity[kb_entity_id]
                                    kb_entity.add_entity_type(rule_new_entity_type_subtype, rule_confidence)
                                    #print "Adding entity type to: " + kb_entity.id + " rule_new_entity_type_subtype " + str(rule_confidence)
        return resolved_kb
