
import argparse
import codecs
from collections import defaultdict
import json
import os
import sys

try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.join(
        script_dir, "..", "..", "..", "..", "text-open", "src", "python"))
    import serifxml3
except ImportError as e:
    raise e

from causal_factor_structure import EntityMentionGenerator
from causal_factor_structure import EntityMention
from causal_factor_structure import to_tokens


class EventTypeWithSerifxmlAttributes(object):

    def __init__(self, type_name, score):
        self.event_type = type_name
        self.score = score


class Mapping(object):

    def __init__(self):
        self._docid_to_sentence_to_span_to_name = dict()
        self._type_to_id_to_score = dict()
        self._id_to_role_to_names = dict()
        self._id_to_event_mention = dict()
        self._id_to_string_and_sentence_and_sentence_id = dict()

    def get_event_mention_string_info(self, _id):
        return self._id_to_string_and_sentence_and_sentence_id.get(
            _id, ("NOT FOUND", "NOT FOUND", -1))

    def update_name_map_with_mentions(
            self, mentions, doc_id, sentence_id, whitelist=None):
        for mention in mentions:
            if whitelist is None or mention.canonical_name in whitelist:
                span = int(mention.start_char), int(mention.end_char)
                self._docid_to_sentence_to_span_to_name.setdefault(
                    doc_id, {}).setdefault(
                    sentence_id, {})[span] = mention.canonical_name

    def get_arguments(self, event_mention, sentence_id, doc_id):
        arguments = {}
        for argument in event_mention.arguments:
            mention = argument.mention
            if mention is not None:
                mention_span = int(mention.start_char), int(mention.end_char)
                spans = self._docid_to_sentence_to_span_to_name.get(
                    doc_id, {}).get(sentence_id, {})
                for covering_span in spans:
                    if span_is_covered(mention_span, covering_span):
                        arguments.setdefault(argument.role, []).append(
                            spans[covering_span])
                        break
        return arguments

    def add_mapping(
            self,
            event_mention,
            doc_id,
            semantic_phrase,
            sentence,
            sentence_id,
            whitelist=None):
        role_to_names = self.get_arguments(event_mention, sentence_id, doc_id)

        # don't bother mapping if there's a known mismatch
        if whitelist is not None:
            for names in role_to_names.values():
                for name in names:
                    if name not in whitelist:
                        return

        _id = get_id(doc_id, event_mention)
        self._id_to_event_mention[_id] = event_mention
        self._id_to_role_to_names[_id] = role_to_names
        self._id_to_string_and_sentence_and_sentence_id[_id] = (
            semantic_phrase, sentence, sentence_id)
        for causal_factor in event_mention.event_types:
            self._type_to_id_to_score.setdefault(
                causal_factor.event_type, {})[_id] = causal_factor.score

    def match_against_event_mentions(self,
                                     query_event_mentions,
                                     role_to_names,
                                     strictness='relaxed',
                                     cutoff=0
                                     ):

        def args_match(dict_1, dict_2, strictness):
            if strictness == 'relaxed':  # ignore counts
                all_names_in_1 = set()
                for names in dict_1.values():
                    all_names_in_1.update(names)
                all_names_in_2 = set()
                for names in dict_2.values():
                    all_names_in_2.update(names)
                return all_names_in_1 == all_names_in_2
            elif strictness == 'exact':
                return dict_1 == dict_2
            return False

        corpus_em_id_to_best_match_info = {}
        matched_em_id_to_wb_type = {}
        for semantic_phrase, causal_factors in query_event_mentions:
            for causal_factor in causal_factors:
                wb_em_score = causal_factor.score
                for corpus_em_id in self._type_to_id_to_score.get(
                        causal_factor.event_type, {}):
                    corpus_em_score = self._type_to_id_to_score[
                        causal_factor.event_type][corpus_em_id]
                    corpus_role_to_names = self._id_to_role_to_names[
                        corpus_em_id]
                    if args_match(
                            role_to_names, corpus_role_to_names, strictness):

                        match_score = wb_em_score * corpus_em_score

                        best_score = corpus_em_id_to_best_match_info.get(
                            corpus_em_id, (-1, None))[0]
                        if best_score < match_score:
                            match_info = (match_score, corpus_role_to_names)
                            corpus_em_id_to_best_match_info[corpus_em_id] = match_info
                            matched_em_id_to_wb_type[corpus_em_id] = (
                                causal_factor.event_type)

        if cutoff < 1:
            cutoff = len(corpus_em_id_to_best_match_info)
        matches = sorted(
            corpus_em_id_to_best_match_info.items(),
            reverse=True,
            key=lambda x: (x[1][0], x[0])
        )[:cutoff]

        match_dicts = []
        for _id, (score, arguments) in matches:
            phrase, sentence, sentence_id = (
                self.get_event_mention_string_info(_id))
            event_mention = self._id_to_event_mention[_id]
            match_dict = {
                "match_score": score,
                "semantic_phrase": phrase,
                "sentence_id": sentence_id,
                "sentence_text": sentence,
                "document": _id.split(".")[0],
                "event_mention": _id.split(".")[1],
                "event_mention_start_and_end": "{}-{}".format(
                    event_mention.semantic_phrase_start,
                    event_mention.semantic_phrase_end),
                "arguments": arguments,
                "groundings": sorted(
                    [(t.event_type, t.score)
                     for t in event_mention.event_types],
                    reverse=True,
                    key=lambda x: (x[1], x[0])),
                "type_of_whiteboard_EM_matched_with_this_corpus_EM": (
                    matched_em_id_to_wb_type[_id])
            }
            match_dicts.append(match_dict)
        return match_dicts


def span_is_covered(span, potential_covering_span):
    start_1 = span[0]
    end_1 = span[1]
    start_2 = potential_covering_span[0]
    end_2 = potential_covering_span[1]
    return start_1 >= start_2 and end_1 <= end_2


def get_id(doc_id, element):
    return "{}.{}".format(doc_id, element.id)


def load_serifxmls(serifxml_filelist):
    serifxml_filelist = os.path.realpath(os.path.abspath(serifxml_filelist))
    with codecs.open(serifxml_filelist, 'r', encoding='utf8') as fh:
        return [path.strip() for path in fh.readlines()]


def load_wb_json(whiteboard_json_file):
    whiteboard_json_file = os.path.realpath(os.path.abspath(
        whiteboard_json_file))
    with codecs.open(whiteboard_json_file, 'r', encoding='utf8') as fh:
        return json.load(fh)


def get_corpus_mapping(serifxml_filelist, whitelist=None):
    mapping = Mapping()
    serifxml_file_paths = load_serifxmls(serifxml_filelist)
    for path in serifxml_file_paths:
        serif_doc = serifxml3.Document(path)

        for sentence_id, sentence in enumerate(serif_doc.sentences):
            st = sentence.sentence_theories[0]
            """:type: serifxml.SentenceTheory"""
            if len(st.token_sequence) == 0:
                continue
            tokens = to_tokens(st)
            """:type: list[Token]"""
            entity_mentions = EntityMentionGenerator.get_entity_mentions(
                st, serif_doc, tokens)
            """:type: list[EntityMention]"""
            mapping.update_name_map_with_mentions(
                entity_mentions, serif_doc.docid, sentence_id, whitelist)

            sentence_tokens = list(sentence.token_sequence)
            sentence_string = u" ".join([t.text for t in sentence_tokens])
            for event_mention in st.event_mention_set:
                mention_start = int(event_mention.semantic_phrase_start)
                mention_end = int(event_mention.semantic_phrase_end)
                semantic_phrase_tokens = (
                    sentence_tokens[mention_start:mention_end + 1])
                semantic_phrase = u' '.join(
                    [t.text for t in semantic_phrase_tokens])
                mapping.add_mapping(
                    event_mention,
                    serif_doc.docid,
                    semantic_phrase,
                    sentence_string,
                    sentence_id,
                    whitelist)
    return mapping


def get_whiteboard_artifacts_from_json(whiteboard_json_file):
    whiteboard_artifacts = []
    queries = load_wb_json(whiteboard_json_file)
    for query in queries:
        doc_id = query["docid"]
        query_text = query["text"]
        args = {"entity_mention": [m["canonical_name"]
                                   for m in query["entity_mentions"]]}
        wb_event_mentions = []
        for semantic_phrase_dict in query['semantic_phrases']:
            event_types = [EventTypeWithSerifxmlAttributes(et[0], et[1])
                           for et in semantic_phrase_dict["event_types"]]
            semantic_phrase = semantic_phrase_dict['text']
            wb_event_mentions.append((semantic_phrase, event_types))
        whiteboard_artifacts.append(
            (doc_id, query_text, args, wb_event_mentions))
    return whiteboard_artifacts


def get_whiteboard_name_whitelist_from_jsons(whiteboard_json_file):
    whitelist = []
    queries = load_wb_json(whiteboard_json_file)
    for query in queries:
        for mention in query['entity_mentions']:
            whitelist.append(mention['canonical_name'])
    return set(whitelist)


def serialize(wb_artifacts, match_list, wb_in, corpus_in, out_path):
    assert len(match_list) == len(wb_artifacts)
    queries_list = []
    for i, wb_artifact_data in enumerate(wb_artifacts):
        query_doc_id = wb_artifact_data[0]
        query_text = wb_artifact_data[1]
        query_args = wb_artifact_data[2]
        query_ems = wb_artifact_data[3]
        query_ems = [
            {"semantic_phrase": semantic_phrase,
             "event_types": [(et.event_type, et.score) for et in event_types]}
            for (semantic_phrase, event_types) in query_ems]
        matches = match_list[i]["ranked_corpus_event_mentions"]

        query_dict = dict()
        query_dict["query_info"] = {}
        query_dict["query_info"]["doc_id"] = query_doc_id
        query_dict["query_info"]["query_text"] = query_text
        query_dict["query_info"]["arguments"] = query_args
        query_dict["query_info"]["event_mentions"] = query_ems
        query_dict["ranked_corpus_event_mentions"] = matches

        queries_list.append(query_dict)

    queries_with_metadata = {
        "_whiteboard_input_file": os.path.realpath(os.path.abspath(wb_in)),
        "_corpus_input_file": os.path.realpath(os.path.abspath(corpus_in)),
        "queries": queries_list}
    path = os.path.realpath(os.path.abspath(out_path))
    with codecs.open(path, 'w', encoding='utf8') as fh:
        json.dump(queries_with_metadata, fh, indent=4, sort_keys=True)


def main_with_json(corpus_serifxml_filelist, whiteboard_json, output=None):
    whitelist = get_whiteboard_name_whitelist_from_jsons(whiteboard_json)
    corpus_mapping = get_corpus_mapping(
        corpus_serifxml_filelist, whitelist=whitelist)
    whiteboard_artifacts = get_whiteboard_artifacts_from_json(whiteboard_json)

    all_matches = []
    for docid, query, arguments, wb_event_mentions in whiteboard_artifacts:

        matches = corpus_mapping.match_against_event_mentions(
            wb_event_mentions,
            arguments,
            cutoff=100  # TODO remove this limit
        )
        query_dict = {  # format is not ideal but @hqiu may be using this now
            "doc": docid,
            "query": query,
            "ranked_corpus_event_mentions": matches
        }
        all_matches.append(query_dict)

    if output is not None:
        serialize(whiteboard_artifacts,
                  all_matches,
                  whiteboard_json,
                  corpus_serifxml_filelist,
                  output)

    return all_matches


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--corpus_serifxml_filelist")
    arg_parser.add_argument("--whiteboard_jsons")
    arg_parser.add_argument("--output_json", default=None)
    args = arg_parser.parse_args()

    main_with_json(
        args.corpus_serifxml_filelist,
        args.whiteboard_jsons,
        args.output_json)
