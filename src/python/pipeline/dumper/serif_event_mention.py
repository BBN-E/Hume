import enum

import serifxml3

def get_event_anchor(serif_em:serifxml3.EventMention,serif_sentence_tokens:serifxml3.TokenSequence):

    if serif_em.semantic_phrase_start is not None:
        serif_em_semantic_phrase_text = " ".join(i.text for i in serif_sentence_tokens[int(serif_em.semantic_phrase_start):int(serif_em.semantic_phrase_end)+1])
        return serif_em_semantic_phrase_text
    elif len(serif_em.anchors) > 0:
        return " ".join(i.anchor_node.text for i in serif_em.anchors)
    else:
        return serif_em.anchor_node.text
class SerifEventMentionTypingField(enum.Enum):
    event_type = "event_type"
    event_types = "event_types"
    factor_types = "factor_types"

def get_event_type(serif_em:serifxml3.EventMention,typing_field:SerifEventMentionTypingField):
    if typing_field == SerifEventMentionTypingField.event_type:
        return [[serif_em.event_type,serif_em.score]]
    ret = list()
    if typing_field == SerifEventMentionTypingField.event_types:
        for event_type in serif_em.event_types:
            ret.append([event_type.event_type,event_type.score])
    elif typing_field == SerifEventMentionTypingField.factor_types:
        for event_type in serif_em.factor_types:
            ret.append([event_type.event_type,event_type.score])
    else:
        raise NotImplementedError
    return ret

def get_event_arg(serif_em:serifxml3.EventMention):
    ret = list()
    for argument in serif_em.arguments:
        if isinstance(argument.mention,serifxml3.Mention):
            ret.append([argument.role,argument.mention.text])
        elif isinstance(argument.value_mention,serifxml3.ValueMention):
            ret.append([argument.role,argument.value_mention.text])
        else:
            raise NotImplementedError
    return ret