import json
import logging

logger = logging.getLogger(__name__)


def event_frame_to_groundings(event_frame, entity_id2ent):
    ret = list()
    h_theme = None
    h_property = None
    for event_arg in event_frame["arguments"]:
        arg_entity_id = event_arg["value"]["@id"]
        arg_role = event_arg["type"]
        canonical_name = entity_id2ent[arg_entity_id].get("canonicalName", entity_id2ent[arg_entity_id]["text"])
        if arg_role == "has_theme":
            assert h_theme is None, "Assume singleton theme"
            h_theme = canonical_name
        if arg_role == "has_property":
            assert h_property is None, "Assume singleton property"
            h_property = canonical_name
    for grounding in sorted(event_frame["grounding"], key=lambda x: x['value'], reverse=True):
        concept = grounding["ontologyConcept"]
        ret.append((concept, h_theme, h_property))
    return ret


def get_marked_binary_span(sent_id2sent, left_span, right_span):
    sent_id = left_span["provenance"][0]["sentence"]
    sent = sent_id2sent[sent_id]
    left_start, left_end = left_span["provenance"][0]["sentenceCharPositions"]["start"], \
                           left_span["provenance"][0]["sentenceCharPositions"]["end"]
    right_start, right_end = right_span["provenance"][0]["sentenceCharPositions"]["start"], \
                             right_span["provenance"][0]["sentenceCharPositions"]["end"]
    ret_s = ""
    for idx, c in enumerate(sent["text"]):
        if idx == left_start:
            ret_s += "["
        if idx == right_start:
            ret_s += "{"
        ret_s += c.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        if idx == right_end:
            ret_s += "}"
        if idx == left_end:
            ret_s += "]"
    return ret_s


def get_id_obj_map(json_ld_path):
    doc_uuid = None
    with open(json_ld_path, 'r') as f:
        json_data = json.load(f)
        # cache sentences
        sent_id2sent = dict()
        for doc in json_data["documents"]:
            doc_uuid = doc["@id"]
            for sent in doc["sentences"]:
                sent_id2sent[sent["@id"]] = sent
        # cache entities
        entity_id2ent = dict()
        for extraction in json_data["extractions"]:
            if extraction["subtype"] == "entity":
                entity_id2ent[extraction["@id"]] = extraction
        # process events and event event relation
        event_id2event = dict()
        event_event_relation_id_to_event_event_relation = dict()
        for extraction in json_data["extractions"]:
            if extraction["subtype"] == "event":
                if extraction['@id'] not in event_id2event:
                    event_id2event[extraction['@id']] = extraction
                else:
                    print("DUPLICATE: {}".format(extraction['@id']))
            if extraction["type"] == "relation" and extraction['subtype'] in {"causation", "precondition", "catalyst",
                                                                              "mitigation", "prevention"}:
                if extraction["@id"] in event_event_relation_id_to_event_event_relation:
                    print("DUPLICATE: {}".format(extraction['@id']))
                else:
                    event_event_relation_id_to_event_event_relation[extraction["@id"]] = extraction
    return doc_uuid, sent_id2sent, entity_id2ent, event_id2event, event_event_relation_id_to_event_event_relation


def single_document_handler(json_ld_path):
    doc_uuid, sent_id2sent, entity_id2ent, event_id2event, event_event_relation_id_to_event_event_relation = get_id_obj_map(
        json_ld_path)
    ret = list()
    # for event_id ,event_mention in event_id2event.items():
    #     groundings = event_frame_to_groundings(event_mention, entity_id2ent)
    #     original_sentence_marked = get_marked_binary_span(sent_id2sent, event_mention, event_mention)
    #     evidence = "[E] {} {} {}".format(doc_uuid, event_id, original_sentence_marked)
    #     non_generic_only_event = False
    #     for grounding in groundings:
    #         left_type, left_theme, left_property = grounding
    #         if left_type not in {"/wm/process","/wm/concept"}:
    #             non_generic_only_event = True
    #             break
    #     if non_generic_only_event is True:
    #         logger.info(evidence)
    #         for grounding in groundings:
    #             left_type, left_theme, left_property = grounding
    #             event_tuple = "[G] {}".format(grounding)
    #             logger.info(event_tuple)
    for eerm_id, event_event_relation_extraction in event_event_relation_id_to_event_event_relation.items():
        src_event_mention = None
        tgt_event_mention = None
        for argument in event_event_relation_extraction["arguments"]:
            if argument["type"] == "source":
                src_event_mention = event_id2event[argument['value']['@id']]
            if argument['type'] == "destination":
                tgt_event_mention = event_id2event[argument['value']['@id']]
        relation_type = event_event_relation_extraction['subtype']
        left_groundings = event_frame_to_groundings(src_event_mention, entity_id2ent)
        right_groundings = event_frame_to_groundings(tgt_event_mention, entity_id2ent)
        original_sentence_marked = get_marked_binary_span(sent_id2sent, src_event_mention, tgt_event_mention)
        useless_grounding = True
        for left_grounding in left_groundings:
            left_type, left_theme, left_property = left_grounding
            if left_type in {"/wm/process","/wm/concept"}:
                continue
            for right_grounding in right_groundings:
                right_type, right_theme, right_property = right_grounding
                if right_type in {"/wm/process","/wm/concept"}:
                    continue
                useless_grounding = False
        if useless_grounding is False:
            evidence = "[E] {} {} {}".format(doc_uuid, eerm_id, original_sentence_marked)
            logger.info(evidence)
            for left_grounding in left_groundings:
                left_type, left_theme, left_property = left_grounding
                if left_type in {"/wm/process","/wm/concept"}:
                    continue
                for right_grounding in right_groundings:
                    right_type, right_theme, right_property = right_grounding
                    if right_type in {"/wm/process","/wm/concept"}:
                        continue
                    pure_tuple = "[PE] {} {} {}".format(left_type, relation_type,right_type)
                    prop_tuple = "[PROPE] {} {} {}".format(left_grounding, relation_type, right_grounding)
                    logger.info(pure_tuple)
                    logger.info(prop_tuple)


    return ret


def main(input_jsonld_list):
    aggr_tuple_evidences = dict()
    with open(input_jsonld_list) as fp:
        for i in fp:
            i = i.strip()
            eer_tuple_evidence_list = single_document_handler(i)
            for eer_tuple, evidence in eer_tuple_evidence_list:
                aggr_tuple_evidences.setdefault(eer_tuple, list()).append(evidence)
    logger.info("#################################################################")
    for eer_tuple, evidences in aggr_tuple_evidences.items():
        logger.info(eer_tuple)
        for evidence in evidences:
            logger.info("\t{}".format(evidence))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # input_jsonld_list = "/d4m/ears/expts/48393.030422.dsmte.v1/expts/dsmte.030322.v1/json-ld.list"
    # input_jsonld_list = "/d4m/ears/expts/48231.030922.v1/expts/hume_test.dart.082720.wm.v1/json-ld.list"
    input_jsonld_list = "/d4m/ears/expts/48393.031522.dsmte.v1/expts/dsmte.030122.v1/json-ld.list"
    main(input_jsonld_list)
