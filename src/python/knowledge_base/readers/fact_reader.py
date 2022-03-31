import json

from elements.kb_event import KBEvent
from elements.kb_event_mention import KBEventMention
from elements.kb_mention import KBMention
from elements.kb_relation import KBRelation
from elements.kb_relation_mention import KBRelationMention
from elements.kb_value_mention import KBValueMention
from internal_ontology import OntologyMapper
from shared_id_manager.shared_id_manager import SharedIDManager


class FactReader:
    # Maps semantic class from facts.json in causeex_pipeline output
    # to (ACE-relation-type, reverse-flag,)
    semantic_class_to_relation_type = {
        "org:parents": ("PART-WHOLE.Subsidiary", False,),
        "org:subsidiaries": ("PART-WHOLE.Subsidiary", True,),
        "org:shareholders": ("ORG-AFF.Investor-Shareholder", True,),
        "org:founded_by": ("ORG-AFF.Founder", True,),
        "org:members": ("ORG-AFF.Membership", True,),
        "org:top_members_employees": ("ORG-AFF.Employment", True),
        "per:employee_or_member_of": ("ORG-AFF.Employment", False,),
        "per:schools_attended": ("ORG-AFF.Student-Alum", False,),
        "per:spouse": ("PER-SOC.Family", False,),
        "per:children": ("PER-SOC.Family", False,),
        "per:parents": ("PER-SOC.Family", False,),
        "per:siblings": ("PER-SOC.Family", False,),
        "per:other_family": ("PER-SOC.Family", False,),
        "org:place_of_headquarters": ("GEN-AFF.Org-Location", False,),
        "per:place_of_residence": ("GEN-AFF.Citizen-Resident-Religion-Ethnicity", False,),
        "per:country_of_origin": ("GEN-AFF.Citizen-Resident-Religion-Ethnicity", False,),
        "per:place_of_birth": ("GEN-AFF.Citizen-Resident-Religion-Ethnicity", False,),
    }

    def __init__(self):
        pass

    def read(self, kb, factfinder_json_file, event_ontology_yaml, ontology_flags
             ):
        print("FactReader READ")

        ontology_mapper = OntologyMapper()
        ontology_mapper.load_ontology(event_ontology_yaml)

        docid_to_ff_relations = self.load_docid_to_ff_relations(factfinder_json_file)

        document_mentions = dict() # docid -> list of KBMention objects
        for kb_entity_id, kb_entity in kb.get_entities():
            for kb_mention in kb_entity.mentions:
                docid = kb_mention.document.id
                if docid not in document_mentions:
                    document_mentions[docid] = []
                document_mentions[docid].append(kb_mention)
        
        document_relations = dict() # docid -> list of known KBRelations
        for kb_relation_id, kb_relation in kb.get_relations():
            if kb_relation.argument_pair_type != "entity-entity":
                continue
            for kb_relation_mention in kb_relation.relation_mentions:
                docid = kb_relation_mention.document.id
                if docid not in document_relations:
                    document_relations[docid] = []
                document_relations[docid].append(kb_relation)
                #print "Seen: " + kb_relation.relation_type + " " + kb_relation.left_argument_id + " " + kb_relation.right_argument_id
                
        # Use Factfinder facts to augment KB info
        for docid, mention_list in document_mentions.items():
            kb_document =  kb.docid_to_kb_document[docid]
            mention_span_to_mention = dict() # (start_char, end_char,) => KBMention
            for kb_mention in mention_list:
                mention_span = (kb_mention.head_start_char, kb_mention.head_end_char,)
                mention_span_to_mention[mention_span] = kb_mention

            doc_ff_relation_list = []
            if docid in docid_to_ff_relations:
                doc_ff_relation_list = docid_to_ff_relations[docid]

            for ff_rm in doc_ff_relation_list:
                arg1_span = (ff_rm["arg1_span_list"][0], ff_rm["arg1_span_list"][1])
                
                if arg1_span not in mention_span_to_mention:
                    continue

                # Arg1
                kb_mention1 = mention_span_to_mention[arg1_span]
                if kb_mention1 not in kb.kb_mention_to_entid:
                    continue
                entity_id = kb.kb_mention_to_entid[kb_mention1]
                kb_entity1 = kb.entid_to_kb_entity[entity_id]
                
                # Map this class into a known relation type if possible
                semantic_class = ff_rm["semantic_class"]
                if semantic_class in FactReader.semantic_class_to_relation_type:
                    relation_type, reverse_flag = FactReader.semantic_class_to_relation_type[semantic_class]
                    arg2_span = (ff_rm["arg2_span_list"][0], ff_rm["arg2_span_list"][1])
                    if arg2_span not in mention_span_to_mention:
                        continue
                    kb_mention2 = mention_span_to_mention[arg2_span]
                    if kb_mention2 not in kb.kb_mention_to_entid:
                        continue
                    entity_id = kb.kb_mention_to_entid[kb_mention2]
                    kb_entity2 = kb.entid_to_kb_entity[entity_id]
                    if reverse_flag:
                        temp = kb_mention1
                        kb_mention1 = kb_mention2
                        kb_mention2 = temp
                        temp = kb_entity1
                        kb_entity1 = kb_entity2
                        kb_entity2 = temp
                    if self.is_already_known_relation(kb_entity1, kb_entity2, relation_type, document_relations.get(docid)):
                        #print "Already known relation: " + kb_entity1.id + " " + kb_entity2.id + " " + relation_type
                        continue
                    kb_sentence = self.get_kb_sentence(kb_document, arg2_span[0], arg2_span[1])
                    if kb_sentence is None:
                        print("WARNING: could not find KBSentence for " + docid + " " + arg2_span[0] + " " + arg2_span[1])
                        continue
                    # Make a relation from the various pieces we've figured out above
                    relation_id = SharedIDManager.get_in_document_id("Relation", docid)
                    relation_mention_id = SharedIDManager.get_in_document_id("RelationMention", docid)
                    snippet = [kb_sentence.text, kb_sentence.start_offset, kb_sentence.end_offset]
                    relation = KBRelation(relation_id, "entity-entity", relation_type, kb_entity1.id, kb_entity2.id)
                    relation_mention = KBRelationMention(relation_mention_id, kb_mention1, kb_mention2, snippet, kb_document)
                    relation.add_relation_mention(relation_mention)
                    kb.add_relation(relation)

                    #print "New relation: " + relation.id + " " + kb_mention1.mention_head_text + " " + kb_mention2.mention_head_text + " " + relation_type
                    #print "Entities: " + kb_entity1.id + " " + kb_entity2.id
                    #print " --------- "

                    # Add to seen relations
                    if docid not in document_relations:
                        document_relations[docid] = []
                    document_relations[docid].append(relation)

                # per:title -- special case, since it uses a title value mention as one of its slots
                if semantic_class == "per:title" and kb_mention1.entity_type == "PER":
                            
                    title_text = ff_rm["arg2_text"][0]
                    if kb_entity1.canonical_name is not None and kb_entity1.canonical_name != title_text:
                        # We have a good title, make a Job-Title value mention out of it
                        job_title_start_offset = ff_rm["arg2_span_list"][0]
                        job_title_end_offset = ff_rm["arg2_span_list"][1]
                        value_mention_id = SharedIDManager.get_in_document_id("ValueMention", docid)
                        kb_sentence = self.get_kb_sentence(kb_document, job_title_start_offset, job_title_end_offset)
                        if kb_sentence is None:
                            print("WARNING: could not find KBSentence for " + docid + " " + str(job_title_start_offset) + " " + str(job_title_end_offset))
                            continue
                        value_mention = KBValueMention(value_mention_id, "Job-Title", title_text, kb_document, job_title_start_offset, job_title_end_offset, kb_sentence,title_text)

                        # Make an event from the mention and the value mention
                        event_id = SharedIDManager.get_in_document_id("Event", docid)
                        event_mention_id = SharedIDManager.get_in_document_id("EventMention", docid)
                        snippet = [kb_sentence.text, kb_sentence.start_offset, kb_sentence.end_offset]
                        event = KBEvent(event_id, None)  # event_type deprecated
                        event_mention = KBEventMention(
                            event_mention_id, kb_document, title_text,
                            job_title_start_offset, job_title_end_offset, snippet,
                            [], [], kb_sentence, [], None, "FACTFINDER",0.5,title_text,None,None)

                        for flag in ontology_flags.split(','):
                            for mapping in (
                                    ontology_mapper.look_up_external_types(
                                        'Affiliation', flag)):
                                event_mention.add_or_change_grounding(
                                    mapping, 0.5)

                        event.add_event_mention(event_mention)
                        event_mention.add_argument("Person", kb_mention1,0.5)
                        event_mention.add_argument("Position", value_mention,0.5)
                        kb.add_event(event)

    def get_kb_sentence(self, document, start_offset, end_offset):
        for sentence in document.sentences:
            if start_offset >= sentence.start_offset and end_offset <= sentence.end_offset:
                return sentence
        return None

    def load_docid_to_ff_relations(self, factfinder_json_file):
        docid_to_relations = dict()
        
        with open(factfinder_json_file) as fp:
            list_fact_relation_mention = json.load(fp)
            for ff_relation_mention in list_fact_relation_mention:
                docid=ff_relation_mention["docid"]
                docid_to_relations.setdefault(docid,list()).append(ff_relation_mention)
        return docid_to_relations
    
    def is_already_known_relation(self, entity1, entity2, relation_type, known_relations):
        if not known_relations:
            return False
        
        for known_relation in known_relations:
            if (known_relation.relation_type == relation_type and
                known_relation.left_argument_id == entity1.id and 
                known_relation.right_argument_id == entity2.id):
                return True
        
        return False

    def is_already_known_position(self, entity, job_title_value_mention, known_event_mentions, kb):
        if not known_event_mentions:
            return False

        for known_event_mention in known_event_mentions:
            if (self.has_argument(known_event_mention, entity, kb) and
                self.has_matching_position(known_event_mention, job_title_value_mention)):
                return True
        return False


    def has_argument(self, event_mention, entity, kb):
        for arg_list in event_mention.arguments.values(): # values() returns a list of lists
            for arg in arg_list:
                if not isinstance(arg, KBMention):
                    continue
                arg_entity_id = kb.kb_mention_to_entid[arg]
                arg_entity = kb.entid_to_kb_entity[arg_entity_id]
                if arg_entity == entity:
                    return True
        return False

    def has_matching_position(self, event_mention, value_mention):
        if "Position" not in event_mention.arguments:
            return False
        for arg in event_mention.arguments["Position"]:
            if (value_mention.head_start_char >= arg.head_start_char and
                value_mention.head_end_char <= arg.head_end_char):
                return True
        return False
