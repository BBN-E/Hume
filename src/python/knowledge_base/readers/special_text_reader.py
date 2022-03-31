from elements.kb_causal_factor import KBCausalFactor
from elements.kb_document import KBDocument
from elements.kb_entity import KBEntity
from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from elements.kb_group import KBEntityGroup, KBEventGroup
from elements.kb_mention import KBMention
from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from elements.kb_sentence import KBSentence
from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention
from shared_id_manager.shared_id_manager import SharedIDManager

def add_sentence(sent_no,kb_document,sent_start,sent_end,sent_text):
    sentid = SharedIDManager.get_in_document_id("Sentence", kb_document.id)
    kb_sentence = KBSentence(sentid, sent_start, sent_end, sent_text,
                             sent_text,
                             sent_no)
    kb_document.add_sentence(kb_sentence)

def get_snippet(kb_sentence):
    sentence_start = kb_sentence.start_offset
    sentence_end = kb_sentence.end_offset
    return kb_sentence.original_text, sentence_start, sentence_end

def get_causal_factors(kb_document, groundings):
    ret = list()
    for factor_type,score in groundings:
        cf_id = SharedIDManager.get_in_document_id("CausalFactor", kb_document.id)
        trend = "Unknown"
        new_causal_factor = KBCausalFactor(cf_id, factor_type, trend, score, 0.0)
        ret.append(new_causal_factor)
    return ret

def add_event(kb_document, kb_sentence, event_start_char, event_end_char, event_start_idx, event_end_idx, original_text,grounding):
    event_mention_id = SharedIDManager.get_in_document_id("EventMention", kb_document.id)
    kb_event_mention = KBEventMention(event_mention_id,
                                      kb_document,
                                      original_text,
                                      event_start_char,
                                      event_end_char,
                                      get_snippet(kb_sentence),
                                      [],
                                      get_causal_factors(kb_document, grounding),
                                      kb_sentence,
                                      [], [], "KBP", max(i[1] for i in grounding),
                                      original_text,
                                      event_start_idx, event_end_idx)
    kb_event_mention.properties["direction_of_change"] = "Unknown"
    event_id = SharedIDManager.get_in_document_id(  # Generates a new one for a new Event
        "Event",
        kb_document.id
    )
    kb_event = KBEvent(event_mention_id, max(grounding,key=lambda x:x[1])[0])
    kb_event.add_event_mention(kb_event_mention)
    return kb_event

def create_eerm(kb_document, kb_event_left, kb_event_right,relation_type):
    relation_id = SharedIDManager.get_in_document_id("Relation", kb_document.id)
    relation_mention_id = SharedIDManager.get_in_document_id("RelationMention", kb_document.id)
    kb_relation = KBRelation(relation_id, "event-event", relation_type, kb_event_left.id,
                             kb_event_right.id)
    kb_relation_mention = KBRelationMention(relation_mention_id, kb_event_left.event_mentions[0],
                                            kb_event_right.event_mentions[0], get_snippet(kb_event_left.event_mentions[0].sentence), kb_document)
    kb_relation.add_relation_mention(kb_relation_mention)
    return kb_relation

class SpecialTextReader:

    def __init__(self):
        pass

    def read(self, kb):
        raw_text = "Floods cause migration. Migration causes conflict."
        sent_1 = (0,22)
        span1_1 = (0,5) # Floods
        span1_2 = (7,11) # cause
        span1_3 = (13, 21) # migration

        sent_2 = (24,49)
        span2_1 = (24, 32)
        span2_2 = (34, 39)
        span2_3 = (41,48)

        doc_id = "ENG_WM_BEN_011122"
        kb_document = KBDocument(doc_id, {"offset":0,"uuid":doc_id})
        kb.add_document(kb_document)

        # Handle sentences
        add_sentence(0, kb_document, sent_1[0], sent_1[1], raw_text[sent_1[0]:sent_1[1]+1])
        add_sentence(1, kb_document, sent_2[0], sent_2[1], raw_text[sent_2[0]:sent_2[1]+1])

        # Handle event
        before_flood_0_grounding = [["/wm/concept/natural_disaster",1.0]]
        flood_0_event = add_event(kb_document, kb_document.sentences[0], span1_1[0], span1_1[1], 0, 0, raw_text[span1_1[0]:span1_1[1]+1],before_flood_0_grounding)
        kb.add_event(flood_0_event)
        before_migration_0_grounding = [["/wm/concept/migration",1.0]]
        migration_0_event = add_event(kb_document, kb_document.sentences[0], span1_3[0], span1_3[1], 0, 0, raw_text[span1_3[0]:span1_3[1]+1],before_migration_0_grounding)
        kb.add_event(migration_0_event)
        before_migration_1_grounding = [["/wm/concept/migration",1.0]]
        migration_1_event = add_event(kb_document, kb_document.sentences[1], span2_1[0], span2_1[1], 0, 0, raw_text[span2_1[0]:span2_1[1]+1],before_migration_1_grounding)
        kb.add_event(migration_1_event)
        before_conflict_1_grounding = [["/wm/concept",1.0]]
        after_conflict_1_grounding = [["/wm/concept/conflict",1.0]]
        conflict1_event = add_event(kb_document, kb_document.sentences[1], span2_3[0], span2_3[1], 0, 0, raw_text[span2_3[0]:span2_3[1]+1],after_conflict_1_grounding)
        kb.add_event(conflict1_event)

        # Handle causal relation
        kb_relation_1 = create_eerm(kb_document, flood_0_event, migration_0_event, "Cause-Effect")
        kb.add_relation(kb_relation_1)
        kb_relation_2 = create_eerm(kb_document, migration_1_event, conflict1_event, "Cause-Effect")
        kb.add_relation(kb_relation_2)


if __name__ == "__main__":
    pass