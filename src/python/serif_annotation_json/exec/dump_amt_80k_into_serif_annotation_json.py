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


from models import SerifAnnotationData, MarkingStatus, AnnotationEntry, Span, Marking, NodeMentionAnnotation


def get_or_create_event_mention_annotation(list_of_event_mentions: typing.List[NodeMentionAnnotation], span):
    for event_mention in list_of_event_mentions:
        if event_mention.span == span:
            return event_mention
    event_mention = NodeMentionAnnotation(span)
    list_of_event_mentions.append(event_mention)
    return event_mention


def get_or_create_annotation_entry(list_of_annotation_entries: typing.List[AnnotationEntry], source):
    for annotation_entry in list_of_annotation_entries:
        if source == annotation_entry.source:
            return annotation_entry
    annotation_entry = AnnotationEntry(source)
    list_of_annotation_entries.append(annotation_entry)
    return annotation_entry


def main():
    scs_doc_list_path = "/nfs/raid87/u11/users/hqiu/runjob/expts/Hume/causeex_scs.v1.051619/generic_events_serifxml_out.list"
    gigaword_list_path = "/nfs/e-nfs-03/home/jfaschin/gigaword_400K.list"
    scs_doc_id_to_doc_path = dict()
    with open(scs_doc_list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id.replace(".xml", "")
            scs_doc_id_to_doc_path[doc_id] = i
    gigaword_doc_id_to_doc_path = dict()
    with open(gigaword_list_path) as fp:
        for i in fp:
            i = i.strip()
            doc_id = os.path.basename(i)
            doc_id = doc_id.replace(".xml", "")
            gigaword_doc_id_to_doc_path[doc_id] = i

    event_annotation_file = "/nfs/raid88/u10/users/hqiu/annotation/amt/event/062119/batch_0_90.json"
    with open(event_annotation_file) as fp:
        src_json = json.load(fp)

    doc_id_to_span_to_marking = dict()

    for annotation_en in src_json:
        if "gold_label" in annotation_en.keys():
            continue
        candidate_types = set(annotation_en['candidate_event_types'])
        for annotation in annotation_en['annotation']:
            event_type = annotation['event_type']
            if event_type is None or pandas.isna(event_type):
                event_type = "NA"
            for candidate_type in candidate_types:
                doc_id_to_span_to_marking.setdefault(annotation_en['docid'], dict()).setdefault(
                    Span(annotation_en['start'], annotation_en['end'] - 1, annotation_en['sent_start'],
                         annotation_en['sent_end']), dict()).setdefault("AMT_TURKER/{}".format(annotation['id']),
                                                                        list()).append(Marking(candidate_type,
                                                                                               MarkingStatus.FROZEN_GOOD if event_type == candidate_type else MarkingStatus.FROZEN_BAD))

    for doc_id, span_to_marking in doc_id_to_span_to_marking.items():
        output_folder = None
        if doc_id in scs_doc_id_to_doc_path.keys():
            output_folder = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/cx_scs"
        if doc_id in gigaword_doc_id_to_doc_path.keys():
            output_folder = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/gigaword"
        possible_serif_annotation_json_path = os.path.join(output_folder, doc_id + ".json")
        if os.path.isfile(possible_serif_annotation_json_path):
            serif_annotation_data = SerifAnnotationData.read_serif_annotation_json(possible_serif_annotation_json_path)
        else:
            serif_annotation_data = SerifAnnotationData(doc_id)
        for span, markings in span_to_marking.items():
            for turker_id, markings in markings.items():
                event_mention = get_or_create_event_mention_annotation(serif_annotation_data.event_mentions, span)
                annotation_entry = get_or_create_annotation_entry(event_mention.annotation_entries, turker_id)
                annotation_entry.markings.clear()
                annotation_entry.markings.extend(markings)
        serif_annotation_data.write_serif_annotation_json(possible_serif_annotation_json_path)


if __name__ == "__main__":
    main()
