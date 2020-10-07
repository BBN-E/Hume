import typing

from models import SerifAnnotationData


class Converter():

    def __init__(self, doc_id_to_doc_path: dict, list_serif_annotation_data: typing.List[SerifAnnotationData],
                 output_folder: str):
        self.doc_id_to_doc_path = doc_id_to_doc_path
        self.list_serif_annotation_data = list_serif_annotation_data
        self.output_folder = output_folder

    @staticmethod
    def single_document_worker(doc_path: str, serif_annotation_data: SerifAnnotationData):
        raise NotImplemented

    def convert(self):
        raise NotImplemented
