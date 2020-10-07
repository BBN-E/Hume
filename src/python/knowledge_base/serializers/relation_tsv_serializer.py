import codecs
import json


class RelationTSVSerializer:
    def __init__(self):
        pass

    def serialize(self, kb, output_tsv_file):
        print("RelationTSVSerializer SERIALIZE")

        o = codecs.open(output_tsv_file, 'w', encoding='utf8')
        
        all_causal_relation_mentions = []
        for relid, relation in kb.get_relations():
            if relation.argument_pair_type != "event-event":
                continue

            for relation_mention in relation.relation_mentions:
                all_causal_relation_mentions.append((relation_mention, relation,))

        all_causal_relation_mentions.sort(key=lambda x: x[0].document.id)
        for relation_mention, relation in all_causal_relation_mentions:
            
            left_event_mention = relation_mention.left_mention
            right_event_mention = relation_mention.right_mention
            left_sentence = left_event_mention.sentence
            right_sentence = right_event_mention.sentence

            left_trigger = self.get_trigger(left_event_mention)
            right_trigger = self.get_trigger(right_event_mention)
            model = self.get_model(relation_mention)
            pattern = self.get_pattern(relation_mention)

            # Get text of sentence(s)
            sentence_text = self.clean_string(left_sentence.text)
            if left_sentence.start_offset < right_sentence.start_offset:
                sentence_text += " " + self.clean_string(right_sentence.text)
            elif left_sentence.start_offset > right_sentence.start_offset:
                sentence_text = self.clean_string(right_sentence.text) + " " + sentence_text
                
            if left_event_mention.sentence != right_event_mention.sentence:
                sentence_text = sentence_text + " " + self.clean_string(right_event_mention.sentence.text)
            
            o.write(relation_mention.id + "\t" +
                    relation.relation_type + "\t" +
                    model + "\t" +
                    json.dumps({
                        k: v for k, v in
                        left_event_mention.external_ontology_sources}) + "\t" +
                    left_event_mention.model + "\t" +
                    self.clean_string(left_trigger) + "\t" +
                    json.dumps({
                        k: v for k, v in
                        right_event_mention.external_ontology_sources}) + "\t" +
                    right_event_mention.model + "\t" +
                    self.clean_string(right_trigger) + "\t" +
                    relation_mention.document.id + "\t" +
                    self.clean_string(pattern) + "\t" +
                    sentence_text + "\n"
                    )
                
        o.close()

    def clean_string(self, s):
        return s.replace("\n", " ").replace("\t", " ")

    def get_trigger(self, em):
        if em.triggering_phrase is not None and len(em.triggering_phrase) > 0:
            return em.triggering_phrase
        if em.trigger is not None and len(em.trigger) > 0:
            return em.trigger

        if len(em.proposition_infos) > 0:
            return em.proposition_infos[0][0] # Predicate of first proposition on ACCENT event
        
        return "NO_TRIGGER"

    def get_model(self, rm):
        if rm.properties.get("model"):
            return rm.properties["model"]
        return "UNKNOWN_MODEL"
    
    def get_pattern(self, rm):
        if rm.properties.get("pattern"):
            return rm.properties["pattern"]
        return "UNKNOWN_PATTERN"
