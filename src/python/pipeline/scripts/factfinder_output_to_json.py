import sys, os, re, codecs, json, glob


class FactfinderOutputToJson:
    def __init__(self):
        pass

    class FactRelationMention:
        factType2KBPSlots = {
            "org_date_dissolved": "org:date_dissolved",
            "org_parents": "org:parents",
            "org_shareholders": "org:shareholders",
            "org_website": "org:website",
            "per_alternate_names": "per:alternate_names",
            "org_alternate_names": "org:alternate_names",
            "org_founded_by_serif": "org:founded_by",
            "org_members_serif": "org:members",
            "org_members": "org:members",
            "org_top_members_employees": "org:top_members_employees",
            "org_shareholders_serif": "org:shareholders",
            "org_subsidiary_serif": "org:subsidiaries",
            "per_charges_serif": "per:charges",
            "per_employee_or_member_of_serif": "per:employee_or_member_of",
            "per_employee_or_member_of": "per:employee_or_member_of",
            "per_date_of_death_serif": "per:date_of_death",
            "per_date_of_death": "per:date_of_death",
            "per_schools_attended_serif": "per:schools_attended",
            "per_schools_attended": "per:schools_attended",
            "per_spouse_serif": "per:spouse",
            "BirthDate": "per:date_of_birth",
            "DeathDate": "per:date_of_death",
            "Education": "per:schools_attended",
            "Employer": "per:employee_or_member_of",
            "Children": "per:children",
            "Parents": "per:parents",
            "per_parents": "per:parents",
            "Siblings": "per:siblings",
            "per_siblings": "per:siblings",
            "Spouse": "per:spouse",
            "per_spouse": "per:spouse",
            "Other_family": "per:other_family",
            "per_other_family": "per:other_family",
            "Founder": "org:founded_by",
            "org_founded_by": "org:founded_by",
            "FoundingDate": "org:date_founded",
            "org_date_founded": "org:date_founded",
            "PerTitle": "per:title",
            "per_date_of_birth": "per:date_of_birth",
            "per_title": "per:title"
        }

        def __init__(self, fields):

            filler = fields[12];
            isValue = filler.startswith("\"") and filler.endswith("\"")

            relnType = fields[1]
            docId = fields[0]

            role1 = fields[2]

            # for agent1
            srcEntityId = None
            queryType = None
            querySubType = None
            arg1_start = None
            arg1_end = None
            arg1_confidence = None
            arg1_linkConfidence = None
            arg1_brandyConfidence = None

            # for filler
            dstEntityId = None
            answerType = None
            answerSubType = None
            arg2_start = None
            arg2_end = None
            arg2_confidence = None
            arg2_linkConfidence = None
            arg2_brandyConfidence = None

            if role1=="AGENT1":
                srcEntityId = fields[3]
                queryType = fields[4]
                querySubType = fields[5]
                arg1_start = int(fields[6])
                arg1_end = int(fields[7])

                arg1_confidence = float(fields[8])
                arg1_linkConfidence = float(fields[9])
                arg1_brandyConfidence = fields[10].strip()

                dstEntityId = fields[12]
                answerType = fields[13]
                answerSubType = fields[14]
                arg2_start = int(fields[15])
                arg2_end = int(fields[16])

                if fields[17]=="NULL":
                    arg2_confidence = 0
                else:
                    arg2_confidence = float(fields[17])
                if fields[18]=="NULL":
                    arg2_linkConfidence = 0
                else:
                    arg2_linkConfidence = float(fields[18])
                arg2_brandyConfidence = fields[19].strip()
            else:
                dstEntityId = fields[3]
                answerType = fields[4]
                answerSubType = fields[5]
                arg2_start = int(fields[6])
                arg2_end = int(fields[7])

                arg2_confidence = float(fields[8])
                arg2_linkConfidence = float(fields[9])
                arg2_brandyConfidence = fields[10].strip()

                srcEntityId = fields[12]
                queryType = fields[13]
                querySubType = fields[14]
                arg1_start = int(fields[15])
                arg1_end = int(fields[16])

                if fields[17]=="NULL":
                    arg1_confidence = 0
                else:
                    arg1_confidence = float(fields[17])
                if fields[18]=="NULL":
                    arg1_linkConfidence = 0
                else:
                    arg1_linkConfidence = float(fields[18])
                arg1_brandyConfidence = fields[19].strip()

            self.sent_start = int(fields[20])
            self.sent_end = int(fields[21])

            self.confidence = float(fields[22])

            self.strTextArg1 = fields[23].strip()
            self.strTextArg2 = fields[24].strip()

            self.sentence_text = fields[25].strip()

            self.filler = filler
            self.isValue = isValue
            self.relnType = relnType
            self.docId = docId
            self.role1 = role1

            self.queryType = queryType
            self.querySubType = querySubType

            self.arg1_start = arg1_start
            self.arg1_end = arg1_end
            self.arg1_confidence = arg1_confidence
            self.arg1_linkConfidence = arg1_linkConfidence
            self.arg1_brandyConfidence = arg1_brandyConfidence

            # for filler
            self.dstEntityId = dstEntityId
            self.answerType = answerType
            self.answerSubType = answerSubType
            self.arg2_start = arg2_start
            self.arg2_end = arg2_end
            self.arg2_confidence = arg2_confidence
            self.arg2_linkConfidence = arg2_linkConfidence
            self.arg2_brandyConfidence = arg2_brandyConfidence

        def is_valid_then_get_slot(self):
            if not self.answerType.strip() or not self.queryType.strip():
                return None

            # these patterns has incorrect argument order
            if self.relnType == "per_parents_24" or \
                self.relnType == "per_parents_ds_29" or \
                self.relnType == "per_parents_ds_65" or \
                self.relnType == "per_parents_ds_80" or \
                self.relnType == "per_parents_ds_81" or \
                self.relnType == "per_parents_ds_89" or \
                self.relnType == "per_parents_ds_101" or \
                self.relnType == "per_parents_ds_106" or \
                self.relnType == "per_parents_ds_153" or \
                self.relnType == "per_parents_ds_216" or \
                self.relnType == "per_parents_ds_219" or \
                self.relnType == "per_alternate_names_11":
                print("SKIP:\tlow precision patterns\t" + self.relnType)
                return None

            if (self.relnType == "org_parents_1" or self.relnType == "org_parents_23" or \
                self.relnType == "org_parents_274" or self.relnType == "org_parents_ds_27" or \
                self.relnType == "org_parents_ds_120" or self.relnType == "org_parents_ds_156" or \
                self.relnType == "org_parents_ds_164" or self.relnType == "org_parents_ds_225" or \
                self.relnType == "org_parents_ds_274" or self.relnType == "org_parents_ds_276" or \
                self.relnType == "org_parents_ds_277" or self.relnType == "org_parents_ds_278" or \
                self.relnType == "org_parents_ds_332" or self.relnType == "org_parents_ds_333" or \
                self.relnType == "org_parents_ds_339" or self.relnType == "org_parents_ds_385" or \
                self.relnType == "org_parents_ds_386" or self.relnType == "org_parents_ds_387" or \
                self.relnType == "org_parents_ds_388" or self.relnType == "org_parents_ds_390" or \
                self.relnType == "org_parents_ds_391" or self.relnType == "org_parents_ds_411" or \
                self.relnType == "org_parents_ds_419" or self.relnType == "org_parents_ds_449" or \
                self.relnType == "org_parents_ds_455" or self.relnType == "org_parents_ds_546" or \
                self.relnType == "org_parents_ds_547" or self.relnType == "org_parents_ds_548" or \
                self.relnType == "org_parents_ds_549" or self.relnType == "org_parents_ds_550" or \
                self.relnType == "org_parents_ds_551" or self.relnType == "org_parents") \
                    and self.answerType == "GPE":
                print("SKIP:\torg_parents patterns only work for ORG\t" + self.relnType)
                return None

            # PER moved to ORG
            if (self.relnType == "per_employee_or_member_of_ds_618" or \
                self.relnType == "per_employee_or_member_of_ds_35" or \
                self.relnType == "per_employee_or_member_of_ds_86" or \
                self.relnType == "per_employee_or_member_of_ds_355" or \
                self.relnType == "per_employee_or_member_of_ds_222" or \
                self.relnType == "per_employee_or_member_of_ds_553" or \
                self.relnType == "per_employee_or_member_of_ds_278") \
                and self.answerType == "GPE":
                print("SKIP:\t\"moved_to\" pattern only works for ORG\t" + self.relnType)
                return None

            if self.relnType == "per_alternate_names_11":
                print("SKIP:\tbad alt_name pattern\t" + self.relnType)
                return None

            slot = self.fromFactTypeString(self.relnType, self.querySubType, self.answerSubType, self.strTextArg1, self.strTextArg2)

            if not slot:
                print("SKIP:\tno valid slot aligned\t" + self.relnType);
                return None

            if slot == "per:title" and not self.isValue:
                print("SKIP:\tslot is per:title but is not a value slot\t" + slot)

            # filters non-name alternate names
            if slot == "org:alternate_names" or slot == "per:alternate_names":
                return None

            return slot

        def fromFactTypeString(self, returnLabel, querySubType, answerSubType, strTextArg1, strTextArg2):
            # hack to get cs2015 patterns through
            if returnLabel.startswith("cs2015_"):
                newReturnLabel = returnLabel[returnLabel.index("_") + 1:]
                #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                returnLabel = newReturnLabel

            # use mapping table
            for factType in self.factType2KBPSlots.keys():
                if returnLabel.startswith(factType):
                    newReturnLabel = self.factType2KBPSlots.get(factType)
                    #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                    return newReturnLabel

            if returnLabel.startswith("per_place_of_birth_serif") or \
                    returnLabel.startswith("Country_of_birth") or \
                    returnLabel.startswith("per_place_of_birth"):
                newReturnLabel = "per:place_of_birth"
                #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                return newReturnLabel

            if returnLabel.startswith("per_place_of_death_serif") or \
                    returnLabel.startswith("per_place_of_death"):
                newReturnLabel = "per:place_of_death"
                #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                return newReturnLabel

            if returnLabel.startswith("Headquarters") or \
                    returnLabel.startswith("org_place_of_headquarters") or \
                    returnLabel.startswith("GPENestedInORG"):
                newReturnLabel = "org:place_of_headquarters"
                #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                return newReturnLabel

            if returnLabel.startswith("resident_of") or returnLabel.startswith("per_place_of_residence"):
                newReturnLabel = "per:place_of_residence"
                #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                return newReturnLabel

            if returnLabel.startswith("per_origin"):
                if answerSubType=="Nation":
                    newReturnLabel = "per:country_of_origin"
                    #print("Change fact type: " + returnLabel + " -> " + newReturnLabel)
                    return newReturnLabel

            print ("invalid type: " + returnLabel)
            return None

    def to_simplified_relation_json(self, fact_relation_mention, slot):
        reln = dict()
        reln["docid"] = fact_relation_mention.docId
        reln["semantic_class"] = slot
        reln["arg1_span_list"] = [fact_relation_mention.arg1_start, fact_relation_mention.arg1_end]
        reln["arg1_text"] = [fact_relation_mention.strTextArg1]
        reln["arg2_span_list"] = [fact_relation_mention.arg2_start, fact_relation_mention.arg2_end]
        reln["arg2_text"] = [fact_relation_mention.strTextArg2]
        reln["sentence_text"] = fact_relation_mention.sentence_text
        return reln

    def get_docid_and_arg1_and_arg2(self, fact_relation_mention):
        return fact_relation_mention.docId + "-" + \
               str(fact_relation_mention.arg1_start) + "-" + str(fact_relation_mention.arg1_end) + "-" + \
               str(fact_relation_mention.arg2_start) + "-" + str(fact_relation_mention.arg2_end)

    def process(self, master_input_dir, output_file):
        existing_docid_arg1_relation_arg2 = set() # this is to deduplicate
        list_fact_relation_mention = []

        dirnames = os.listdir(master_input_dir)
        for dirname in dirnames:
            batch_dir = os.path.join(master_input_dir, dirname)
            if not os.path.isdir(batch_dir):
                continue
            factfinder_dir = os.path.join(batch_dir, "factfinder")
            factfinder_filenames = os.listdir(factfinder_dir)
            for factfinder_filename in factfinder_filenames:
                if not factfinder_filename.endswith(".kb"):
                    continue
                print "Processing: " + factfinder_filename
                factfinder_file = os.path.join(factfinder_dir, factfinder_filename)
                with open(factfinder_file, 'r') as f2:
                    for sline in f2:
                        # preprocessing
                        sline = sline.strip()
                        sline = sline.replace("\t\t", "\t")
                        fields = sline.strip().split("\t")
                        if len(fields) < 25:
                            #print("Not a relation mention: " + sline)
                            pass
                        else:
                            fact_relation_mention = self.FactRelationMention(fields)
                            slot = fact_relation_mention.is_valid_then_get_slot()
                            if slot is not None:
                                docid_arg1_relation_arg2 = self.get_docid_and_arg1_and_arg2(fact_relation_mention) + "-" + slot
                                if docid_arg1_relation_arg2 not in existing_docid_arg1_relation_arg2: # this is to deduplicate
                                    # print(fact_relation_mention)
                                    json_dict = self.to_simplified_relation_json(fact_relation_mention, slot)
                                    list_fact_relation_mention.append(json_dict)
                                    existing_docid_arg1_relation_arg2.add(docid_arg1_relation_arg2)

        # dump into a JSON file
        print("dumping into json file...")
        o = codecs.open(output_file, 'w', encoding='utf8')
        o.write(json.dumps(list_fact_relation_mention, sort_keys=True, indent=4))
        o.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: " + sys.argv[0] + " master_input_dir output_json_file"
        sys.exit(1)

    master_input_dir, output_json_file = sys.argv[1:]
    fact_relation_mention_reader = FactfinderOutputToJson()
    
    fact_relation_mention_reader.process(master_input_dir, output_json_file)
