import sys, os, re, codecs
from knowledge_base import KnowledgeBase
from kb_resolver import KBResolver
import collections


class EntityAddPropertyResolver(KBResolver):
    def __init__(self):
        pass

    '''
    Find the most common mention text as the canonical name
    '''
    def pick_canonical_name(self, kb_entity):
        names = []
        for kb_mention in kb_entity.mentions:
            if kb_mention.mention_type == "desc" or kb_mention.mention_type == "part":
                names.append(kb_mention.mention_text)
        if collections.Counter(names).most_common(1):
            kb_entity.canonical_name = collections.Counter(names).most_common(1)[0][0].encode('utf-8').replace("\n", "")

    def resolve(self, kb):
        print "EntityAddPropertyResolver RESOLVE"
        resolved_kb = KnowledgeBase()

        super(EntityAddPropertyResolver, self).copy_all(resolved_kb, kb)

        for entid, kb_entity in resolved_kb.entid_to_kb_entity.iteritems():
            if kb_entity.canonical_name is None:
                self.pick_canonical_name(kb_entity)

        return resolved_kb


