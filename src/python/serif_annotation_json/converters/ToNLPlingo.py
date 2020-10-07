import collections
import enum
import os
import shutil
import sys
import typing

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.insert(0, project_root)
from converters import Converter
from util.nlplingo_const import Entity_type_str, generate_nlplingo_training_parameter_str
from util.read_serif_list import read_doc_list_from_file_list_or_file_list_folder


Span = collections.namedtuple('Span', ['start_char_off', 'end_char_off'])
EventMentionSpan = collections.namedtuple('EventMentionSpan', ['doc_id', 'sent_span', 'trigger_span'])
EventMentionArgSpan = collections.namedtuple('EventMentionArgSpan', ['event_mention', 'sent_span', 'arg_span'])

from models import SerifAnnotationData, MarkingStatus


class TriggerOrRole(enum.Enum):
    Trigger = "Trigger"
    Role = "Role"


class NLPLingoConverter(Converter):
    def __init__(self, doc_id_to_doc_path: dict, list_serif_annotation_data: typing.List[SerifAnnotationData],
                 output_folder: str, trigger_or_role: TriggerOrRole, should_output_negative=True):
        super().__init__(doc_id_to_doc_path, list_serif_annotation_data, output_folder)
        self.triggle_or_role = trigger_or_role
        self.output_negative_examples = should_output_negative

    def convert(self):
        shutil.rmtree(self.output_folder, ignore_errors=True)
        os.makedirs(self.output_folder)
        doc_id_to_event_mention_to_event_arg = dict()
        sent_span_set = set()

        positive_event_cnt = 0
        for doc_annotation in self.list_serif_annotation_data:
            if self.triggle_or_role == TriggerOrRole.Trigger:
                for event_mention in doc_annotation.event_mentions:
                    event_trigger_key = EventMentionSpan(doc_annotation.doc_id,
                                                         Span(event_mention.span.sent_start_char_off,
                                                              event_mention.span.sent_end_char_off),
                                                         Span(event_mention.span.start_char_off,
                                                              event_mention.span.end_char_off))
                    event_arg_key = EventMentionArgSpan(event_trigger_key, Span(event_mention.span.sent_start_char_off,
                                                                                event_mention.span.sent_end_char_off),
                                                        Span(event_mention.span.start_char_off,
                                                             event_mention.span.end_char_off))

                    for annotation_entry in event_mention.annotation_entries:
                        for marking in annotation_entry.markings:
                            event_type = marking.label
                            doc_id_to_event_mention_to_event_arg.setdefault(event_trigger_key.doc_id,
                                                                            dict()).setdefault(
                                (event_trigger_key, event_type), set()).add(
                                ("trigger", event_arg_key,
                                 True if event_type != "NA" and marking.status == MarkingStatus.FROZEN_GOOD else False))
            if self.triggle_or_role == TriggerOrRole.Role:
                for event_mention_to_event_role in doc_annotation.event_event_argument_relation_mentions:
                    event_trigger_key = EventMentionSpan(doc_annotation.doc_id,
                                                         Span(event_mention_to_event_role.left_span.sent_start_char_off,
                                                              event_mention_to_event_role.left_span.sent_end_char_off),
                                                         Span(event_mention_to_event_role.left_span.start_char_off,
                                                              event_mention_to_event_role.left_span.end_char_off))
                    event_arg_key = EventMentionArgSpan(event_trigger_key,
                                                        Span(event_mention_to_event_role.right_span.sent_start_char_off,
                                                             event_mention_to_event_role.right_span.sent_end_char_off),
                                                        Span(event_mention_to_event_role.right_span.start_char_off,
                                                             event_mention_to_event_role.right_span.end_char_off))
                    for annotation_entry in event_mention_to_event_role.annotation_entries:
                        for marking in annotation_entry.markings:
                            event_role_type = marking.label
                            doc_id_to_event_mention_to_event_arg.setdefault(event_trigger_key.doc_id,
                                                                            dict()).setdefault(
                                (event_trigger_key, "Event"), set()).add(
                                (event_role_type, event_arg_key,
                                 True if event_role_type != "NA" and marking.status == MarkingStatus.FROZEN_GOOD else False))

        current_working_folder = self.output_folder
        event_type_to_trigger_word_mapping = dict()
        span_file_serif_path_output_buffer = dict()
        argument_type_set = set()
        for doc_id in doc_id_to_event_mention_to_event_arg.keys():
            potential_span_file_path = os.path.join(current_working_folder, doc_id + ".span")
            serifxml_path = self.doc_id_to_doc_path[doc_id]
            for event_mention_id, event_mention_type in doc_id_to_event_mention_to_event_arg[doc_id].keys():
                output_buffer = list()
                should_output = False
                trigger_positive = True
                for event_arg in doc_id_to_event_mention_to_event_arg[doc_id][(event_mention_id, event_mention_type)]:
                    should_output = True
                    argument_type, arg_span, positive = event_arg
                    argument_start_char, argument_end_char = arg_span.arg_span.start_char_off, arg_span.arg_span.end_char_off
                    if argument_type != "trigger" and positive == True:
                        argument_type_set.add(argument_type)
                        output_buffer.append(
                            "{}/{} {} {}\n".format(event_mention_type, argument_type, argument_start_char,
                                                   argument_end_char + 1))
                    if argument_type == "trigger" and positive == False:
                        trigger_positive = False
                ptr_to_span_file_output_buffer = span_file_serif_path_output_buffer.setdefault(
                        (potential_span_file_path, serifxml_path, doc_id), list())
                if self.output_negative_examples is True:
                    event_type_to_trigger_word_mapping.setdefault(event_mention_type, list())

                    sent_span_set.add((doc_id, event_mention_id.sent_span.start_char_off,
                                       event_mention_id.sent_span.end_char_off + 1))

                if should_output is True and trigger_positive is True:
                    if self.output_negative_examples is False:
                        sent_span_set.add((doc_id, event_mention_id.sent_span.start_char_off,
                                           event_mention_id.sent_span.end_char_off + 1))

                    event_type_to_trigger_word_mapping.setdefault(event_mention_type, list())
                    ptr_to_span_file_output_buffer.append("<Event type=\"{}\">\n".format(event_mention_type))
                    ptr_to_span_file_output_buffer.append(
                        "{} {} {}\n".format(event_mention_type, event_mention_id.sent_span.start_char_off,
                                            event_mention_id.sent_span.end_char_off + 1))

                    if len(output_buffer) > 0:
                        ptr_to_span_file_output_buffer.extend(output_buffer)
                    positive_event_cnt += 1
                    ptr_to_span_file_output_buffer.append(
                        "anchor {} {}\n".format(event_mention_id.trigger_span.start_char_off,
                                                event_mention_id.trigger_span.end_char_off + 1))
                    ptr_to_span_file_output_buffer.append("</Event>\n")

        # Do Some check on project before you change this name "argument.span_serif_list", "argument.sent_spans","argument.sent_spans.list","argument.sent_spans"
        with open(os.path.join(current_working_folder, 'argument.span_serif_list'), 'w') as booking_fp:
            for k, v in span_file_serif_path_output_buffer.items():
                span_file_path, serifxml_path, doc_id = k
                booking_fp.write("SPAN:{} SERIF:{}\n".format(os.path.join(current_working_folder, doc_id + ".span"),
                                                             self.doc_id_to_doc_path.get(doc_id)))
                with open(span_file_path, 'w') as span_fp:
                    for output_item in v:
                        span_fp.write(output_item)
        with open(os.path.join(current_working_folder, 'argument.sent_spans'), 'w') as fp:
            for i in sent_span_set:
                fp.write("{} {} {}\n".format(i[0], i[1], i[2]))
        with open(os.path.join(current_working_folder, 'argument.sent_spans.list'), 'w') as fp:
            fp.write(os.path.join(current_working_folder, 'argument.sent_spans'))
        with open(os.path.join(current_working_folder, 'domain_ontology.txt'), 'w') as fp:
            for event_type in event_type_to_trigger_word_mapping.keys():
                fp.write("<Event type=\"{}\">\n".format(event_type))
                for argument_type in argument_type_set:
                    fp.write("<Role>{}</Role>\n".format(argument_type))
                fp.write("</Event>\n")
            fp.write(Entity_type_str)
        os.makedirs(os.path.join(current_working_folder, 'nlplingo_out'), exist_ok=True)
        with open(os.path.join(current_working_folder, 'params'), 'w') as fp:
            fp.write(
                generate_nlplingo_training_parameter_str(current_working_folder,
                                                         os.path.join(current_working_folder, 'nlplingo_out')))
        shutil.copy(os.path.join(current_working_folder, 'domain_ontology.txt'),
                    os.path.join(current_working_folder, 'nlplingo_out'))


def main():
    json_root = "/home/hqiu/ld100/learnit/expts/causeex_m17_test.v4/serialization_out/event_argument_has_location"
    serif_annotation_data_list = list()
    for file in os.listdir(json_root):
        serif_annotation_data_list.append(SerifAnnotationData.read_serif_annotation_json(os.path.join(json_root, file)))
    serif_list = "/home/hqiu/ld100/Hume_pipeline/Hume/expts/causeex_m17_5files_test.v1/grounded_serifxml.list"
    doc_id_to_serif_path_map = read_doc_list_from_file_list_or_file_list_folder(serif_list)
    output_folder = "/nfs/raid88/u10/users/hqiu/tmp/nlplingo_argument_serialization_test"
    converter = NLPLingoConverter(doc_id_to_serif_path_map, serif_annotation_data_list, output_folder,
                                  TriggerOrRole.Role, False)
    converter.convert()


if __name__ == "__main__":
    main()
