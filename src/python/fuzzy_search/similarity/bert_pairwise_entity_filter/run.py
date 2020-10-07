import json
import os
import pickle
import sys

current_script_path = __file__
project_root = os.path.realpath(os.path.join(current_script_path, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

from similarity.bert_pairwise_entity_filter.serif_bert_feature_extractor import BertSerifSingleDocumentFeatureExtractor, \
    MyEventMentionFeature
from similarity.bert_pairwise_entity_filter.query_bert_feature_extractor import QueryFeatureExtractor, MyQueryFeature
from similarity.bert_pairwise_entity_filter.cosine_similarity import CosineSimilarityModule
from similarity.bert_pairwise_entity_filter.entity_constraint_filter import EntityConstraintFilter
from similarity.bert_pairwise_entity_filter.dumper import ReportDumper
from similarity.utils import ComplexEncoder


def create_doc_id_to_path(file_list, extension):
    docid_to_path = dict()
    with open(file_list) as fp:
        for i in fp:
            i = i.strip()
            docid = os.path.basename(i).replace(extension, "")
            docid_to_path[docid] = i
    return docid_to_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', required=True)
    parser.add_argument('--output_path', required=True)

    parser.add_argument('--input_serif_list', required=False)
    parser.add_argument('--input_serif_npz_list', required=False)

    parser.add_argument('--input_query_serif_list', required=False)
    parser.add_argument('--input_query_npz_list', required=False)

    parser.add_argument('--input_doc_feature_list', required=False)
    parser.add_argument('--input_query_feature_list', required=False)
    parser.add_argument('--query_result', required=False)

    parser.add_argument('--metric',required=False)
    parser.add_argument('--n_trees',required=False,type=int)

    args = parser.parse_args()
    if args.mode == "BUILD_FEATURE_FOR_CORPUS":
        doc_id_to_serif_path = create_doc_id_to_path(args.input_serif_list, ".xml")
        doc_id_to_npz_path = create_doc_id_to_path(args.input_serif_npz_list, ".npz")
        only_doc_id = list(doc_id_to_serif_path.keys())[0]

        if only_doc_id in doc_id_to_npz_path.keys():
            extractor = BertSerifSingleDocumentFeatureExtractor(doc_id_to_serif_path[only_doc_id],
                                                                doc_id_to_npz_path[only_doc_id])

            features = extractor.extract()
        else:
            features = list()
        with open(os.path.join(args.output_path, only_doc_id + "_complex.json"), 'w') as fp:
            json.dump(features, fp, cls=ComplexEncoder, ensure_ascii=False)
        with open(os.path.join(args.output_path, only_doc_id + "_simple.json"), 'w') as fp:
            json.dump([i.reprSimpleJSON() for i in features], fp, ensure_ascii=False)

    if args.mode == "BUILD_FEATURE_FOR_QUERY":
        query_doc_id_to_serif_path = create_doc_id_to_path(args.input_query_serif_list, ".xml")
        query_doc_id_to_npz_path = create_doc_id_to_path(args.input_query_npz_list, ".npz")
        for query_doc_id in query_doc_id_to_serif_path.keys():
            extractor = QueryFeatureExtractor(query_doc_id_to_serif_path[query_doc_id],
                                              query_doc_id_to_npz_path[query_doc_id])
            features = extractor.extract()
            with open(os.path.join(args.output_path, query_doc_id + ".json"), 'w') as fp:
                json.dump(features, fp, cls=ComplexEncoder, ensure_ascii=False)
    if args.mode == "CALCULATE_SIMILARITY":
        list_query_feature = list()
        with open(args.input_query_feature_list) as fp:
            for i in fp:
                i = i.strip()
                with open(i) as fp2:
                    j = json.load(fp2)
                    for k in j:
                        list_query_feature.append(MyQueryFeature.fromJSON(k))
        list_doc_feature = list()
        with open(args.input_doc_feature_list) as fp:
            for i in fp:
                i = i.strip()
                with open(i) as fp2:
                    j = json.load(fp2)
                    for k in j:
                        list_doc_feature.append(MyEventMentionFeature.fromJSON(k))
        cosine_similarity_module = CosineSimilarityModule()
        similarity_dict = cosine_similarity_module.get_similarity(args.metric,args.n_trees,list_query_feature, list_doc_feature)
        with open(args.output_path, 'wb') as fp:
            pickle.dump(similarity_dict, fp)

    if args.mode == "ENTITY_FILTER":
        entity_filter = EntityConstraintFilter(args.query_result, args.input_query_feature_list,
                                               args.input_doc_feature_list)
        similarity_dict = entity_filter.filter()
        with open(args.output_path, 'wb') as fp:
            pickle.dump(similarity_dict, fp)

    if args.mode == "DUMP_REPORT":
        report_dumper = ReportDumper(args.metric,args.n_trees,args.query_result, args.input_query_feature_list, args.input_doc_feature_list)
        output_en = report_dumper.dump()
        with open(args.output_path, 'w') as fp:
            json.dump(output_en, fp, ensure_ascii=False, indent=4, sort_keys=True)
