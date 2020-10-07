
import os

try:
    from .grounder import *
    from .mention_candidate import *
except ImportError:  # relative import invalid if calling test script directly
    from grounder import *
    from mention_candidate import *

script_dir = os.path.dirname(os.path.realpath(__file__))
project_dir = os.path.join(script_dir, "..", "..", "..")

try:
    sys.path.insert(
        0, os.path.join(project_dir, 'src', 'python', 'knowledge_base'))
    from internal_ontology import Ontology
    from internal_ontology import OntologyMapper
except ImportError as e:
    raise e


class CXTestSetup(object):

    def __init__(self):
        ont_dir = "{}/resource/ontologies/internal/causeex".format(project_dir)
        self.default_flag = "CAUSEEX"
        self.embeddings_file = "/nfs/raid87/u10/shared/Hume/common/glove.6B.50d.p"
        self.exemplars_json = "{}/data_example_events.json".format(ont_dir)
        self.internal_yaml_path = "{}/event_ontology.yaml".format(ont_dir)
        self.centroids_json = "{}/event_centroid.json".format(ont_dir)
        self.min_groundings = 5
        self.threshold = 0.7
        self.modes = [
                utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME
        ]
        self.bert_docid_to_npz = None

        self.test_cases = [
            #
            #
            {"phrase": "his 2020 re-election bid",
             "entry_points": ['Attempt', 'ElectionCampaign'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#ElectionCampaign"
             },
            {"phrase": "inquiry into Russia",
             "entry_points": ['ExploratoryCommunication', 'Investigation'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Investigation"
             },
            {"phrase": "Russia has denied election interference",
             "entry_points": ['Denial', 'Election'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Denial"
             },
            {"phrase": "saying",
             "entry_points": ['DeclarativeCommunication'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#DeclarativeCommunication"
             },
            {"phrase": "the sex-trafficking law",
             "entry_points": ['GoverningDirective'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#GoverningDirective"
             },
            {"phrase": "deception to prevent plaintiffs",
             "entry_points": ['DisinformationCampaign', 'PsychologicalAttack',
                              'DeceptiveCommunication'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Deception"
             },
            {"phrase": "suit",
             "entry_points": ['FilingOfLawsuit'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#FilingOfLawsuit"
             },
            {"phrase": "intimidate journalists",
             "entry_points": ['Threatening'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#IntimidationAndCoercion"
             },
            {"phrase": "alleged assaults",
             "entry_points": ['DeclarativeCommunication', 'CriminalAct',
                              'PhysicalAssault'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#PhysicalAssault"
             },
            {"phrase": "dismissing all defendants",
             "entry_points": ['Cooperation'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#FindingOfNotGuilty"
             },
            #
            #
            {"phrase": "meetings with young women",
             "entry_points": ['MeetingOrEncounter'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#MeetingOrEncounter"
             },
            {"phrase": "say they",
             "entry_points": ['DeclarativeCommunication'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#DeclarativeCommunication"
             },
            {"phrase": "We are disappointed that certain claims",
             "entry_points": ['CommunicationConveyingEmotion'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#CommunicationConveyingPessimism"
             },
            {"phrase": "the sex-trafficking allegation",
             "entry_points": ['Accusation'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#AccusationOrAssigningOfResponsibility"
             },
            {"phrase": "said in a statement",
             "entry_points": ['IssuingPublishingOrReleasing',
                              'DeclarativeCommunication'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#IssuingPublishingOrReleasing"
             },
            {"phrase": "trial in state court",
             "entry_points": ['LegalProceedingsOrTrial'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#LegalProceedingsOrTrial"
             },
            {"phrase": "criminal sexual assault charges",
             "entry_points": ['CriminalAct', 'SexualAssault', 'Indictment'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Indictment"
             },
            {"phrase": "A lawsuit seeking to represent any woman",
             "entry_points": ['RequestAppealOrDemand', 'RequestOrAppeal',
                              'FilingOfLawsuit'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#FilingOfLawsuit"
             },
            {"phrase": "Additional reporting by David Morgan",
             "entry_points": ['Announcement', 'Reporting'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Reporting"
             },
            {"phrase": "own prior contacts with Russia",
             "entry_points": ['Ownership'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Communication"
             },
            #
            #
            {"phrase": "efforts to convince Sessions",
             "entry_points": ['Attempt'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#RequestAppealOrDemand"
             },
            {"phrase": "believe they",
             "entry_points": ['Belief'],
             "gold": "http://graph.causeex.com/bbn#Belief"
             },
            {"phrase": "14 criminal referrals for investigation",
             "entry_points": ['CriminalAct'],
             "gold": "http://graph.causeex.com/bbn#Complaint"
             },
            {"phrase": "they are open investigations",
             "entry_points": ['Investigation'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Investigation"
             },
            {"phrase": "a subpoena to force Trump",
             "entry_points": ['LegalEvent'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#LegalEvent"
             },
            {"phrase": "a criminal conspiracy with Moscow",
             "entry_points": ['CriminalAct'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#CriminalActOrCorruption"
             },
            {"phrase": "concluded",
             "entry_points": ['DeclarativeCommunication',
                              'DecisionOrRecommendation'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#DecisionOrRecommendation"
             },
            {"phrase": "hacked Democratic emails",
             "entry_points": ['CyberAttack', 'Democracy',
                              'CommunicationViaInstantOrTextMessage'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#CyberAttack"
             },
            {"phrase": "shown that they",
             "entry_points": ['ShowOrExhibit'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#ShowOrExhibit"
             },
            {"phrase": "supported",
             "entry_points": ['Dependance', 'DefenseOrSupport'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#DefenseOrSupport"
             },
            #
            #
            {"phrase": "a pardon to a former aide",
             "entry_points": ['Pardon'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Pardon"
             },
            {
             "phrase": "The Democratic chairman of the House Judiciary Committee",
             "entry_points": ['Democracy'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Event"
            },
            {"phrase": "ELECTION MEDDLING",
             "entry_points": ['Election'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#Corruption"
             },
            {"phrase": "described as a Russian campaign of hacking",
             "entry_points": ['DeclarativeCommunication', 'CyberAttack'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#CyberAttack"
             },
            {"phrase": "Any impeachment effort",
             "entry_points": ['LegalEvent', 'Attempt'],
             "gold": "http://ontology.causeex.com/ontology/odps/Event#LegalProceedingsOrTrial"
             },
        ]
        '''
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            #
            #
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
            {"phrase": "",
             "entry_points": ,
             "gold": ""
             },
        ]
        '''
        self.test_cases_dict = {
            (case['phrase'], str(sorted(case['entry_points']))): case['gold']
            for case in self.test_cases
        }
        for k in sorted(self.test_cases_dict):
            print(k)

    def match_against_cases(self, mention_candidate, entry_points):
        return self.test_cases_dict.get(
            (mention_candidate.get_original_mention_string(),
             str(sorted(entry_points))))

    def add_npz_info(self, npz_filelist):
        self.bert_docid_to_npz = utils.build_docid_to_npz_map(npz_filelist)
        bert_mode = (utils.SimilarityMode
                     .COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT)
        self.modes.insert(0, bert_mode)


class CXTestSetupWithOMG(CXTestSetup):

    def __init__(self):
        super(CXTestSetupWithOMG, self).__init__()
        self.mapper = OntologyMapper()
        self.mapper.load_ontology(self.internal_yaml_path)
        self.ontology = Ontology()
        self.ontology.load_from_internal_yaml(self.internal_yaml_path)
        exemplars = Ontology.load_internal_exemplars(self.exemplars_json)
        self.ontology.add_internal_exemplars(exemplars, None, None)
        self.ontology.init_embeddings(self.embeddings_file)
        self.ontology.add_embeddings_to_nodes()
        centroids = utils.load_json(self.centroids_json)
        self.ontology.add_node_contextual_embeddings_with_name(centroids)
        self.grounder = Grounder(self.ontology, self.min_groundings)


class WMTestSetup(object):

    def __init__(self):
        self.flag = "WM"
        self.embeddings_file = "/nfs/raid87/u10/shared/Hume/common/glove.6B.50d.p"
        self.exemplars_json = (
            "{}/resource/ontologies/internal/hume/data_example_events.json"
            .format(project_dir))
        self.min_groundings = 5
        self.threshold = 0.7
        self.yaml_path = "/nfs/raid85/u13/users/criley/repos/WM_Ontologies/wm_metadata.yml"
        self.internal_yaml_path = (
            "{}/resource/ontologies/internal/hume/event_ontology.yaml"
            .format(project_dir))
        self.blacklist_path = "/nfs/raid87/u10/shared/Hume/wm/wm.blacklist.json"
        self.root_path = "/wm/concept/causal_factor"
        self.modes = [
                utils.SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG,
                utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME
        ]
        try:
            stops = ('{}/resource/ontologies/internal/hume/stopwords.list'
                     .format(project_dir))
            keywords = ('{}/resource/ontologies/internal/hume/'
                        'keywords-anchor_annotation.txt'.format(project_dir))
            self.stopwords = utils.read_stopwords_from_hume_resources(stops)
            self.keywords = utils.read_keywords_from_bbn_annotation(keywords)
            self.blacklist = set(utils.load_json(self.blacklist_path))
        except IOError:
            self.stopwords = None
            self.keywords = None
            self.blacklist = None


class WMTestSetupWithOMG(WMTestSetup):

    def __init__(self):
        super(WMTestSetupWithOMG, self).__init__()
        self.ontology = Ontology()
        self.ontology.load_from_yaml_with_metadata(self.yaml_path)
        self.ontology.init_embeddings(self.embeddings_file)
        self.ontology.add_embeddings_to_nodes()
        self.ontology_mapper = OntologyMapper()
        self.ontology_mapper.load_ontology(self.internal_yaml_path)
        self.grounder = Grounder(self.ontology, self.min_groundings)
        self.grounder.build_grounder(self.keywords, self.stopwords)
        self.grounder.specify_user_root_path(self.root_path)


def _test_wm_timing():
    mentions_path = '/nfs/raid88/u10/users/ychan/repos/Hume/temp/anchor_context.log'
    mentions_with_int = []
    with io.open(mentions_path, encoding='utf8') as f:
        for line in f:
            _, ep, anchor, mention = line.strip().split('\t', 3)
            mentions_with_int.append({
                "sentence": "tmp_sentence",
                "mention_str": mention,
                "entry_point": ep
            })
    wm_test_setup = WMTestSetupWithOMG()
    grounder = wm_test_setup.grounder

    time_before_grounding_from_int = time.time()
    counter = 0
    for m in mentions_with_int:
        counter += 1
        candidate = MentionCandidate(
            m.get('mention_str'),
            m.get('sentence')
        )
        candidate.add_structured_data(grounder.get_keywords())
        candidate.remove_stopwords_from_mention(grounder.get_stopwords())
        last_time = time.time()
        groundings = grounder.ground_mention(
            candidate,
            [],
            wm_test_setup.threshold)
        next_time = time.time()

        print('------')
        print(candidate)
        for (p, s) in groundings:
            print(s, p)
        print('Time to ground mention:', next_time - last_time)
        print('------')

    final_time = time.time()
    print('Time to ground all {} in batch:'.format(counter),
          final_time - time_before_grounding_from_int)


def _test_cx_icm_bert_grounding():
    npz_file = "/home/criley/raid/Hume/cx_icm_test.npz_list"
    _test_cx_grounding(npz_filelist=npz_file, flag="ICM")


def _test_cx_icm_grounding():
    _test_cx_grounding(flag="ICM")


def _test_cx_bert_grounding():
    npz_file = "/home/criley/raid/Hume/cx_icm_test.npz_list"
    _test_cx_grounding(npz_filelist=npz_file)


def _test_cx_grounding(npz_filelist=None, flag="CAUSEEX"):
    inputs = ["/home/criley/raid/Hume/cx_icm_test_1.serifxml",
              "/home/criley/raid/Hume/cx_icm_test_2.serifxml"]

    sys.path.insert(0, '{}/src/python/misc/'.format(project_dir))
    from ground_serifxml import read_serifxml_event_mentions

    cx_setup = CXTestSetupWithOMG()

    if npz_filelist is not None:
        cx_setup.add_npz_info(npz_filelist)

    print_data = []
    data = []
    correct_in_top_1 = 0
    correct_in_top_k = 0
    correct_in_entry_points = 0
    correct_in_top_k_but_not_entry_points = 0
    test_cases_seen = 0
    for input in inputs:
        docid, mentions_and_entry_points = read_serifxml_event_mentions(
            input,
            {},
            set(),
            cx_setup.ontology,
            cx_setup.mapper,
            flag,
            cx_setup.bert_docid_to_npz
        )

        print_data.append(input)

        for (mention_candidate,
             entry_points,
             serifxml_types) in mentions_and_entry_points:

            groundings = cx_setup.grounder.ground_mention(
                mention_candidate,
                entry_points,
                cx_setup.threshold,
                modes=cx_setup.modes,
                force_entry_points=False,
                verbose=0
            )

            cx_setup.grounder.set_k(cx_setup.min_groundings)
            new_groundings = cx_setup.mapper.map_internal_paths_to_k_sources(
                groundings, cx_setup.grounder, flag)

            '''
            #
            # (1/2) this chunk of code is for checking vs. specified test cases.
            # it is brittle and temporary!
            #
            gold = cx_setup.match_against_cases(mention_candidate, entry_points)
            if gold:
                test_cases_seen += 1
                correct_is_in_entry_points = False
                for entry_point in entry_points:
                    entry_point_sources = (
                        cx_setup.mapper.look_up_external_types(
                            entry_point, cx_setup.default_flag))
                    if gold in entry_point_sources:
                        correct_is_in_entry_points = True
                if correct_is_in_entry_points:
                    correct_in_entry_points += 1
                grounded_paths = [path for path, _ in new_groundings]
                if len(grounded_paths) > 0:
                    if grounded_paths[0] == gold:
                        correct_in_top_1 += 1
                        to_print = "\n  ".join(
                            [str(pair) for pair in new_groundings])
                        data.append(
                            "Good grounding:\n{}\n --> [\n{}\n]".format(
                                mention_candidate, to_print))
                    if gold in grounded_paths:
                        correct_in_top_k += 1
                        to_print = "\n  ".join(
                            [str(pair) for pair in new_groundings])
                        data.append(
                            "Acceptable grounding:\n{}\n --> [\n{}\n]".format(
                                mention_candidate, to_print))
                        if not correct_is_in_entry_points:
                            correct_in_top_k_but_not_entry_points += 1
                    else:
                        to_print = "\n  ".join(
                            [str(pair) for pair in new_groundings])
                        data.append(
                            "Bad grounding:\n{}\n --> [\n{}\n]".format(
                                mention_candidate, to_print))
            #
            #
            #
            '''

            #
            # this chunk of code is for reviewing all
            #
            grounding_print = (
                "\n  ".join(["["] + [str(pair) for pair in groundings] + ["]"])
                + "\n - mapped to - \n"
                + "\n  ".join(
                    ["["] + [str(pair) for pair in new_groundings] + ["]"]))
            print_data.append("{}\n{}\n{}".format(
                mention_candidate,
                entry_points,
                grounding_print))

    for datum in print_data:
        print("###\n{}\n###".format(datum))
    #
    #
    #

    '''
    #
    # (2/2) specified test cases review
    #
    for datum in data:
        print("###\n{}\n###\n".format(datum))
    print(
        "{:.1f}% ({}/{}) gold in entry points\n{:.1f}% ({}/{}) gold in top "
        "1\n{:.1f}% ({}/{}) gold in top {}\n{:.1f}% ({}/{}) gold in top {} but "
        "not in entry points".format(
            100 * correct_in_entry_points / test_cases_seen,
            correct_in_entry_points,
            test_cases_seen,
            100 * correct_in_top_1 / test_cases_seen,
            correct_in_top_1,
            test_cases_seen,
            100 * correct_in_top_k / test_cases_seen,
            correct_in_top_k,
            test_cases_seen,
            cx_setup.min_groundings,
            100 * correct_in_top_k_but_not_entry_points / (
                test_cases_seen - correct_in_entry_points),
            correct_in_top_k_but_not_entry_points,
            test_cases_seen - correct_in_entry_points,
            cx_setup.min_groundings))
    #
    #
    #
    '''


def _test_cx_test_cases(npz_filelist=None):

    cx_setup = CXTestSetupWithOMG()
    test_cases = cx_setup.test_cases

    # validate
    seen = set()
    for item in test_cases:
        gold = item['gold']
        names = cx_setup.mapper.look_up_internal_types_mapped_to_source(
            gold, cx_setup.default_flag)
        nodes = []
        for name in names:
            nodes.extend(cx_setup.ontology.get_nodes_by_name(name))
        if len(nodes) == 0:
            raise IOError("Invalid test case: gold standard node {} does not "
                          "exist in ontology".format(item['gold']))
        seen_key = "|||".join([item['gold'], item['phrase']]
                              + item['entry_points'])
        if seen_key in seen:
            raise IOError("Test case appears more than once: {}".format(item))
        seen.add(seen_key)

    if npz_filelist is not None:
        cx_setup.add_npz_info(npz_filelist)

    data = []
    correct_in_top_1 = 0
    correct_in_top_k = 0
    correct_in_entry_points = 0
    correct_in_top_k_but_not_entry_points = 0
    for case in test_cases:
        candidate = MentionCandidate(case["phrase"], "DUMMY")
        entry_points = case["entry_points"]
        gold = case['gold']

        correct_is_in_entry_points = False
        for entry_point in entry_points:
            entry_point_sources = cx_setup.mapper.look_up_external_types(
                entry_point, cx_setup.default_flag)
            if gold in entry_point_sources:
                correct_is_in_entry_points = True
        if correct_is_in_entry_points:
            correct_in_entry_points += 1

        groundings = cx_setup.grounder.ground_mention(
            candidate,
            entry_points,
            cx_setup.threshold,
            modes=cx_setup.modes,
            force_entry_points=False,
            verbose=1
        )

        cx_setup.grounder.set_k(cx_setup.min_groundings)
        groundings = cx_setup.mapper.map_internal_paths_to_k_sources(
            groundings, cx_setup.grounder, cx_setup.default_flag)
            
        grounded_paths = [path for path, _ in groundings]
        
        if len(grounded_paths) > 0:
            if grounded_paths[0] == gold:
                correct_in_top_1 += 1
            if gold in grounded_paths:
                correct_in_top_k += 1
                if not correct_is_in_entry_points:
                    correct_in_top_k_but_not_entry_points += 1
            else:
                to_print = "\n  ".join([str(pair) for pair in groundings])
                data.append(
                    "Bad grounding:\n{}\n --> [\n{}\n]".format(candidate, to_print))

    for datum in data:
        print("###\n{}\n###\n".format(datum))

    print(
        "{:.1f}% ({}/{}) gold in entry points\n{:.1f}% ({}/{}) gold in top 1\n"
        "{:.1f}% ({}/{}) gold in top {}\n{:.1f}% ({}/{}) gold in top {} but not"
        " in entry points".format(
            100*correct_in_entry_points/len(test_cases),
            correct_in_entry_points,
            len(test_cases),
            100*correct_in_top_1/len(test_cases),
            correct_in_top_1,
            len(test_cases),
            100 * correct_in_top_k / len(test_cases),
            correct_in_top_k,
            len(test_cases),
            cx_setup.min_groundings,
            100 * correct_in_top_k_but_not_entry_points / (
                    len(test_cases) - correct_in_entry_points),
            correct_in_top_k_but_not_entry_points,
            len(test_cases) - correct_in_entry_points,
            cx_setup.min_groundings
            ))


def _test_wm_dart_test_cases():

    wm_test_setup = WMTestSetupWithOMG()
    grounder = wm_test_setup.grounder
    ontology = wm_test_setup.ontology
    test_cases = [
        {"phrase": "Food insecurity expected to worsen",
         "entry_points": ["causal_factor"],
         "gold": "food_insecurity"
         },
        {"phrase": "harvesting of the 2016 first season crops",
         "entry_points": ["causal_factor"],
         "gold": "crop_production"
         },
        {"phrase": "crop production",
         "entry_points": ["causal_factor"],
         "gold": "crop_production"
         },
        {"phrase": "access fields",
         "entry_points": ["causal_factor"],
         "gold": "road_access"
         },
        {"phrase": "cereal prices almost doubling in Juba",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "prices of sorghum",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "supplies",
         "entry_points": ["causal_factor"],
         "gold": "supply"
         },
        {"phrase": "eased inflationary pressures",
         "entry_points": ["causal_factor"],
         "gold": "inflation"
         },
        {"phrase": "Food insecurity is deepening",
         "entry_points": ["causal_factor"],
         "gold": "food_insecurity"
         },
        {"phrase": "678,163 South Sudanese refugees",
         "entry_points": ["causal_factor"],
         "gold": "human_migration"
         },
        {"phrase": "come to a halt",
         "entry_points": ["causal_factor"],
         "gold": "causal_factor"
         },
        {"phrase": "air deliveries to provide life-saving food assistance",
         "entry_points": ["causal_factor"],
         "gold": "provide_food"
         },
        {"phrase": "enrolment in schools",
         "entry_points": ["causal_factor"],
         "gold": "education"
         },
        {"phrase": "developing acute malnutrition",
         "entry_points": ["causal_factor"],
         "gold": "famine"
         },
        {"phrase": "the communications services",
         "entry_points": ["causal_factor"],
         "gold": "basic_services"
         },
        {"phrase": "improve connectivity coverage",
         "entry_points": ["causal_factor"],
         "gold": "basic_services"
         },
        {"phrase": "easy access to new Digital Radios",
         "entry_points": ["causal_factor"],
         "gold": "access"
         },
        {"phrase": "the security situation allows",
         "entry_points": ["causal_factor"],
         "gold": "peacekeeping_and_security"
         },
        {"phrase": "government staff scheduled for early April",
         "entry_points": ["causal_factor"],
         "gold": "government"
         },
        {"phrase": "Staple food prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "influence livestock markets",
         "entry_points": ["causal_factor"],
         "gold": "market"
         },
        {"phrase": "Market anomalies remain",
         "entry_points": ["causal_factor"],
         "gold": "market"
         },
        {"phrase": "resulted in significant market improvements",
         "entry_points": ["causal_factor"],
         "gold": "market"
         },
        {"phrase": "declining",
         "entry_points": ["causal_factor"],
         "gold": "trend"
         },
        {"phrase": "ample market supply led to a marginal decrease",
         "entry_points": ["causal_factor"],
         "gold": "supply"
         },
        {"phrase": "Imported rice prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "regional wheat deficits",
         "entry_points": ["causal_factor"],
         "gold": "food_shortage"
         },
        {"phrase": "wheat prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "price trends in selected reference markets",
         "entry_points": ["causal_factor"],
         "gold": "price_or_cost"
         },
        {"phrase": "weather concerns",
         "entry_points": ["causal_factor"],
         "gold": "weather_issue"
         },
        {"phrase": "International wheat prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "weather conditions in competitor countries",
         "entry_points": ["causal_factor"],
         "gold": "weather"
         },
        {"phrase": "inflationary pressures on global rice prices",
         "entry_points": ["causal_factor"],
         "gold": "inflation"
         },
        {"phrase": "the first stocks contraction in six years",
         "entry_points": ["causal_factor"],
         "gold": "market"
         },
        {"phrase": "price policies",
         "entry_points": ["causal_factor"],
         "gold": "regulation"
         },
        {"phrase": "aggregate cereal production",
         "entry_points": ["causal_factor"],
         "gold": "crop_production"
         },
        {"phrase": "Regional market supplies",
         "entry_points": ["causal_factor"],
         "gold": "supply"
         },
        {"phrase": "elevated source market prices in Nigeria",
         "entry_points": ["causal_factor"],
         "gold": "price_or_cost"
         },
        {"phrase": "the insecurity stricken Greater Lake Chad basin",
         "entry_points": ["causal_factor"],
         "gold": "physical_insecurity"
         },
        {"phrase": "prices declined",
         "entry_points": ["causal_factor"],
         "gold": "price_or_cost"
         },
        {"phrase": "responses to the different atypical supply",
         "entry_points": ["causal_factor"],
         "gold": "supply"
         },
        {"phrase": "local cereal prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "This price trend",
         "entry_points": ["causal_factor"],
         "gold": "price_or_cost"
         },
        {"phrase": "follow their normal seasonal trends",
         "entry_points": ["causal_factor"],
         "gold": "trend"
         },
        {"phrase": "Staple food prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
        {"phrase": "the harvest",
         "entry_points": ["causal_factor"],
         "gold": "crop_production"
         },
        {"phrase": "resulting in low supply levels",
         "entry_points": ["causal_factor"],
         "gold": "supply"
         },
        {"phrase": "supply",
         "entry_points": ["causal_factor"],
         "gold": "supply"
         },
        {"phrase": "food aid",
         "entry_points": ["causal_factor"],
         "gold": "provide_food"
         },
        {"phrase": "Livestock prices",
         "entry_points": ["causal_factor"],
         "gold": "food_price"
         },
    ]

    # validate
    for item in test_cases:
        nodes = ontology.get_nodes_by_name(item['gold'])
        if len(nodes) == 0:
            raise IOError("Invalid test case: gold standard node {} does not "
                          "exist in ontology".format(item['gold']))

    data = []
    correct_in_top_1 = 0
    correct_in_top_k = 0
    for case in test_cases:
        candidate = MentionCandidate(case["phrase"], "DUMMY")
        candidate.add_structured_data(grounder.keywords)
        candidate.remove_stopwords_from_mention(grounder.stopwords)
        entry_points = case["entry_points"]
        gold_paths = {
            n.get_path() for n in ontology.get_nodes_by_name(case["gold"])
            if n is not None}

        groundings = grounder.ground_mention(
            candidate,
            entry_points,
            wm_test_setup.threshold,
            # blacklisted_paths=wm_test_setup.blacklist,
            modes=wm_test_setup.modes,
            verbose=1
        )
        grounded_paths = [path for path, _ in groundings]
        if len(grounded_paths) > 0:
            if grounded_paths[0] in gold_paths:
                correct_in_top_1 += 1
            if any(path in gold_paths for path in grounded_paths):
                correct_in_top_k += 1
            else:
                to_print = "\n  ".join(
                    ["["] + [str(pair) for pair in groundings] + ["]"])
                data.append(
                    "Bad grounding:\n{}\n --> {}".format(candidate, to_print))

    for datum in data:
        print("###\n{}\n###\n".format(datum))

    print("{:.1f}% ({}/{}) gold in top 1\n{:.1f}% ({}/{}) gold in top {}"
          .format(100*correct_in_top_1/len(test_cases),
                  correct_in_top_1,
                  len(test_cases),
                  100 * correct_in_top_k / len(test_cases),
                  correct_in_top_k,
                  len(test_cases),
                  grounder.MIN_GROUNDINGS_FROM_ENTRY_POINT
                  ))


def _test_wm_dart_sample_frequent():
    raise NotImplementedError


def _test_wm_dart_review_frequent():

    inputs = [
        "considerable longterm moisture deficits remain",
        "strengthening moisture deficits",
        "disrupt access to livelihood activities",
        "a result of good domestic supplies",
        "a drought-reduced output",
        "snow melt",
        "heavy rains",
        "support availability",
        "restricted access to services",
        "partners finally gained access",
        "Ruweng State has appealed to the Ministry of Health",
        "access",
        "facilitate access to immediate assistance",
        "increasing humanitarian access",
        "disrupted in Greater Upper Nile",
        "declined in most areas of Greater Upper Nile",
        "exacerbated by expectations of a sharply-reduced 2017 secondary yala crop",
        "concerns over crop conditions",
        "planted as an alternative to sorghum",
        "harvesting",
        "plant",
        "minimal crop production",
        "black bean production for export to Venezuela",
        "reduced national production",
        "driven by anticipated reduced domestic production",
        "the recently-completed second season harvest increased supplies",
        "food assistance",
        "inadequate food consumption",
        "promote resilience",
        "future trends in population growth",
        "Food insecurity",
        "food remained",
        "WFP shared examples of awareness",
        "food availability",
    ]
    wm_test_setup = WMTestSetupWithOMG()
    grounder = wm_test_setup.grounder

    print_data = []
    for input in inputs:

        candidate = MentionCandidate(
            input, "DUMMY"
        )
        candidate.add_structured_data(grounder.keywords)
        candidate.remove_stopwords_from_mention(grounder.stopwords)

        entry_points = []

        groundings = grounder.ground_mention(
            candidate,
            entry_points,
            wm_test_setup.threshold,
            blacklisted_paths=wm_test_setup.blacklist,
            modes=wm_test_setup.modes,
            verbose=1
        )

        # # all groundings:
        # grounding_print = "\n  ".join(
        #     ["["] + [str(pair) for pair in groundings] + ["]"])
        # 1-best
        grounding_print = str(groundings[0]) if len(groundings) > 0 else "( )"
        print_data.append("{}\n --> {}".format(candidate, grounding_print))

    for datum in print_data:
        print("###\n{}\n###\n".format(datum))


def _test_not_found():
    print("Test `{}` not recognized".format(sys.argv[1]))


if __name__ == "__main__":

    test_functions = {
        "cx": _test_cx_grounding,
        "cx_bert": _test_cx_bert_grounding,
        "cx_icm": _test_cx_icm_grounding,
        "cx_icm_bert": _test_cx_icm_bert_grounding,
        "cx_test": _test_cx_test_cases,
        "wm_review_frequent": _test_wm_dart_review_frequent,
        "wm_dart_test": _test_wm_dart_test_cases,
    }
    test_functions.get(sys.argv[-1], _test_not_found)()
    sys.exit(0)

