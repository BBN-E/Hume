
import os,sys,json,logging,subprocess
import numpy as np
current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir,os.path.pardir))
sys.path.append(project_root)

from similarity.event_and_arg_emb_pairwise.config import Config

logger = logging.getLogger(__name__)

from similarity.event_and_arg_emb_pairwise.utils.common import create_file_name_to_path
from similarity.event_and_arg_emb_pairwise.utils.logging_config import config_logging

def main(name,args):
    if name == "SerifNLPLingoFeatureExtractor":
        from similarity.event_and_arg_emb_pairwise.feature_extractor.serif_nlplingo_feature_extractor import \
            SerifNLPLingoFeatureExtractor
        serif_list = args.input_serif_list
        npz_list = args.input_npz_list
        output_path = args.output_path
        key_getter_strs = args.key_getter_str
        input_bert_list = args.input_bert_list

        doc_id_to_bert_npz_path = create_file_name_to_path(input_bert_list, ".npz")

        list_features_all = list()
        serif_nlplingo_feature_extractor = SerifNLPLingoFeatureExtractor(
            serif_list, npz_list, doc_id_to_bert_npz_path, {i.strip() for i in key_getter_strs.split(",")})
        extracted_features = serif_nlplingo_feature_extractor.extract_features()
        list_features_all.extend(extracted_features)
        with open(os.path.join(
                output_path, "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    elif name == "LearnItObversationFeatureExtractor":
        from similarity.event_and_arg_emb_pairwise.feature_extractor.learnit_obversation_ave_bert_feature_extractor import \
            LearnItObversationFeatureExtractor
        input_bert_list = args.input_bert_list # This is not from pipeline
        input_feature_list = args.input_feature_list
        output_path = args.output_path
        cap = int(args.cap)
        learnit_obversation_feature_extractor = LearnItObversationFeatureExtractor(input_feature_list,input_bert_list,cap,output_path)
        feature_list = learnit_obversation_feature_extractor.extract_features()
        with open(os.path.join(
                output_path, "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=feature_list)

    elif name == "LearnItObversationFeatureExtractorRaw":
        from similarity.event_and_arg_emb_pairwise.feature_extractor.learnit_obversation_bert_feature_extractor_raw import LearnItObversationFeatureExtractorRaw
        learnit_jar_path = args.learnit_jar_path
        learnit_target = args.learnit_target
        learnit_param = args.learnit_param
        serif_list = args.input_serif_list
        input_bert_list = args.input_bert_list
        output_path = args.output_path
        cap = args.cap
        learnit_observation_feature_extractor_raw = LearnItObversationFeatureExtractorRaw(learnit_jar_path,learnit_target,learnit_param,serif_list,input_bert_list,cap,output_path)
        feature_list = learnit_observation_feature_extractor_raw.extract_features()
        with open(os.path.join(
                output_path, "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=feature_list)

    elif name == "SerifEventMentionTypeCentroidExtractor":
        from similarity.event_and_arg_emb_pairwise.feature_extractor.serif_em_type_centroid_extractor import SerifEventMentionTypeCentroidExtractor
        serif_list = args.input_serif_list
        output_path = args.output_path
        input_bert_list = args.input_bert_list
        em_representation_mode = args.em_representation_mode

        list_features_all = list()
        serif_em_type_centroid = SerifEventMentionTypeCentroidExtractor(
            serif_list, input_bert_list,em_representation_mode)
        extracted_features = serif_em_type_centroid.extract_features()
        list_features_all.extend(extracted_features)
        with open(os.path.join(
                output_path, "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    elif name == "SerifEventMentionBertExtractor":
        from similarity.event_and_arg_emb_pairwise.feature_extractor.serif_em_bert_extractor import \
            SerifEventMentionBertExtractor
        serif_list = args.input_serif_list
        output_path = args.output_path
        input_bert_list = args.input_bert_list
        em_representation_mode = args.em_representation_mode
        drop_generic_event = args.drop_generic_event if hasattr(args,"drop_generic_event") else False

        list_features_all = list()
        serif_em_bert_feature_extractor = SerifEventMentionBertExtractor(
            serif_list, input_bert_list,em_representation_mode,drop_generic_event)
        extracted_features = serif_em_bert_feature_extractor.extract_features()
        list_features_all.extend(extracted_features)
        with open(os.path.join(
                output_path, "features.npz"), 'wb') as fp:
            np.savez_compressed(fp, features=list_features_all)

    else:
        raise ValueError()

if __name__ == "__main__":
    config_logging()
    json_path = sys.argv[1]
    feature_id = sys.argv[2]
    with open(json_path) as fp:
        j = json.load(fp)
    c = Config()
    c.update_using_dict(j)
    feature_id_to_feature = {i.id:i for i in c.feature_extractors}
    dumper_config = feature_id_to_feature[feature_id]
    name = dumper_config.name
    args = dumper_config.args
    main(name,args)