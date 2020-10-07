from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention
from elements.unification.unification_element import UnificationElement
from elements.unification.unification_event_argument import UnificationEventArgument
from elements.unification.unification_relation_argument import UnificationRelationArgument
from elements.unification.unification_provenance import UnificationProvenance
from elements.unification.unification_span import UnificationSpan
from elements.unification.unification_causal_factor import UnificationCausalFactor


class UnificationEventFrame(UnificationElement):
    def __init__(self, kb_event_mention, kb):
        self.arguments = []
        self.frame_types = self.get_frame_types(kb_event_mention.external_ontology_sources)
        self.causal_factors = self.get_causal_factors(kb_event_mention)

        for bbn_role, event_arguments in kb_event_mention.arguments.items():
            role = self.get_argument_role(bbn_role)

            for event_argument,arg_score in event_arguments:
                # position_or_role valuementions are dropped
                if (isinstance(event_argument, KBMention) or
                        (isinstance(event_argument, KBValueMention) and (
                                self.is_time_role(role)))):
                    self.arguments.append(UnificationEventArgument(role, event_argument, kb,arg_score))

        self.properties = dict()
        confidence = kb_event_mention.get_max_grounding_confidence()
        if confidence < 0.1:
            confidence = 0.1
        self.properties["confidence"] = confidence
        self.properties["polarity"] = kb_event_mention.properties["polarity"]
        self.evidence = dict()
        span = UnificationSpan.create_from_event_mention(kb_event_mention)
        if span:
            self.evidence["extended_trigger"] = span
        anchor_span = UnificationSpan.create_from_event_mention_anchor(kb_event_mention)
        if anchor_span:
            self.evidence["trigger"] = anchor_span

        self.evidence["sentence"] = UnificationSpan.create_from_sentence(
            kb_event_mention.sentence, kb_event_mention.document)

        self.docid = kb_event_mention.document.properties["uuid"]
        self.provenance = UnificationProvenance()

        # has_topic argument
        if kb_event_mention.has_topic:
            event_frame = UnificationEventFrame(kb_event_mention.has_topic, kb)
            unification_relation_argument = UnificationRelationArgument("http://ontology.causeex.com/ontology/odps/Event#has_topic", event_frame, kb_event_mention.has_topic.get_max_grounding_confidence())
            self.arguments.append(unification_relation_argument)

    @staticmethod
    def is_time_role(role):
        return role in ["has_time", "has_start_time", "has_end_time"]

    @staticmethod
    def mapped_role(role):
        mapping = {'Person': 'http://ontology.causeex.com/ontology/odps/Event#has_actor'}
        return mapping.get(role)

    @staticmethod
    def is_general_role(role):
        gen = ["involves_goods_or_property", "located_at", "position_or_role"]
        return role in gen

    def get_causal_factors(self, kb_event_mention):
        ret = []
        for kb_causal_factor in kb_event_mention.causal_factors:
            ret.append(UnificationCausalFactor(kb_causal_factor))
        return ret

    def get_frame_types(self, external_ontology_sources):
        results = dict()
        for pair in external_ontology_sources:
            results[pair[0]] = pair[1]
        return results

    def get_argument_role(self, bbn_role):
        if self.is_time_role(bbn_role):
            return "has_time"
        if self.is_general_role(bbn_role):
            return "http://ontology.causeex.com/ontology/odps/GeneralConcepts#" + bbn_role
        mapped_role = self.mapped_role(bbn_role)
        if mapped_role:
            return mapped_role
        return "http://ontology.causeex.com/ontology/odps/Event#" + bbn_role

    def is_duplicate_of(self, other):
        if "trigger" not in self.evidence or "trigger" not in other.evidence:
            return False
        if (self.has_topic() and not other.has_topic()) or (not self.has_topic() and other.has_topic()):
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
            if not self.has_matching_argument(argument):
                self.arguments.append(argument)

    def has_matching_argument(self, event_argument):
        for argument in self.arguments:
            if argument.is_duplicate_of(event_argument):
                return True
        return False

    def has_topic(self):
        for argument in self.arguments:
            if argument.role.endswith("has_topic"):
                return True
        return False
