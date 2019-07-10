from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
from elements.kb_mention import KBMention
from util.extra_numeric_for_mention import extract_numeric_for_mention

class EntityMentionNumericResolver(KBResolver):

    def __init__(self):
        super(EntityMentionNumericResolver, self).__init__()

    def resolve(self, kb):
        print "EntityMentionNumericResolver RESOLVE"

        resolved_kb = KnowledgeBase()

        super(EntityMentionNumericResolver, self).copy_all(resolved_kb, kb)

        for evtid,kb_event in resolved_kb.evid_to_kb_event.items():
            for kb_event_mention in kb_event.event_mentions:
                for arg_role,args in kb_event_mention.arguments.items():
                    # if arg_role in {'has_actor','has_active_actor','has_affected_actor','has_recipient','has_provider'}:
                    if True:
                        for arg in args:
                            if isinstance(arg,KBMention):
                                kb_mention = arg
                                original_sentence_str = kb_mention.sentence.text
                                sent_start = kb_mention.sentence.start_offset
                                mention_str = original_sentence_str[kb_mention.head_start_char-sent_start:kb_mention.head_end_char-sent_start+1]
                                possible_numeric_dict = extract_numeric_for_mention(original_sentence_str,mention_str)
                                if len(possible_numeric_dict.keys()) > 0:
                                    kb_mention.properties['numeric'] = possible_numeric_dict
        return resolved_kb
