import enum
import json
import typing


class SerifAnnotationDataJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)


class Span():
    def __init__(self, start_char_off: int, end_char_off: int, sent_start_char_off: int, sent_end_char_off: int):
        self.start_char_off = start_char_off
        self.end_char_off = end_char_off
        self.sent_start_char_off = sent_start_char_off
        self.sent_end_char_off = sent_end_char_off

    def reprJSON(self):
        return {"start_char_off": self.start_char_off, "end_char_off": self.end_char_off,
                "sent_start_char_off": self.sent_start_char_off, "sent_end_char_off": self.sent_end_char_off}

    def __repr__(self):
        return str(self.reprJSON())

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.sent_start_char_off == other.sent_start_char_off and self.sent_end_char_off == other.sent_end_char_off and self.start_char_off == other.start_char_off and self.end_char_off == other.end_char_off

    def __hash__(self):
        return (self.start_char_off, self.end_char_off, self.sent_start_char_off, self.sent_end_char_off).__hash__()

    @staticmethod
    def fromDICT(input_dict):
        return Span(**input_dict)


class MarkingStatus(enum.Enum):
    FROZEN_GOOD = "FROZEN_GOOD"
    NO_FROZEN = "NO_FROZEN"
    FROZEN_BAD = "FROZEN_BAD"


class Marking():
    def __init__(self, label, status: MarkingStatus):
        self.label = label
        self.status = status

    def reprJSON(self):
        return {"label": self.label, 'status': self.status.value}

    @staticmethod
    def fromDICT(input_dict):
        return Marking(input_dict['label'], MarkingStatus(input_dict['status']))

    def __eq__(self, other):
        if not isinstance(other, Marking):
            return False
        return self.label == other.label and self.status == other.status

    def __hash__(self):
        return (self.label, self.status).__hash__()


class AnnotationEntry():
    def __init__(self, source: str, markings: typing.List[Marking] = None):
        self.source = source
        if markings is None:
            markings = []
        self.markings = markings

    def reprJSON(self):
        return {"source": self.source, "markings": self.markings}

    @staticmethod
    def fromDICT(input_dict):
        markings = list()
        for marking in input_dict.get('markings', list()):
            markings.append(Marking.fromDICT(marking))
        return AnnotationEntry(input_dict['source'], markings)


class NodeMentionAnnotation():
    def __init__(self, span: Span, annotation_entries: typing.List[AnnotationEntry] = None):
        self.span = span
        if annotation_entries is None:
            annotation_entries = []
        self.annotation_entries = annotation_entries

    def reprJSON(self):
        return {"span": self.span, "annotation_entries": self.annotation_entries}

    @staticmethod
    def fromDICT(input_dict: dict):
        span = Span.fromDICT(input_dict['span'])
        annotation_entries = list()
        for annotation_entry in input_dict.get('annotation_entries', list()):
            annotation_entries.append(AnnotationEntry.fromDICT(annotation_entry))
        return NodeMentionAnnotation(span, annotation_entries)


class EdgeMentionAnnotation():
    def __init__(self, left_span: Span, right_span: Span, annotation_entries: typing.List[AnnotationEntry] = None):
        self.left_span = left_span
        self.right_span = right_span
        if annotation_entries is None:
            annotation_entries = []
        self.annotation_entries = annotation_entries

    def reprJSON(self):
        return {"left_span": self.left_span, "right_span": self.right_span,
                "annotation_entries": self.annotation_entries}

    @staticmethod
    def fromDICT(input_dict: dict):
        left_span = Span.fromDICT(input_dict['left_span'])
        right_span = Span.fromDICT(input_dict['right_span'])
        annotation_entries = list()
        for annotation_entry in input_dict.get('annotation_entries', list()):
            annotation_entries.append(AnnotationEntry.fromDICT(annotation_entry))
        return EdgeMentionAnnotation(left_span, right_span, annotation_entries)


class SerifAnnotationData():
    def __init__(self, doc_id: str, event_mentions: typing.List[NodeMentionAnnotation] = None,
                 event_event_relation_mentions: typing.List[EdgeMentionAnnotation] = None,
                 event_event_argument_relation_mentions: typing.List[EdgeMentionAnnotation] = None):
        self.doc_id = doc_id
        if event_mentions is None:
            event_mentions = []
        self.event_mentions = event_mentions
        if event_event_relation_mentions is None:
            event_event_relation_mentions = []
        self.event_event_relation_mentions = event_event_relation_mentions
        if event_event_argument_relation_mentions is None:
            event_event_argument_relation_mentions = []
        self.event_event_argument_relation_mentions = event_event_argument_relation_mentions

    def reprJSON(self):
        return {"doc_id": self.doc_id, "event_mentions": self.event_mentions,
                "event_event_relation_mentions": self.event_event_relation_mentions,
                'event_event_argument_relation_mentions': self.event_event_argument_relation_mentions,
                "@class": ".SerifAnnotationData"}

    @staticmethod
    def fromDICT(input_dict: dict):
        doc_id = input_dict['doc_id']
        event_mentions = list()
        for event_mention in input_dict.get('event_mentions', list()):
            event_mentions.append(NodeMentionAnnotation.fromDICT(event_mention))
        event_event_relation_mentions = list()
        for event_event_relation_mention in input_dict.get('event_event_relation_mentions', list()):
            event_event_relation_mentions.append(EdgeMentionAnnotation.fromDICT(event_event_relation_mention))
        event_event_argument_relation_mentions = list()
        for event_event_argument_relation_mention in input_dict.get('event_event_argument_relation_mentions', list()):
            event_event_argument_relation_mentions.append(
                EdgeMentionAnnotation.fromDICT(event_event_argument_relation_mention))
        return SerifAnnotationData(doc_id, event_mentions, event_event_relation_mentions,
                                   event_event_argument_relation_mentions)

    def write_serif_annotation_json(self, output_json_path):
        with open(output_json_path, 'w') as fp:
            json.dump(self, fp, ensure_ascii=False, cls=SerifAnnotationDataJSONEncoder, indent=4, sort_keys=True)

    @staticmethod
    def read_serif_annotation_json(input_json_path):
        with open(input_json_path) as fp:
            j = json.load(fp)
        return SerifAnnotationData.fromDICT(j)
