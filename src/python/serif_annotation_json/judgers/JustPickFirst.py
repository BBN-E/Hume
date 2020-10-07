import typing

from judgers import Judger, NodeMentionAnnotation, EdgeMentionAnnotation
from models import AnnotationEntry


class JustPickFirst(Judger):
    def judge(self, serif_annotation_en_ptr: typing.Union[NodeMentionAnnotation, EdgeMentionAnnotation]):

        new_annotation_entries = list()

        for annotation_entry in serif_annotation_en_ptr.annotation_entries:
            if len(annotation_entry.markings) > 0:
                marking = annotation_entry.markings[0]
                new_annotation_entry = AnnotationEntry(annotation_entry.source, [marking])
                new_annotation_entries.append(new_annotation_entry)
            break

        serif_annotation_en_ptr.annotation_entries.clear()
        serif_annotation_en_ptr.annotation_entries.extend(new_annotation_entries)
