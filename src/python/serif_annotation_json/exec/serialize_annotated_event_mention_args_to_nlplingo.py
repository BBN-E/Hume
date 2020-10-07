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
    # Stage 1, AMT
    amt_doc_id_to_doc_path = read_doc_list_from_file_list_or_file_list_folder(
        '/nfs/raid88/u10/users/ychan/generic_arguments_corpus/filelists/batch0.filelist.deduplicated')
    amt_serif_annotation_data_list = list()
    amt_serif_json_root = "/nfs/raid88/u10/users/hqiu/annotation/serif_annotation_json/unmerged/amt_0819_event_arg_task"
    for file in os.listdir(amt_serif_json_root):
        amt_serif_annotation_data_list.append(
            SerifAnnotationData.read_serif_annotation_json(os.path.join(amt_serif_json_root, file)))

    # Get Majority Voting
    majority_judger = AMTMajorityVotingJudger()
    filter_by_keyword_judger = FilterAnnotationEntriesByKeywords({"AMT_RESOLVED"})
    for serif_annotation_data in amt_serif_annotation_data_list:
        for event_mention_arg_annotation in serif_annotation_data.event_event_argument_relation_mentions:
            majority_judger.judge(event_mention_arg_annotation)
            filter_by_keyword_judger.judge(event_mention_arg_annotation)

    # Stage 2, Serialize
    # output_folder = "/nfs/raid88/u10/users/hqiu/tmp/serialization_test"
    nlplingo_converter = NLPLingoConverter(amt_doc_id_to_doc_path, amt_serif_annotation_data_list,
                                           output_folder, TriggerOrRole.Role, should_output_negative=True)
    nlplingo_converter.convert()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_folder', required=True)
    args = parser.parse_args()
    output_folder = args.output_folder
    main(output_folder)
