import typing

from judgers import Judger, NodeMentionAnnotation, EdgeMentionAnnotation
from models import AnnotationEntry,MarkingStatus,Marking


class AllNegativeToNAPositive(Judger):
    def judge(self, serif_annotation_en_ptr: typing.Union[NodeMentionAnnotation, EdgeMentionAnnotation]):
        new_annotation_entries = list()

        for annotation_entry in serif_annotation_en_ptr.annotation_entries:
            new_annotation_entry = AnnotationEntry(annotation_entry.source+"_ONLY_POSITIVE_NA")
            only_negative_existed = True
            for marking in annotation_entry.markings:
                status = marking.status
                if status is not MarkingStatus.FROZEN_BAD:
                    only_negative_existed = False
                    break
            if only_negative_existed is True and len(annotation_entry.markings) > 0:
                new_annotation_entry.markings.append(Marking("NA",MarkingStatus.FROZEN_GOOD))
                new_annotation_entries.append(new_annotation_entry)

        serif_annotation_en_ptr.annotation_entries.clear()
        serif_annotation_en_ptr.annotation_entries.extend(new_annotation_entries)