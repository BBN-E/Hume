import os
import sys

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir))
sys.path.insert(0, project_root)

from models import SerifAnnotationData
from converters.ToNLPlingo import NLPLingoConverter, TriggerOrRole
from util.read_serif_list import read_doc_list_from_file_list_or_file_list_folder
from judgers.AMTMarjorityVoting import AMTMajorityVotingJudger
from judgers.FilterAnnotationEntriesByKeywords import FilterAnnotationEntriesByKeywords


def main(output_folder):
    # Stage 1, legacy
    legacy_doc_id_to_doc_path = read_doc_list_from_file_list_or_file_list_folder(
        "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/legacy_cx.list")
    legacy_serif_annotation_data_list = list()
    legacy_serif_annotation_dir = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/legacy_cx"
    for file in os.listdir(legacy_serif_annotation_dir):
        path = os.path.join(legacy_serif_annotation_dir, file)
        legacy_serif_annotation_data_list.append(SerifAnnotationData.read_serif_annotation_json(path))

    # Do not do anything here

    # Stage 2, AMT 80K
    amt_doc_id_to_doc_path = read_doc_list_from_file_list_or_file_list_folder(
        '/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/cx_scs.list')
    tmp = read_doc_list_from_file_list_or_file_list_folder(
        "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/gigaword_400K.list")
    amt_doc_id_to_doc_path.update(tmp)
    amt_serif_annotation_data_list = list()
    gigaword_root = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/gigaword"
    for file in os.listdir(gigaword_root):
        amt_serif_annotation_data_list.append(
            SerifAnnotationData.read_serif_annotation_json(os.path.join(gigaword_root, file)))
    cx_scs_root = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/cx_scs"
    for file in os.listdir(cx_scs_root):
        amt_serif_annotation_data_list.append(
            SerifAnnotationData.read_serif_annotation_json(os.path.join(cx_scs_root, file)))

    # Get Majority Voting
    majority_judger = AMTMajorityVotingJudger()
    filter_by_keyword_judger = FilterAnnotationEntriesByKeywords({"AMT_RESOLVED"})
    for serif_annotation_data in amt_serif_annotation_data_list:
        for event_mention_annotation in serif_annotation_data.event_mentions:
            majority_judger.judge(event_mention_annotation)
            filter_by_keyword_judger.judge(event_mention_annotation)

    # Stage 3, Merge
    total_serif_annotation_data = list()
    total_serif_annotation_data.extend(legacy_serif_annotation_data_list)
    total_serif_annotation_data.extend(amt_serif_annotation_data_list)
    total_doc_id_to_doc = dict()
    total_doc_id_to_doc.update(legacy_doc_id_to_doc_path)
    total_doc_id_to_doc.update(amt_doc_id_to_doc_path)

    # Stage 4, Serialize
    # output_folder = "/nfs/raid88/u10/users/hqiu/tmp/serialization_test"
    nlplingo_converter = NLPLingoConverter(total_doc_id_to_doc, total_serif_annotation_data,
                                           output_folder, TriggerOrRole.Trigger, should_output_negative=True)
    nlplingo_converter.convert()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_folder', required=True)
    args = parser.parse_args()
    output_folder = args.output_folder
    main(output_folder)
