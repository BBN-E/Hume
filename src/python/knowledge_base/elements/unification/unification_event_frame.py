from elements.kb_event_mention import KBEventMention
from elements.kb_value_mention import KBValueMention
from elements.kb_mention import KBMention
from unification_provenance import UnificationProvenance
from unification_event_argument import UnificationEventArgument
from unification_span import UnificationSpan
from unification_element import UnificationElement

class UnificationEventFrame(UnificationElement):
    def __init__(self, kb_event_mention, kb):
        self.arguments = []
        self.frame_types = self.get_frame_types(kb_event_mention.external_ontology_sources)

        for bbn_role, event_arguments in kb_event_mention.arguments.iteritems():
            role = self.get_argument_role(bbn_role)
            for event_argument in event_arguments:
                if (isinstance(event_argument, KBMention) or 
                    (isinstance(event_argument, KBValueMention) and (role == "time" or role == "has_time" or role == "Time"))):
                    self.arguments.append(UnificationEventArgument(role, event_argument, kb))

        self.properties = dict()
        self.properties["confidence"] = kb_event_mention.confidence
        self.evidence = dict()
        span = UnificationSpan.create_from_event_mention(kb_event_mention)
        if span:
            self.evidence["trigger"] = span

        self.evidence["sentence"] = UnificationSpan.create_from_sentence(
            kb_event_mention.sentence, kb_event_mention.document)

        self.docid = kb_event_mention.document.properties["uuid"]
        self.provenance = UnificationProvenance()

        # has_topic argument
        if kb_event_mention.has_topic:
            self.arguments.append(self.create_argument_frame("http://ontology.causeex.com/ontology/odps/Event#has_topic", kb_event_mention.has_topic, kb))

    # does the same thing as UnificationRelationArgument, but we want to avoid the import loop
    def create_argument_frame(self, role, kb_event_mention, kb):
        results = {}
        results["role"] = role
        results["confidence"] = kb_event_mention.confidence
        results["frame"] = UnificationEventFrame(kb_event_mention, kb)
        return results

    def get_frame_types(self, external_ontology_sources):
        results = dict()
        for pair in external_ontology_sources:
            results[pair[0]] = pair[1]
        return results

    def get_argument_role(self, bbn_role):
        if bbn_role == "time" or bbn_role == "Time" or bbn_role == "has_time":
            return "has_time"
        if bbn_role == "involves_goods_or_property" or bbn_role == "located_at":
            return "http://ontology.causeex.com/ontology/odps/GeneralConcepts#" + bbn_role
        return "http://ontology.causeex.com/ontology/odps/Event#" + bbn_role

    def is_duplicate_of(self, other):
        if "trigger" not in self.evidence or "trigger" not in other.evidence:
            return False
        return self.evidence["trigger"].is_duplicate_of(other.evidence["trigger"])

    def merge_with(self, other):
        self.properties["confidence"] = max(self.properties["confidence"], other.properties["confidence"])

        for frame_type in other.frame_types.keys():
            if frame_type not in self.frame_types:
                self.frame_types[frame_type] = other.frame_types[frame_type]
            else:
                self.frame_types[frame_type] = max(self.frame_types[frame_type], other.frame_types[frame_type])

        for argument in other.arguments:
            if isinstance(argument, dict):
                # This is a has_topic event argument
                continue
            
            if not self.has_matching_argument(argument):
                self.arguments.append(argument)

    def has_matching_argument(self, event_argument):
        for argument in self.arguments:
            if argument.is_duplicate_of(event_argument):
                return True
        return False

