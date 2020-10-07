
import argparse
import io
import json
import os
import sys
import enum
import logging
logger = logging.getLogger(__name__)
from collections import defaultdict

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_dir, "..", "knowledge_base"))
try:
    from internal_ontology import Node
    from internal_ontology import Ontology
    from internal_ontology import OntologyMapper
except ImportError as e:
    raise e

sys.path.insert(0, os.path.join(script_dir, ".."))
try:
    from grounding import Grounder
    from grounding import MentionCandidate
    from grounding import utils
except ImportError as e:
    raise e

try:
    import serifxml3
except ImportError as e:
    raise e


class SerifEventMentionTypingField(enum.Enum):
    event_type = "event_type"
    event_types = "event_types"
    factor_types = "factor_types"


class PGEventType(object):
    """
    Duck class for handle event type sources
    """
    def __init__(self,event_type,score):
        self.event_type = event_type
        self.score = score

    def __str__(self):
        return "{}: {}".format(self.event_type,self.score)

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def from_serif_event_typing_to_pg_event_type_list(
            serif_em, serif_event_mention_typing_field):
        assert isinstance(serif_em, serifxml3.EventMention)
        ret = list()
        if (serif_event_mention_typing_field
                == SerifEventMentionTypingField.event_type):
            ret.append(PGEventType(serif_em.event_type,serif_em.score))
        elif (serif_event_mention_typing_field
              == SerifEventMentionTypingField.event_types):
            for event_type in serif_em.event_types:
                ret.append(PGEventType(event_type.event_type, event_type.score))
        elif (serif_event_mention_typing_field
              == SerifEventMentionTypingField.factor_types):
            for event_type in serif_em.factor_types:
                ret.append(PGEventType(event_type.event_type, event_type.score))
        return ret



ONTOLOGIES_REQUIRING_PRE_MAP = {"WM"}
ONTOLOGIES_REQUIRING_POST_MAP = {"CAUSEEX", "ICM", "BBN"}

class SerifXMLGrounder(object):
    def __init__(self,max_number_of_tokens_per_sentence:int,which_ontology,keywords,stopwords,event_ontology_yaml,internal_ontology_yaml,grounding_mode,embeddings,exemplars,bert_centroids,bert_npz_file_list,n_best:int,only_use_bert_from_root:bool,blacklist,event_mention_typing_field,threshold:float,**kwargs):
        self.counter = defaultdict(int)
        self.ontology = Ontology()
        self.ontology_mapper = OntologyMapper()
        self.max_number_of_tokens_per_sentence = max_number_of_tokens_per_sentence
        self.which_ontology = which_ontology
        self.event_mention_typing_field = SerifEventMentionTypingField(event_mention_typing_field)
        self.threshold = threshold
        self.only_use_bert_from_root = only_use_bert_from_root
        self.n_best = n_best
        self.bert_docid_to_npz = None
        if self.which_ontology in ONTOLOGIES_REQUIRING_PRE_MAP:
            if "compositional" in event_ontology_yaml.lower():
                root_path = "/wm_compositional/process"  # TODO don't hard-code
            else:
                root_path = "/wm/concept/causal_factor"  # TODO don't hard-code
            kws = utils.read_keywords_from_bbn_annotation(keywords)
            stops = utils.read_stopwords_from_hume_resources(stopwords)
            self.ontology.load_from_yaml_with_metadata(event_ontology_yaml)
            self.ontology_mapper.load_ontology(internal_ontology_yaml)
            # bert_function = ontology.add_node_contextual_embeddings_with_mapper
            # bert_function_args = [ontology_mapper, args.which_ontology]

            if grounding_mode == 'fast':
                # simply map entry points to external ontology
                self.force_entry_points_into_groundings = True
                self.grounding_modes = []  # no modes --> no groundings but entry points

            elif grounding_mode == 'medium':
                # Same as Full mode, currently.  The similarity mode specified by
                # utils.SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG
                # uses the embeddings associated with wm_metadata.yml file exemplars
                # --these are currently always static.
                self.force_entry_points_into_groundings = False
                self.grounding_modes = [
                    utils.SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME,
                ]
                self.ontology.init_embeddings(embeddings)

            elif grounding_mode == 'full':
                self.force_entry_points_into_groundings = False
                self.grounding_modes = [
                    utils.SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME,
                ]
                self.ontology.init_embeddings(embeddings)
            else:
                raise NotImplementedError("No supported {}".format(grounding_mode))
        else:
            root_path = None
            kws = {}
            stops = utils.read_stopwords_from_hume_resources(stopwords)
            self.ontology_mapper.load_ontology(event_ontology_yaml)
            self.ontology.load_from_internal_yaml(event_ontology_yaml)

            # simply map entry points to external ontology
            if grounding_mode == 'fast':
                self.force_entry_points_into_groundings = True
                self.grounding_modes = []  # no modes --> no groundings but entry points

            elif grounding_mode == 'medium':
                self.force_entry_points_into_groundings = True
                self.grounding_modes = [
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME,
                ]
                self.ontology.add_internal_exemplars_from_json(
                    exemplars, None, self.which_ontology)
                self.ontology.init_embeddings(embeddings)

            elif grounding_mode == 'full':
                self.force_entry_points_into_groundings = True
                self.grounding_modes = [
                    utils.SimilarityMode
                        .COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                    utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME,
                ]
                self.ontology.add_internal_exemplars_from_json(
                    exemplars, None, self.which_ontology)
                self.ontology.init_embeddings(embeddings)
                internal_name_to_float_list = utils.load_json(bert_centroids)
                self.ontology.add_node_contextual_embeddings_with_name(
                    internal_name_to_float_list)
                self.bert_docid_to_npz = utils.build_docid_to_npz_map(
                    bert_npz_file_list)

            elif grounding_mode == 'centroids_only':
                self.force_entry_points_into_groundings = True
                self.grounding_modes = [
                    utils.SimilarityMode
                        .COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT
                ]
                internal_name_to_float_list = utils.load_json(bert_centroids)
                self.ontology.add_node_contextual_embeddings_with_name(
                    internal_name_to_float_list)
                self.bert_docid_to_npz = utils.build_docid_to_npz_map(
                    bert_npz_file_list)

            else:
                raise NotImplementedError("No supported {}".format(grounding_mode))
        logger.info("Mode: {}\nForcing entry points into output: {}\nSimilarity modes: {}"
              .format(grounding_mode,
                      self.force_entry_points_into_groundings,
                      self.grounding_modes))

        self.top_k = self.n_best
        # due to potential for duplication, let's keep extras
        if self.which_ontology in ONTOLOGIES_REQUIRING_POST_MAP:
            self.top_k = self.top_k * 3

        self.grounder = Grounder(self.ontology, self.top_k)
        self.grounder.build_grounder(kws, stops)
        self.grounder.specify_user_root_path(root_path)

        self.remove_zero_score_groundings = False
        if self.only_use_bert_from_root is True:
            self.grounding_modes = [
                (utils.SimilarityMode
                 .COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT)]
            self.force_entry_points_into_groundings = True
            self.remove_zero_score_groundings = True

        self.grounding_blacklist = set()
        if os.path.isfile(blacklist):
            with open(blacklist, 'r', encoding='utf8') as blacklist_fh:
                self.grounding_blacklist = set(json.load(blacklist_fh))

        self.cache = {}


    def process_doc(self,serif_doc):
        docid, mentions_and_entry_points, serif_doc = self.read_serifxml_event_mentions(
            serif_doc
        )

        # "grounding cache" format
        for (mention_candidate, entry_points, serifxml_entry_types, serif_em) in mentions_and_entry_points:

            if len(entry_points) == 0 and len(serifxml_entry_types) > 0:
                # map blacklisted node without grounding
                logger.warning("Mapping blacklisted node without grounding.  Scores may "
                      "be unexpected.")
                grounded_classes = []
                for blacklisted_type in serifxml_entry_types:
                    blacklisted_paths = self.ontology_mapper.look_up_external_types(
                        blacklisted_type.event_type, self.which_ontology)
                    for path in blacklisted_paths:
                        # FIXME avoids Grounder.get_grounding_key()
                        grounded_classes.append((path, blacklisted_type.score))
                grounded_classes = sorted(grounded_classes, key=lambda x: -x[1])

            elif (len(entry_points) == 1 and
                  entry_points[0] == self.grounder.get_ontology().get_root().get_name()):
                logger.warning("Not grounding generic {} with score {}".format(
                    serifxml_entry_types[0].event_type,
                    serifxml_entry_types[0].score))
                grounded_classes = []

            else:  # ground normally

                grounded_classes = self.grounder.ground_mention(
                    mention_candidate,
                    entry_points,
                    self.threshold,
                    modes=self.grounding_modes,
                    force_entry_points=self.force_entry_points_into_groundings,
                    remove_groundings_with_small_score=self.remove_zero_score_groundings,
                    blacklisted_paths=self.grounding_blacklist
                )

            # pass through input entry points and scores
            if self.force_entry_points_into_groundings or len(grounded_classes) < 1:
                groundings_dict = {g: s for g, s in grounded_classes}
                entry_points_dict = {}
                for i, serifxml_entry_type in enumerate(serifxml_entry_types):
                    score = serifxml_entry_type.score
                    paths_for_entry_point = {}

                    if self.which_ontology in ONTOLOGIES_REQUIRING_PRE_MAP:
                        for path in self.ontology_mapper.look_up_external_types(
                                serifxml_entry_type.event_type,
                                self.which_ontology):
                            paths_for_entry_point[path] = score

                    else:
                        nodes = self.ontology.get_nodes_by_name(
                            serifxml_entry_type.event_type)
                        for node in nodes:
                            path = node.get_path()
                            paths_for_entry_point[path] = score

                    # overwrites repeated external sources with highest score
                    utils.merge_groundings(entry_points_dict,
                                           paths_for_entry_point)

                grounded_classes = (
                    self.grounder.get_top_k_from_ep_and_grounded_dicts(
                        entry_points_dict, groundings_dict))

            if len(grounded_classes) < 1:
                if self.only_use_bert_from_root is False:
                    if self.which_ontology in ONTOLOGIES_REQUIRING_PRE_MAP:
                        logging.warning("We cannot find external type mappings "
                              "for {}".format(serifxml_entry_types))
                        grounded_classes = self.grounder.get_top_k_from_dict(
                            {self.grounder.get_user_root_path(): 0.00001})

            # CX: map internal ontology path to external source
            if self.which_ontology in ONTOLOGIES_REQUIRING_POST_MAP:
                self.grounder.set_k(self.n_best)
                grounded_classes = (
                    self.ontology_mapper.map_internal_paths_to_k_sources(
                        grounded_classes, self.grounder, self.which_ontology))

            if len(grounded_classes) < 1 and len(serifxml_entry_types) > 0:
                raise ValueError(
                    "We're discarding {} from {} , and there will be 0 {} which"
                    " will cause downstream problems.".format(
                        serifxml_entry_types,
                        self.event_mention_typing_field,
                        self.event_mention_typing_field))

            self.add_groundings_to_cache(
                grounded_classes,
                mention_candidate,
                serifxml_entry_types,
                )

            self.maintain_serif_doc_event_mention(
                serif_em,
                grounded_classes,
                )

    def read_serifxml_event_mentions(
            self,
            serif_doc):
        mentions = []
        docid = serif_doc.docid
        using_bert = self.bert_docid_to_npz is not None

        contextual_embeddings = None
        contextual_token_map = None
        if using_bert:
            if hasattr(serif_doc,"aux") and hasattr(serif_doc.aux,"bert_npz"):
                contextual_embeddings, contextual_token_map = (utils.truncation_npz(serif_doc.aux.bert_npz))
            else:
                npz_path = self.bert_docid_to_npz.get(docid)
                if npz_path is None:
                    logger.warning("No BERT npz file for docid {}".format(docid))
                    return docid, mentions, serif_doc
                contextual_embeddings, contextual_token_map = (
                    utils.load_contextual_npz(npz_path))

        for sentence_index, sentence in enumerate(serif_doc.sentences):

            for sentence_theory in sentence.sentence_theories:
                if self.max_number_of_tokens_per_sentence > -1:
                    if len(sentence_theory.token_sequence) == 0 or len(sentence_theory.token_sequence) > self.max_number_of_tokens_per_sentence:
                        logger.info("Will not process lengthy sentences docid: {}, sentid: {}, sent: {}".format(docid,sentence_index," ".join(
                    token.text for token in sentence_theory.token_sequence)))
                        continue
                sentence_string = u" ".join(
                    token.text for token in sentence_theory.token_sequence)

                mention_to_embedding = dict()
                mention_to_anchor_embeddings = dict()
                if using_bert:
                    if len(sentence_theory.token_sequence) > 0:
                        mention_to_embedding, mention_to_anchor_embeddings = (
                            utils.get_serif_event_mention_to_contextual_embedding(
                                sentence_theory, sentence_index,
                                contextual_embeddings, contextual_token_map))

                for event_mention in sentence_theory.event_mention_set:
                    event_types = (
                        PGEventType.from_serif_event_typing_to_pg_event_type_list(
                            event_mention, self.event_mention_typing_field))

                    #original_score = event_mention.score

                    sentence_tokens = list(sentence.token_sequence)
                    mention_start = int(event_mention.semantic_phrase_start)
                    mention_end = int(event_mention.semantic_phrase_end)
                    semantic_phrase_tokens = (
                        sentence_tokens[mention_start:mention_end + 1])
                    mention_string = u' '.join(
                        [t.text for t in semantic_phrase_tokens])

                    if self.which_ontology in ONTOLOGIES_REQUIRING_PRE_MAP:
                        # WM grounds to external ontology: entry point is external
                        entry_point_paths = []
                        for et in event_types:
                            entry_point_paths.extend(
                                self.ontology_mapper.look_up_external_types(et.event_type, self.which_ontology))
                        entry_points = []
                        for path in entry_point_paths:
                            node = self.ontology.get_node_by_path(path)
                            if node is not None:
                                entry_points.append(node.get_name())

                    else:
                        # CX grounds to internal ontology: entry point is internal
                        entry_points = [et.event_type for et in event_types]

                    mention_candidate = MentionCandidate(
                        mention_string[:], sentence_string)
                    mention_candidate.add_structured_data(self.grounder.get_keywords())
                    mention_candidate.remove_stopwords_from_mention(self.grounder.get_stopwords())

                    contextual_embedding = mention_to_embedding.get(event_mention)
                    if contextual_embedding is not None:
                        mention_candidate.set_contextual_embedding(
                            contextual_embedding)
                        anchor_embeddings = mention_to_anchor_embeddings.get(
                            event_mention, [])
                        for anchor_embedding in anchor_embeddings:
                            mention_candidate.add_contextual_anchor_embedding(
                                anchor_embedding)

                    mentions.append(
                        (mention_candidate, entry_points, event_types, event_mention))
                    self.counter[(
                        tuple(sorted([et.event_type for et in event_types])),
                        mention_string
                    )] += 1

        return docid, mentions, serif_doc

    def maintain_serif_doc_event_mention(self,serif_em,
                                         grounded_classes,
                                         ):
        assert isinstance(serif_em, serifxml3.EventMention)
        if (self.event_mention_typing_field
                == SerifEventMentionTypingField.event_type):
            highest_prob_event_type = max(grounded_classes.keys(),
                                          key=lambda g: grounded_classes[g])
            highest_prob_score = grounded_classes[highest_prob_event_type]
            serif_em.event_type = highest_prob_event_type
            serif_em.score = highest_prob_score
            return

        # Erase all existing types

        if (self.event_mention_typing_field
                == SerifEventMentionTypingField.event_types):
            serif_em.event_types = list()
            for grounding, score in grounded_classes:
                serif_em.add_new_event_mention_type(grounding, score)

        elif (self.event_mention_typing_field
              == SerifEventMentionTypingField.factor_types):
            serif_em.factor_types = list()
            for grounding, score in grounded_classes:
                serif_em.add_new_event_mention_factor_type(grounding, score)

        else:
            raise NotImplementedError


    def add_groundings_to_cache(self,groundings, mc, entry_types):
        cache_key = utils.get_legacy_cache_key(
            mc,
            sorted([et.event_type for et in entry_types]),
            self.grounder.get_ontology().get_root().get_name())
        self.cache[cache_key] = groundings


    def dump_cache(self,output):

        # print json.dumps(cache, indent=4, sort_keys=True, cls=ComplexEncoder)
        if output is not None:
            with io.open(output, 'w', encoding='utf8') as f:
                f.write(json.dumps(self.cache, ensure_ascii=False, indent=4, sort_keys=True))
            with io.open(output + '.frequencies', 'w', encoding='utf8') as f:
                for pair, freq in sorted(self.counter.items(),
                                         reverse=True, key=lambda x: x[1]):
                    f.write(u"{}\t{}\t{}\n".format(freq, pair[0], pair[1]))
                    cache_key = u'|||'.join(["Event", u';'.join(pair[0]), pair[1]])
                    for grounding, score in self.cache.get(cache_key, []):
                        f.write(u'\t{}\t{}\n'.format(grounding, score))

    def write_serifxmls(self,output_serifxml_dir, doc):
        if output_serifxml_dir.lower() != "none":
            os.makedirs(output_serifxml_dir, exist_ok=True)
            doc.save(os.path.join(output_serifxml_dir,"{}.xml".format(doc.docid)))

def str2bool(v):
    """
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
    :param v:
    :return:
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--event_ontology_yaml")
    arg_parser.add_argument("--internal_ontology_yaml", default=None)
    arg_parser.add_argument("--exemplars")
    arg_parser.add_argument("--embeddings")
    arg_parser.add_argument("--stopwords")
    arg_parser.add_argument("--keywords")
    arg_parser.add_argument("--which_ontology")
    arg_parser.add_argument("--threshold", type=float)
    arg_parser.add_argument("--n_best", type=int, default=5)
    arg_parser.add_argument("--max_number_of_tokens_per_sentence",type=int,default=-1)
    arg_parser.add_argument("--serifxmls")
    arg_parser.add_argument("--bert_centroids", default="NONE")
    arg_parser.add_argument("--bert_npz_file_list", default="NONE")
    arg_parser.add_argument("--blacklist", default="NONE")
    arg_parser.add_argument('--output', nargs='?', default=None)
    arg_parser.add_argument('--only_use_bert_from_root', default=False,const=True,type=str2bool,nargs='?')
    arg_parser.add_argument('--grounding_mode', default="full", choices=["full", "fast", "medium"])
    arg_parser.add_argument('--event_mention_typing_field',type=str,required=True)
    arg_parser.add_argument('--output_serifxml_dir',type=str,default="NONE")
    args = arg_parser.parse_args()

    serifxml_grounder = SerifXMLGrounder(**args.__dict__)
    if os.path.isdir(args.serifxmls):
        serifxmls = [f for f in os.listdir(args.serifxmls)
                     if f.endswith('xml') and os.path.isfile(f)]
    else:
        with io.open(args.serifxmls, 'r') as f:
            serifxmls = [line.strip() for line in f.readlines()]
    for serifxml in serifxmls:
        serif_doc = serifxml3.Document(serifxml)
        serifxml_grounder.process_doc(serif_doc)
        serifxml_grounder.write_serifxmls(args.output_serifxml_dir,serif_doc)
    serifxml_grounder.dump_cache(args.output)


if __name__ == "__main__":
    main()
