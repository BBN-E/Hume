import codecs, re, os, json
from elements.kb_mention import KBMention
from elements.kb_value_mention import KBValueMention, KBTimeValueMention, KBMoneyValueMention

class WMTabularFormatSerializer:
    good_date_re = re.compile(r"\d{4}")
    
    def __init__(self):
        pass

    def get_ontology_concept(self,ins_type,ins_subtype,category):
        if category=="event":
            return ins_type
        if category == "entity":
            if "/event" in ins_type or "/entity" in ins_type:
                ontology_concept = ins_type
                # print ("convert[1] " + ins_type + " -> " + ontology_concept)
                return ontology_concept
            elif ins_type in self.config["mappings"][category]:
                ontology_concept = self.config["mappings"][category][ins_type]["default_type"]
                if ins_subtype in self.config["mappings"][category][ins_type]["sub_types"]:
                    ontology_concept = self.config["mappings"][category][ins_type]["sub_types"][ins_subtype]
                # print ("convert[2] entity " + ins_type + " " + ins_subtype + " -> " + ontology_concept)
                return ontology_concept
            else:
                ontology_concept = "/entity"
                # print ("convert[3] entity " + ins_type + " " + ins_subtype + " -> " + ontology_concept)
                return ontology_concept

    def read_config(self, filepath):
        with open(filepath) as fp:
            config = json.load(fp)
        return config

    def get_grounded_types(self, kb_event_mention):
        return json.dumps(
            {k: v for k, v in kb_event_mention.external_ontology_sources})

    def serialize(self, kb, input_metadata_file, output_tabular_file):
        print("WMTABULARSerializer SERIALIZE")
        self.config = self.read_config(
            os.path.dirname(os.path.realpath(__file__)) + "/../config_files/config_ontology_wm.json")

        docid_to_source = dict()
        m = codecs.open(input_metadata_file, 'r', encoding='utf8')
        for line in m:
            line = line.strip()
            pieces = line.split('\t')
            docid_to_source[pieces[0]] = pieces[1]
        m.close()
        
        o = codecs.open(output_tabular_file, 'w', encoding='utf8')

        fields = ["Source", "System", "Sentence ID (start and end document offsets)", "Factor A Text", "Factor A Normalization", "Factor A Location", "Factor A Time", "Factor A Other Arguments", "Factor A Type", "Factor A Polarity", "Relation Text", "Relation Normalization", "Relation Modifiers", "Factor B Text", "Factor B Normalization", "Factor B Location", "Factor B Time", "Factor B Other Arguments", "Factor B Type", "Factor B Polarity", "Location", "Time", "Evidence"]

        all_event_data = []
        for relid, kb_relation in kb.relid_to_kb_relation.items():
            if kb_relation.argument_pair_type == "event-event":
                for kb_relation_mention in kb_relation.relation_mentions:
                    left_event_mention = kb_relation_mention.left_mention
                    right_event_mention = kb_relation_mention.right_mention

                    if right_event_mention is None:
                        continue

                    event_data = dict()
                    event_data["Source"] = docid_to_source[kb_relation_mention.document.id]
                    event_data["System"] = "Hume"
                    event_data["Sentence ID (start and end document offsets)"] = self.get_sentence_offsets(left_event_mention, right_event_mention)

                    event_data["Factor A Text"] = self.get_event_text(left_event_mention)
                    event_data["Factor A Location"] = self.get_location(left_event_mention)
                    event_data["Factor A Time"] = self.get_time(left_event_mention)
                    event_data["Factor A Other Arguments"] = self.get_other_arguments(left_event_mention)
                    # TODO this code looks like it has been broken for a while
                    left_event_type = self.get_ontology_concept(left_event_mention.groundings, "NA", "event")
                    # event_data["Factor A Type"] = left_event_type
                    #(type_from_grounding, type_grounding_score, grounded_concepts) = \
                    #    JSONLDSerializer.get_grounding(self.get_event_text(left_event_mention),left_event_type,3)                    JSONLDSerializer serializer

                    # groundings_with_scores = JSONLDSerializer.get_ontology_concept_for_event(left_event_mention)
                    # (type_from_grounding, type_grounding_score) = groundings_with_scores[0]
                    type_from_grounding = "/event"
                    type_grounding_score = 1.0

                    event_data["Factor A Type"] = self.get_grounded_types(left_event_mention)
                    #type_from_grounding
                    event_data["Factor A Polarity"] = self.get_polarity(left_event_mention)

                    event_data["Relation Normalization"] = kb_relation.relation_type

                    event_data["Factor B Text"] = self.get_event_text(right_event_mention)
                    event_data["Factor B Location"] = self.get_location(right_event_mention)
                    event_data["Factor B Time"] = self.get_time(right_event_mention)
                    event_data["Factor B Other Arguments"] = self.get_other_arguments(right_event_mention)
                    # TODO this code looks like it has been broken for a while
                    right_event_type = self.get_ontology_concept(right_event_mention.groundings, "NA", "event")
                    event_data["Factor B Type"] = right_event_type
                    #(type_from_grounding, type_grounding_score, grounded_concepts) = \
                    #    JSONLDSerializer.get_grounding(self.get_event_text(right_event_mention),right_event_type,3)
                    # groundings_with_scores = JSONLDSerializer.get_ontology_concept_for_event(right_event_mention)
                    # (type_from_grounding, type_grounding_score) = groundings_with_scores[0]
                    type_from_grounding = "/event"
                    type_grounding_score = 1.0

                    event_data["Factor B Type"] = self.get_grounded_types(right_event_mention)
                    # type_from_grounding
                    event_data["Factor B Polarity"] = self.get_polarity(right_event_mention)

                    event_data["Evidence"] = self.get_evidence(left_event_mention, right_event_mention)

                    all_event_data.append(event_data)

        for field in fields:
            o.write(field)
            if field != fields[-1]:
                o.write("\t")
        o.write("\n")

        for event_data in all_event_data:
            for field in fields:
                if event_data.get(field) is not None:
                    o.write(self.clean(event_data[field]))
                if field != fields[-1]:
                    o.write("\t")
            o.write("\n")

    def get_sentence_offsets(self, em1, em2):
        sent1 = em1.sentence
        sent2 = em2.sentence

        start = min(sent1.start_offset, sent2.start_offset)
        end = max(sent1.end_offset, sent2.end_offset)

        return str(start) + "_" + str(end)

    # get triggering phrase
    def get_event_text(self, event_mention):
        if event_mention.triggering_phrase is not None and len(event_mention.triggering_phrase) > 0:
            return event_mention.triggering_phrase

        return event_mention.trigger

    '''
    def get_event_text(self, event_mention):
        if event_mention.trigger is not None:
            return event_mention.trigger
        elif event_mention.triggering_phrase is not None and len(event_mention.triggering_phrase) > 0:
            return event_mention.triggering_phrase
        else:
            return "NA"
    '''
            
    def get_evidence(self, em1, em2):
        if em1.sentence == em2.sentence:
            return em1.sentence.text
        else:
            return em1.sentence.text + " " + em2.sentence.text

    def get_polarity(self, event_mention):
        return event_mention.properties.get("polarity")

    def get_other_arguments(self, event_mention):
        rv = ""
        for role, arguments in event_mention.arguments.items():
            for argument in arguments:
                if isinstance(argument, KBTimeValueMention) or isinstance(argument, KBMoneyValueMention):
                    continue
                if role == "Place":
                    continue
                if len(rv) > 0:
                    rv += ", "
                rv += role + ": " + argument.mention_text
        if len(rv) == 0:
            return None
        return rv
            
    def get_time(self, event_mention):
        for role, arguments in event_mention.arguments.items():
            for argument in arguments:
                if isinstance(argument, KBTimeValueMention):
                    nd = argument.normalized_date
                    if nd is None:
                        continue
                    if WMTabularFormatSerializer.good_date_re.match(nd):
                        return argument.normalized_date
        return None

    def get_location(self, event_mention):
        places = event_mention.arguments.get("Place")
        if places is None or len(places) == 0:
            return None
        return places[0].mention_text
        
    def clean(self, string):
        string = string.replace("\n", " ")
        string = string.replace("\t", " ")
        return string


if __name__ == "__main__":
    import pickle,sys
    import logging
    logger = logging.getLogger(__name__)
    if len(sys.argv) != 4:
        print("Usage: " + sys.argv[0] + " pickled_kb_file metadata output_json_file")
        sys.exit(1)
    json_serializer = WMTabularFormatSerializer()
    with open(sys.argv[1], "rb") as pickle_stream:
        logger.info("Loading pickle file...")
        kb = pickle.load(pickle_stream)
        logger.info("Done loading. Serializing...")
        json_serializer.serialize(kb, sys.argv[2],sys.argv[3])
