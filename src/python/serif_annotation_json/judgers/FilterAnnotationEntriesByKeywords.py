import typing

from judgers import Judger, NodeMentionAnnotation, EdgeMentionAnnotation


class FilterAnnotationEntriesByKeywords(Judger):
    def __init__(self, keyword_set: iter):
        self.keyword_set = set(keyword_set)

    def judge(self, serif_annotation_en_ptr: typing.Union[NodeMentionAnnotation, EdgeMentionAnnotation]):

        new_annotation_entries = list()

        for annotation_entry in serif_annotation_en_ptr.annotation_entries:
            should_add = False
            for keyword in self.keyword_set:
                if keyword in annotation_entry.source:
                    should_add = True
            if should_add is True:
                new_annotation_entries.append(annotation_entry)

        serif_annotation_en_ptr.annotation_entries.clear()
        serif_annotation_en_ptr.annotation_entries.extend(new_annotation_entries)
