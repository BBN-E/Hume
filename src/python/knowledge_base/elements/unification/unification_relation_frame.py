from elements.kb_relation_mention import KBRelationMention
from unification_relation_argument import UnificationRelationArgument
from unification_provenance import UnificationProvenance
from unification_span import UnificationSpan
from unification_element import UnificationElement

class UnificationRelationFrame(UnificationElement):

    type_to_left_arg_role = \
        {
        "MitigatingFactor-Effect": "has_mitigating_factor",
        "Cause-Effect": "has_cause",
        "Catalyst-Effect": "has_catalyst",
        "Precondition-Effect": "has_precondition",
        "Preventative-Effect": "has_preventative"
        }
        
    def __init__(self, kb_relation, kb_relation_mention, kb):
        self.frame_types = dict()
        self.arguments = []
        
        self.frame_types["http://ontology.causeex.com/ontology/odps/CauseEffect#CausalAssertion"] = kb_relation_mention.confidence

        # Left argument
        role = self.get_argument_role(kb_relation, "left")
        event_mention = kb_relation_mention.left_mention
        self.arguments.append(UnificationRelationArgument(role, event_mention, kb))
        
        # Right argument
        role = self.get_argument_role(kb_relation, "right")
        event_mention = kb_relation_mention.right_mention
        self.arguments.append(UnificationRelationArgument(role, event_mention, kb))

        self.properties = dict()
        self.properties["confidence"] = kb_relation_mention.confidence
        self.evidence = dict()
        self.evidence["sentence"] = UnificationSpan.create_from_sentence( 
            kb_relation_mention.left_mention.sentence, kb_relation_mention.document)
        self.docid = kb_relation_mention.document.properties["uuid"]
        self.provenance = UnificationProvenance()

    def merge_with(self, other):
        for frame_type in other.frame_types.keys():
            if frame_type not in self.frame_types:
                self.frame_types[frame_type] = other.frame_types[frame_type]
            else:
                self.frame_types[frame_type] = max(self.frame_types[frame_type], other.frame_types[frame_type])
            
        self.properties["confidence"] = max(self.properties["confidence"], other.properties["confidence"])
        
        if self.arguments[0].is_duplicate_of(other.arguments[0]):
            self.arguments[0].merge_with(other.arguments[0])

        if self.arguments[0].is_duplicate_of(other.arguments[1]):
            self.arguments[0].merge_with(other.arguments[1])

        if self.arguments[1].is_duplicate_of(other.arguments[0]):
            self.arguments[1].merge_with(other.arguments[0])

        if self.arguments[1].is_duplicate_of(other.arguments[1]):
            self.arguments[1].merge_with(other.arguments[1])
    
    def get_argument_role(self, kb_relation, arg_indicator):
        suffix = None
        if arg_indicator == "right":
            suffix = "has_effect"
        if arg_indicator == "left":
            relation_type = kb_relation.relation_type
            suffix = UnificationRelationFrame.type_to_left_arg_role[relation_type]

        return "http://ontology.causeex.com/ontology/odps/CauseEffect#" + suffix

    def is_duplicate_of(self, other):
        if len(self.arguments) != 2 or len(other.arguments) != 2:
            print "Bad arguemnts in relation frame!"
            sys.exit(1)

        if ((self.arguments[0].is_duplicate_of(other.arguments[0]) and self.arguments[1].is_duplicate_of(other.arguments[1])) or
            (self.arguments[0].is_duplicate_of(other.arguments[1]) and self.arguments[1].is_duplicate_of(other.arguments[0]))):
            return True

        return False

