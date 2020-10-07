import typing

from judgers import Judger, NodeMentionAnnotation, EdgeMentionAnnotation
from models import AnnotationEntry, Marking


def get_or_create_annotation_entry(list_of_annotation_entries: typing.List[AnnotationEntry], source):
    for annotation_entry in list_of_annotation_entries:
        if source == annotation_entry.source:
            return annotation_entry
    annotation_entry = AnnotationEntry(source)
    list_of_annotation_entries.append(annotation_entry)
    return annotation_entry

class AMTMajorityVotingJudger(Judger):
    def judge(self, serif_annotation_en_ptr: typing.Union[NodeMentionAnnotation, EdgeMentionAnnotation]):
        turker_set = set()

        label_to_cnt = dict()

        for annotation_entry in serif_annotation_en_ptr.annotation_entries:
            if "AMT_TURKER/" in annotation_entry.source:
                turker_set.add(annotation_entry.source)
                for marking in annotation_entry.markings:
                    label_to_cnt[(marking.label, marking.status)] = label_to_cnt.get((marking.label, marking.status),
                                                                                     0) + 1

        annotation_entry = get_or_create_annotation_entry(serif_annotation_en_ptr.annotation_entries, "AMT_RESOLVED")
        annotation_entry.markings.clear()
        for mark, cnt in label_to_cnt.items():
            label, status = mark
            if cnt / len(turker_set) > 0.5:
                annotation_entry.markings.append(Marking(label, status))
