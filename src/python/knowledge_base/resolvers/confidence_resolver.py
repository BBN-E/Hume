import sys, os, codecs
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from elements.kb_event_mention import KBEventMention

class ConfidenceResolver(KBResolver):

    KBP_EVENT_CONFIDENCE = 0.75
    CAMEO_EVENT_CONFIDENCE = 0.75
    NN_EVENT_CONFIDENCE = 0.70

    SERIF_ENTITY_RELATION_CONFIDENCE = 0.70
    SERIF_EVENT_RELATION_CONFIDENCE = 0.60
    PDTB_RELATION_CONFIDENCE = 0.40
    
    def __init__(self):
        pass

    def resolve(self, kb, relation_frequency_file, event_triggers_file):
        print "ConfidenceResolver RESOLVE"

        # Initialize counts from trigger files
        self.event_trigger_counts = dict()
        etf = codecs.open(event_triggers_file, 'r', encoding='utf8')
        for line in etf:
            line = line.strip()
            pieces = line.split(" ", 1)
            if len(pieces) != 2:
                print "Malformed line: " + str(line)
                sys.exit(1)
                
            count = int(pieces[0])
            trigger_word = pieces[1].lower()
            if trigger_word not in self.event_trigger_counts: # merge by downcased versions of trigger
                self.event_trigger_counts[trigger_word] = 0
            self.event_trigger_counts[trigger_word] += count
            #print str(trigger_word) + ": " + str(self.event_trigger_counts[trigger_word])
        etf.close()

        self.relation_triple_counts = dict()
        rff = codecs.open(relation_frequency_file, 'r', encoding='utf8')
        for line in rff:
            line = line.strip()
            pieces = line.split("\t")
            if len(pieces) != 3:
                print "Malformed line: " + str(line)
                sys.exit(1)
            count_and_relation_type = pieces[0].strip()
            left_trigger = pieces[1].lower().strip()
            right_trigger = pieces[2].lower().strip()
            pieces = count_and_relation_type.split()
            if len(pieces) != 2:
                print "Malformed count and relation: " + str(count_and_relation_type)
                sys.exit(1)
            count = int(pieces[0])
            relation_type = pieces[1].strip()

            key = (relation_type, left_trigger, right_trigger,)
            if key not in self.relation_triple_counts: # merge by downcased versions of triggers
                self.relation_triple_counts[key] = 0
            self.relation_triple_counts[key] += count
            #print str(key) + ": " + str(self.relation_triple_counts[key])
        rff.close()

        # Resolve!
        resolved_kb = KnowledgeBase()
        super(ConfidenceResolver, self).copy_all(resolved_kb, kb)

        for evid, event in resolved_kb.get_events():
            for event_mention in event.event_mentions:
                if event_mention.model == "ACCENT":
                    event_mention.confidence = ConfidenceResolver.CAMEO_EVENT_CONFIDENCE

                # if event_mention.event_type in KBEventMention.kbp_event_types:
                #     event_mention.confidence = ConfidenceResolver.KBP_EVENT_CONFIDENCE
                # if event_mention.model == "ACCENT":
                #     event_mention.confidence = ConfidenceResolver.CAMEO_EVENT_CONFIDENCE
                # elif event_mention.event_type.lower() != "factor":
                #     # Event found by NN-event models
                #     event_mention.confidence = ConfidenceResolver.NN_EVENT_CONFIDENCE
                # else:
                #     # Causal factor
                #     trigger = str(event_mention.trigger).lower()
                #     trigger_count = self.event_trigger_counts.get(trigger)
                #     if trigger_count is None:
                #         trigger_count = 0
                #
                #     if trigger_count >= 10:
                #         event_mention.confidence = 0.7
                #     elif trigger_count >= 5:
                #         event_mention.confidence = 0.5
                #     elif trigger_count >= 2:
                #         event_mention.confidence = 0.3
                #     elif trigger_count >= 1:
                #         event_mention.confidence = 0.2
                #     else:
                #         event_mention.confidence = 0.1
                print "event_mention.confidence 3: " + str(event_mention.confidence)

        for relid, relation in resolved_kb.get_relations():
            for relation_mention in relation.relation_mentions:
                if relation.argument_pair_type == "entity-entity":
                    relation_mention.confidence = ConfidenceResolver.SERIF_ENTITY_RELATION_CONFIDENCE
                elif relation_mention.properties.get("model") == "SERIF":
                    relation_mention.confidence = ConfidenceResolver.SERIF_EVENT_RELATION_CONFIDENCE
                elif relation_mention.properties.get("model") == "PDTB":
                    relation_mention.confidence = ConfidenceResolver.PDTB_RELATION_CONFIDENCE
                elif "extraction_confidence" in relation_mention.properties: # set in CausalRelationReader for NN relations
                    relation_mention.confidence = relation_mention.properties["extraction_confidence"]
                else:
                    # LearnIt 
                    left_event_trigger = str(relation_mention.left_mention.trigger).lower()
                    right_event_trigger = str(relation_mention.right_mention.trigger).lower()
                    key = (relation.relation_type, left_event_trigger, right_event_trigger,)
                    triple_count = self.relation_triple_counts.get(key)
                    if triple_count is None:
                        triple_count = 0

                    if triple_count >= 10:
                        relation_mention.confidence = 0.7
                    elif triple_count >= 5:
                        relation_mention.confidence = 0.5
                    elif triple_count >= 2:
                        relation_mention.confidence = 0.3
                    elif triple_count >= 1:
                        relation_mention.confidence = 0.2
                    else:
                        relation_mention.confidence = 0.1

        return resolved_kb
