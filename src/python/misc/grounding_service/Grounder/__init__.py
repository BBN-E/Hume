
import io
import json
import os
import sys
import time

project_root = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)))))))
kb_root = os.path.join(project_root, 'src', 'python', 'knowledge_base')
ontology_root = os.path.join(kb_root, 'internal_ontology')
sys.path.insert(0, kb_root)
sys.path.insert(0, ontology_root)
from internal_ontology import Node
from internal_ontology import Ontology
from internal_ontology import OntologyMapper
sys.path.insert(0, os.path.join(project_root, 'src', 'python'))
from grounding import Grounder
from grounding import MentionCandidate
from grounding import utils



class ServiceGrounder(object):
    """SaaS wrapper for the grounding code"""

    def __init__(self, ontology_yaml, min_groundings, threshold, embeddings_file, internal_yaml, exemplars_file):
        self.model_loaded = False
        self.model = None  # type: Grounder
        self.mapper = None  # type: OntologyMapper
        self._min_groundings = min_groundings
        self._threshold = threshold
        self._embeddings_file = embeddings_file
        self._ontology_yaml = ontology_yaml
        self._internal_ontology_file = internal_yaml
        self._internal_exemplars = exemplars_file
        self._max_score = 0.9974

    def load_model(self, yaml_string=None):

        if yaml_string is None:  # default / starting ontology yaml
            with io.open(self._ontology_yaml,
                         'r', encoding='utf8') as yaml_file_handle:
                yaml_string = yaml_file_handle.read()

        if self.model_loaded:  # reuse the ontology's embeddings lookup
            ontology = self.model.get_ontology()
            last_time = time.time()
            print('Loading ontology from string...', end=' ')
            ontology.load_from_yaml_string_with_metadata(yaml_string)
            self.model.flush_cache()

        else:  # build from scratch
            ontology = Ontology()
            last_time = time.time()
            print('Loading embeddings...', end=' ')
            ontology.init_embeddings(self._embeddings_file)

            this_time = time.time()
            print('{}s\nLoading ontology from string...'
                  .format(this_time - last_time), end=' ')
            last_time = this_time
            ontology.load_from_yaml_string_with_metadata(yaml_string)

            # mapper to add internal exemplars when possible
            ontology_mapper = OntologyMapper()
            ontology_mapper.load_ontology(self._internal_ontology_file)
            self.mapper = ontology_mapper

        # exemplars = Ontology.load_internal_exemplars(self._internal_exemplars)
        # ontology.add_internal_exemplars(exemplars, self.mapper, "WM")

        this_time = time.time()
        print('{}s\nBuilding ontology embeddings...'
              .format(this_time - last_time), end=' ')
        ontology.add_embeddings_to_nodes()

        # load keywords
        keywords = utils.read_keywords_from_bbn_annotation(
            '{}/resource/ontologies/internal/hume/'
            'keywords-anchor_annotation.txt'.format(project_root))
        # load stopwords
        stopwords = utils.read_stopwords_from_hume_resources(
            "{}/resource/ontologies/internal/hume/stopwords.list"
            .format(project_root))

        self.model = Grounder(ontology, self._min_groundings)
        #self.model.specify_user_root_path(user_specified_root)
        self.model.build_grounder(keywords, stopwords)

        self.model_loaded = True

    def query_grounding(self, mentions, ontology):

        if ((not self.model_loaded)
                or (ontology != self.model.get_ontology().get_as_string())):
            self.load_model(ontology)

        last_time = time.time()

        entry_points = []
        external_grounding_decisions = []
        for mention in mentions:
            mention_str = mention['mention_str']
            sentence = mention.get('sentence', '')
            mention_candidate = MentionCandidate(
                mention_str,
                sentence)
            mc_created_time = time.time()
            mention_candidate.add_structured_data(self.model.get_keywords())
            mention_candidate.remove_stopwords_from_mention(self.model.get_stopwords())
            mc_structured_time = time.time()
            groundings = self.model.ground_mention(
                mention_candidate,
                entry_points,
                self._threshold)
            mc_grounded_time = time.time()
            for idx in range(len(groundings)):
                decision, score = groundings[idx]
                groundings[idx] = (decision, min(score, self._max_score))
            score_fixed_time = time.time()
            external_grounding_decisions.append(groundings)

            #external_grounding_decisions[-1].append(
            #    ("3 ground", mc_grounded_time - mc_structured_time,))
            last_time = time.time()

        return external_grounding_decisions


if __name__ == "__main__":

    external_ont_yaml = (  # not actually in version control
        '/home/criley/repos/Hume/resource/ontologies/open/'
        'hume_ontology_with_metadata.20191007.yaml'.format(project_root))
    internal_yaml = (
        '{}/resource/ontologies/internal/hume/event_ontology.yaml'
        .format(project_root))
    with open(external_ont_yaml, 'r', encoding='utf8') as f:
        yaml_string = f.read()
    embeddings_file = '/nfs/raid87/u10/shared/Hume/common/glove.6B.50d.p'
    if not os.path.isfile(embeddings_file):
        embeddings_file = '/home/hqiu/resource/glove.6B.50d.p'
    min_groundings = 5
    threshold = 0.75

    test_words = ["conflict", "conflict", "armed conflict", "fire", "fire"]

    service = ServiceGrounder(
        external_ont_yaml,
        min_groundings,
        threshold,
        embeddings_file,
        internal_yaml,
        "DUMMY:exemplars"
    )

    mentions = []
    for test_word in test_words:
        mentions.append({
            "mention_str": test_word,
            "sentence": "tmp_sentence"
        })
    print(mentions)
    ret = service.query_grounding(mentions, yaml_string)
    print(json.dumps(ret, indent=1))
    print("-----------------------")

