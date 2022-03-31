from elements.kb_element import KBElement
from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention, KBMoneyValueMention, KBTimeValueMention


class KBEventMention(KBElement):

    # kbp_event_types = { "Conflict.Attack", "Conflict.Demonstrate", "Contact.Broadcast", "Contact.Contact", "Contact.Correspondence", "Contact.Meet", "Justice.Arrest-Jail", "Life.Die", "Life.Injure", "Manufacture.Artifact", "Movement.Transport-Artifact", "Movement.Transport-Person", "Personnel.Elect", "Personnel.End-Position", "Personnel.Start-Position", "Transaction.Transaction", "Transaction.Transfer-Money", "Transaction.Transfer-Ownership" }

    def __init__(self, id, kb_document, trigger, trigger_start, trigger_end, snippet,
                 list_event_types_and_confidence, list_causal_factors,
                 kb_sentence, proposition_infos, anchor_info,
                 model, event_confidence, trigger_original_text, trigger_start_token_idx, trigger_end_token_idx,
                 conceivers=(), timexps=()):

        self.id = id
        self.document = kb_document
        # self.groundings = dict()
        self.trigger = trigger
        self.trigger_start = trigger_start
        self.trigger_end = trigger_end
        self.snippet = snippet
        self.properties = dict()
        self.sentence = kb_sentence
        self.arguments = dict()  # Maps role to list of mentions or value_mentions
        self.has_topic = None
        self.triggering_phrase = None
        # self.internal_ontology_class = None # points to OntologyClass
        self.external_ontology_sources = list_event_types_and_confidence  # (source string, confidence) e.g. ('http://ontology.causeex.com/ontology/odps/Event#Investigation', 1.0)
        self.causal_factors = list_causal_factors  # List of KBCausalFactor objects
        # list of (predicate, start_offset, end_offset,) ordered by how they
        # appear in serifxml. Only used for ACCENT events.
        self.proposition_infos = proposition_infos
        self.anchor_info = anchor_info
        self.model = model
        self.event_confidence = event_confidence
        self.trigger_original_text = trigger_original_text
        self.trigger_start_token_idx = trigger_start_token_idx
        self.trigger_end_token_idx = trigger_end_token_idx
        self.conceivers = conceivers
        self.timexps = timexps

    def add_argument(self, role, mention_or_value_mention, confidence):
        if role not in self.arguments:
            self.arguments[role] = []
        self.arguments[role].append([mention_or_value_mention, confidence])

    @staticmethod
    def get_mention_or_value_mention_span(mention_or_value_mention):
        if isinstance(mention_or_value_mention, KBMention):
            return mention_or_value_mention.start_char, mention_or_value_mention.end_char
        if isinstance(mention_or_value_mention, KBValueMention) or isinstance(mention_or_value_mention,
                                                                              KBTimeValueMention) or isinstance(
            mention_or_value_mention, KBMoneyValueMention):
            return mention_or_value_mention.head_start_char, mention_or_value_mention.head_end_char
        print(type(mention_or_value_mention))
        raise NotImplementedError

    def is_particular_event_argument_existed(self, role, start_char, end_char):

        for argument_in_role, confidence in self.arguments.get(role, list()):
            role_start, role_end = KBEventMention.get_mention_or_value_mention_span(argument_in_role)
            if role_start == start_char and role_end == end_char:
                return True
        return False

    # JSON serialization helper
    def reprJSON(self):
        d = dict()
        for a, v in self.__dict__.items():
            if v is None:
                continue
            elif a == "document":
                d[a] = v.id
            elif a == "has_topic":
                d[a] = v.id
            elif a == "confidence":
                continue
            elif (hasattr(v, "reprJSON")):
                d[a] = v.reprJSON()
            else:
                d[a] = v
        return d

    def add_or_change_grounding(self, event_type, score):
        for i in range(len(self.external_ontology_sources)):
            grounded_type, old_score = self.external_ontology_sources[i]
            if grounded_type == event_type:  # update score
                self.external_ontology_sources[i] = (event_type, score)
                return
        # add new grounding if not present
        self.external_ontology_sources.append((event_type, score))

    # def event_type(self):
    #     event_type = list(self.groundings.keys())[0]
    #     return event_type
    #     # return self.event_type
    #
    # def confidence(self):
    #     event_type = list(self.groundings.keys())[0]
    #     confidence = self.groundings[event_type]
    #     return confidence
    #        return self.confidence

    def get_max_grounding_confidence(self):
        max_score = None

        for kb_causal_factor in self.causal_factors:
            if max_score is None or kb_causal_factor.relevance > max_score:
                max_score = kb_causal_factor.relevance
        if max_score is not None:
            return max_score

        if len(self.external_ontology_sources) == 0:
            print("WARNING: No external ontology sources when calculating max confidence")
            return 1.0

        return max(score for type, score in self.external_ontology_sources)
