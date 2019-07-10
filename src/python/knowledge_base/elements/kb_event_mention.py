from kb_element import KBElement

class KBEventMention(KBElement):

    # kbp_event_types = { "Conflict.Attack", "Conflict.Demonstrate", "Contact.Broadcast", "Contact.Contact", "Contact.Correspondence", "Contact.Meet", "Justice.Arrest-Jail", "Life.Die", "Life.Injure", "Manufacture.Artifact", "Movement.Transport-Artifact", "Movement.Transport-Person", "Personnel.Elect", "Personnel.End-Position", "Personnel.Start-Position", "Transaction.Transaction", "Transaction.Transfer-Money", "Transaction.Transfer-Ownership" }
    
    def __init__(self, id, kb_document, event_type, trigger, trigger_start, trigger_end, snippet, kb_sentence, proposition_infos, model, confidence=0.5):

        if confidence==1.0: # keyword-based event finding
            confidence = 0.75

        self.id = id
        self.document = kb_document
        self.event_type = event_type
        self.trigger = trigger
        self.trigger_start = trigger_start
        self.trigger_end = trigger_end
        self.snippet = snippet
        self.properties = dict()
        self.sentence = kb_sentence
        self.model = model
        self.confidence = confidence
        self.arguments = dict() # Maps role to list of mentions or value_mentions
        self.has_topic = None
        self.triggering_phrase = None
        self.internal_ontology_class = None # points to OntologyClass
        self.external_ontology_sources = []  # source string -> confidence e.g. 'http://ontology.causeex.com/ontology/odps/Event#Investigation' => 1.0
        # list of (predicate, start_offset, end_offset,) ordered by how they
        # appear in serifxml. Only used for ACCENT events.
        self.proposition_infos = proposition_infos
        
    def add_argument(self, role, mention_or_value_mention):
        if role not in self.arguments:
            self.arguments[role] = []
        self.arguments[role].append(mention_or_value_mention)

    def is_similar_and_better_than(self, other):
        if self.sentence != other.sentence:
            return False
        
        if self.trigger is None or other.trigger is None:
            return False

        if self.trigger != other.trigger:
            return False

        # Factfinder events are really a different type of event, they don't
        # appear in causal relations for instance
        if (self.model == "FACTFINDER" and other.model != "FACTFINDER" or
            self.model != "FACTFINDER" and other.model == "FACTFINDER"):
            return False 

        # These are essentially similar, we need to return True if
        # self is better, and False if other is better, and the choice
        # must be consistent if we were to switch the argument order
        # to this function.

        if len(self.arguments) > len(other.arguments):
            return True
        if len(other.arguments) > len(self.arguments):
            return False

        if self.model_type_score() > other.model_type_score():
            return True
        if other.model_type_score() > self.model_type_score():
            return False

        if self.event_type_score() > other.event_type_score():
            return True
        if other.event_type_score() > self.event_type_score():
            return False

        # Tie breaker
        return self.id < other.id
    
    def model_type_score(self):
        if self.model == "ACCENT":
            return 1
        else:
            return 0

    def event_type_score(self):
        # if self.event_type in KBEventMention.kbp_event_types:
        #    return 3
        if self.event_type == "factor":
            return 0
        elif self.event_type == "Factor" or self.event_type == "Event":
            return 1
        else:
            return 2
        
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
            elif (hasattr(v, "reprJSON")):
                d[a] = v.reprJSON()
            else:
                d[a] = v
        return d
