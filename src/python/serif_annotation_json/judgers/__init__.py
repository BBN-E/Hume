import typing

from models import NodeMentionAnnotation, EdgeMentionAnnotation


class Judger():
    def judge(self, serif_annotation_en_ptr: typing.Union[NodeMentionAnnotation, EdgeMentionAnnotation]):
        raise NotImplemented
