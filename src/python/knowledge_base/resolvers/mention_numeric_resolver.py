import os,sys
from resolvers.kb_resolver import KBResolver

from elements.kb_mention import KBMention
from knowledge_base import KnowledgeBase

script_dir = os.path.dirname(os.path.realpath(__file__))
print(os.path.realpath(os.path.join(script_dir, "..", "..")))
sys.path.append(os.path.join(script_dir, "..", ".."))
from extra_numeric_for_mention import extract_numeric_for_mention, my_tokenizer

import json

class EntityMentionNumericResolver(KBResolver):

    def __init__(self):
        super(EntityMentionNumericResolver, self).__init__()

    def resolve(self, kb):
        print("EntityMentionNumericResolver RESOLVE")

        resolved_kb = KnowledgeBase()

        super(EntityMentionNumericResolver, self).copy_all(resolved_kb, kb)

        for evtid,kb_event in resolved_kb.evid_to_kb_event.items():
            for kb_event_mention in kb_event.event_mentions:
                for arg_role,args in kb_event_mention.arguments.items():
                    if arg_role in {'has_actor', 'has_active_actor', 'has_affected_actor'}:
                        for arg in args:
                            if isinstance(arg,KBMention):
                                kb_mention = arg
                                original_sentence_str = kb_mention.sentence.text
                                mention_str = kb_mention.mention_text
                                possible_numeric_dict = extract_numeric_for_mention(mention_str,mention_str)
                                possible_numeric_dict_extra = extract_numeric_for_mention(original_sentence_str,mention_str)

                                if len(possible_numeric_dict.keys()) >0:
                                    for key in possible_numeric_dict_extra.keys():
                                        if key not in {'val','min_val','max_val'}:
                                            possible_numeric_dict[key] = possible_numeric_dict_extra[key]
                                    kb_mention.properties['numeric'] = possible_numeric_dict

        return resolved_kb
