import json
import os
import sys
import typing

import pandas

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.insert(0, project_root)

# Span = collections.namedtuple('Span', ['start_char_off', 'end_char_off'])
# EventMentionSpan = collections.namedtuple('EventMentionSpan', ['doc_id', 'sent_span', 'trigger_span'])
# EventMentionArgSpan = collections.namedtuple('EventMentionArgSpan', ['event_mention', 'arg_span'])


from models import SerifAnnotationData, MarkingStatus, AnnotationEntry, Span, Marking, EdgeMentionAnnotation


def get_or_create_event_argument_mention_annotation(list_of_event_argument_mentions: typing.List[EdgeMentionAnnotation],
                                                    left_span, right_span):
    for event_arg_mention in list_of_event_argument_mentions:
        if event_arg_mention.left_span == left_span and event_arg_mention.right_span == right_span:
            return event_arg_mention
    event_arg_mention = EdgeMentionAnnotation(left_span, right_span)
    list_of_event_argument_mentions.append(event_arg_mention)
    return event_arg_mention


def get_or_create_annotation_entry(list_of_annotation_entries: typing.List[AnnotationEntry], source):
    for annotation_entry in list_of_annotation_entries:
        if source == annotation_entry.source:
            return annotation_entry
    annotation_entry = AnnotationEntry(source)
    list_of_annotation_entries.append(annotation_entry)
    return annotation_entry


def main():
    arg_role_mappings = {
        "Location": "Location",
        "Affected": "Affected",
        "Participant": "Participant",
        "Destination Location": "DestinationLocation",
        "End Time": "EndTime",
        "Actor": "Actor",
        "Source Location": "SourceLocation",
        "Start Time": "StartTime",
        "Intermediate Location": "IntermediateLocation",
        "Time": "Time",
        "NA": "NA",
        "Artifact": "Artifact"
    }

    serif_list_path = "/nfs/raid88/u10/users/ychan/generic_arguments_corpus/filelists/batch0.filelist.deduplicated"
    serif_doc_id_to_doc_path = dict()
    with open(serif_list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id.replace(".xml", "").replace(".serifxml", "")
            serif_doc_id_to_doc_path[doc_id] = i

    event_argument_annotation_file = "/nfs/raid88/u10/users/hqiu/annotation/amt/eventarg/080919/resolved_080919.json"
    with open(event_argument_annotation_file) as fp:
        src_json = json.load(fp)

    doc_id_to_span_to_marking = dict()

    for annotation_en in src_json:
        candidate_types = {arg_role_mappings[i] for i in annotation_en['argument_roles']}
        if "gold_label" in annotation_en.keys():
            chosen_arg_role_type = arg_role_mappings[annotation_en['gold_label']]
            if chosen_arg_role_type is None or pandas.isna(chosen_arg_role_type):
                chosen_arg_role_type = "NA"
            for candidate_type in candidate_types:
                doc_id_to_span_to_marking.setdefault(annotation_en['docid'], dict()).setdefault(
                    (Span(annotation_en['trigger_start'], annotation_en['trigger_end'], annotation_en['sent_start'],
                          annotation_en['sent_end']),
                     Span(annotation_en['argument_start'], annotation_en['argument_end'], annotation_en['sent_start'],
                          annotation_en['sent_end'])), dict()).setdefault("AMT_TURKER/GOLDEN",
                                                                          list()).append(Marking(candidate_type,
                                                                                                 MarkingStatus.FROZEN_GOOD if chosen_arg_role_type == candidate_type else MarkingStatus.FROZEN_BAD))
            continue

        for annotation in annotation_en['annotation']:
            chosen_arg_role_type = arg_role_mappings[annotation['event_argument_role']]
            if chosen_arg_role_type is None or pandas.isna(chosen_arg_role_type):
                chosen_arg_role_type = "NA"
            for candidate_type in candidate_types:
                doc_id_to_span_to_marking.setdefault(annotation_en['docid'], dict()).setdefault(
                    (Span(annotation_en['trigger_start'], annotation_en['trigger_end'], annotation_en['sent_start'],
                          annotation_en['sent_end']),
                     Span(annotation_en['argument_start'], annotation_en['argument_end'], annotation_en['sent_start'],
                          annotation_en['sent_end'])), dict()).setdefault("AMT_TURKER/{}".format(annotation['id']),
                                                                          list()).append(Marking(candidate_type,
                                                                                                 MarkingStatus.FROZEN_GOOD if chosen_arg_role_type == candidate_type else MarkingStatus.FROZEN_BAD))

    for doc_id, span_to_marking in doc_id_to_span_to_marking.items():
        output_folder = None
        if doc_id in serif_doc_id_to_doc_path.keys():
            output_folder = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/unmerged/amt_0819_event_arg_task"
        possible_serif_annotation_json_path = os.path.join(output_folder, doc_id + ".json")
        if os.path.isfile(possible_serif_annotation_json_path):
            serif_annotation_data = SerifAnnotationData.read_serif_annotation_json(possible_serif_annotation_json_path)
        else:
            serif_annotation_data = SerifAnnotationData(doc_id)
        for span, markings in span_to_marking.items():
            left_span, right_span = span
            for turker_id, markings in markings.items():
                event_mention_arg = get_or_create_event_argument_mention_annotation(
                    serif_annotation_data.event_event_argument_relation_mentions, left_span, right_span)
                annotation_entry = get_or_create_annotation_entry(event_mention_arg.annotation_entries, turker_id)
                annotation_entry.markings.clear()
                annotation_entry.markings.extend(markings)
        serif_annotation_data.write_serif_annotation_json(possible_serif_annotation_json_path)


if __name__ == "__main__":
    main()
