
import sys

try:
    from . import utils
except ImportError:
    import utils


class Grounder(object):

    def __init__(self,
                 grounding_ontology,
                 MIN_GROUNDINGS_FROM_ENTRY_POINT):

        self.MIN_GROUNDINGS_FROM_ENTRY_POINT = MIN_GROUNDINGS_FROM_ENTRY_POINT
        self._ontology = grounding_ontology
        self._cache = dict()
        self.stopwords = set()
        self.keywords = dict()
        self._user_root_path = None

    def specify_user_root_path(self, path):
        if path is not None:
            # just ensures that the node exists
            self._ontology.get_node_by_path(path)
        self._user_root_path = path

    def get_user_root_path(self):
        return self._user_root_path

    def flush_cache(self):
        """Needed when ontology is updated."""
        self._cache = dict()

    def remove_stopwords(self):
        self._ontology.get_root().recursively_remove_stopwords(
            self.stopwords, self._ontology.embeddings)

    def get_ontology(self):
        return self._ontology

    def get_k(self):
        return self.MIN_GROUNDINGS_FROM_ENTRY_POINT

    def set_k(self, k):
        self.MIN_GROUNDINGS_FROM_ENTRY_POINT = k

    def update_stopwords(self, stopword_set):
        self.stopwords.update(stopword_set)

    def update_keywords(self, keyword_dict):
        self.keywords.update(keyword_dict)

    def get_keywords(self):
        return self.keywords

    def get_stopwords(self):
        return self.stopwords

    def get_from_cache(self, mention_candidate, entry_point_strings):
        sorted_strings = tuple(sorted(entry_point_strings))
        return self._cache.get((mention_candidate.get_mention_string(),
                                mention_candidate.get_sentence(),
                                sorted_strings), [])

    def update_cache(self, mention_candidate, entry_point_strings, groundings):
        sorted_strings = tuple(sorted(entry_point_strings))
        self._cache[(mention_candidate.get_mention_string(),
                     mention_candidate.get_sentence(),
                     sorted_strings)] = groundings

    def add_structured_data_to_ontology(self):

        def _recur(node):
            node.embed_structured_data(self._ontology.embeddings, self.keywords)
            for child in node.get_children():
                _recur(child)

        root = self._ontology.get_root()
        _recur(root)

    def ground_mention(self,
                       mention_candidate,
                       entry_point_names,
                       threshold,
                       blacklisted_paths=None,
                       modes=None,
                       force_entry_points=False,
                       remove_groundings_with_small_score=False,
                       verbose=0):

        # a collection of paths that are blacklisted (when not in entry points)
        if blacklisted_paths is None:
            blacklisted_paths = set()

        if verbose > 0:
            print("### grounding top {} above threshold {} ###\n{}\n"
                  "Entry points: {}"
                  .format(self.MIN_GROUNDINGS_FROM_ENTRY_POINT,
                          threshold,
                          mention_candidate,
                          entry_point_names))

        groundings = self.get_from_cache(mention_candidate, entry_point_names)
        if len(groundings) > 0:
            if verbose > 0:
                print("Retrieved cached groundings\n{}".format(groundings))
            return groundings

        regular_entry_points = []
        blacklisted_entry_points = []
        for entry_name in entry_point_names:
            nodes = self._ontology.get_nodes_by_name(entry_name)
            for node in nodes:
                if node.get_path() in blacklisted_paths:
                    blacklisted_entry_points.append(node)
                else:
                    regular_entry_points.append(node)
        root = self._ontology.get_root()

        automatically_rooted = False
        if len(entry_point_names) == 0:
            if verbose > 0:
                print("+ adding root to entry points")
            regular_entry_points.append(root)
            automatically_rooted = True

        # search starting from entry point, add things > threshold
        groundings_dict = {}
        for entry_point in regular_entry_points:
            self._compare_mention_with_node_recursively(
                mention_candidate,
                entry_point,
                threshold,
                groundings_dict,
                modes=modes,
                verbose=verbose
            )
        mention_candidate.update_groundings(groundings_dict)

        # none found and not blacklisted: start again from root
        if (
                len(mention_candidate.get_groundings()) == 0
                and len(blacklisted_entry_points) == 0
                and root not in regular_entry_points + blacklisted_entry_points
        ):
            if verbose > 0:
                print(
                    "===\n{} found at original entry points {}; regrounding "
                    "from root".format(
                        len(mention_candidate.get_groundings()),
                        [ep.get_path() for ep in
                         regular_entry_points]))

            groundings_dict = dict()
            self._compare_mention_with_node_recursively(
                mention_candidate,
                root,
                threshold,
                groundings_dict,
                initial_mode_weight=1.0,
                modes=modes,
                verbose=verbose
            )
            mention_candidate.update_groundings(groundings_dict)
        grounding_decisions = mention_candidate.get_groundings()

        # filter out items outside of our target subtree
        if self._user_root_path is not None:
            filtered_groundings = {}
            for grounding_string, (score, mode) in grounding_decisions.items():
                node = self._ontology.get_node_by_path(grounding_string)
                if node.get_path().startswith(self._user_root_path):
                    filtered_groundings[grounding_string] = (score, mode)
            if verbose > 0:
                print("Filtering out groundings from outside the user-specified"
                      " target subtree {}:\nBefore: {}\nAfter:{}"
                      .format(self._user_root_path,
                              grounding_decisions,
                              filtered_groundings))

            # while we are here, prefer deeper groundings when available:
            if len(filtered_groundings) > 1:
                filtered_groundings.pop(self._user_root_path, None)

            grounding_decisions = filtered_groundings

        # sort all groundings
        sorted_groundings = sorted(grounding_decisions.items(),
                                   key=lambda x: (x[1][0], x[0]),
                                   reverse=True)

        # get top k groundings without blacklisted groundings
        top_k_groundings = []
        for grounding_and_similarity_with_mode in sorted_groundings:
            grounding = grounding_and_similarity_with_mode[0]
            similarity = grounding_and_similarity_with_mode[1][0]
            if grounding in blacklisted_paths:
                if verbose > 0:
                    print("Grounding {} with score {} has been blacklisted"
                          .format(grounding, similarity))
                continue
            elif similarity >= threshold:
                top_k_groundings.append((grounding, similarity))

        # blacklist regular entry points, if requested
        if force_entry_points and not automatically_rooted:
            blacklisted_entry_points += regular_entry_points

        # add blacklisted groundings
        self._add_blacklisted_items_to_sorted_groundings(
            top_k_groundings,
            blacklisted_entry_points,
            mention_candidate,
            threshold,
            modes,
            verbose)

        top_k_groundings = (
            top_k_groundings[:self.MIN_GROUNDINGS_FROM_ENTRY_POINT])

        # fix Py2/3 floating point issue
        for i in range(len(top_k_groundings)):
            if top_k_groundings[i][1] > 1:
                top_k_groundings[i] = (top_k_groundings[i][0], 1.0)

        # discard groundings with 0 similarity
        if remove_groundings_with_small_score:
            filtered_groundings = []
            for concept, score in top_k_groundings:
                if score >= 0.00001:
                    filtered_groundings.append((concept, score))
            top_k_groundings = filtered_groundings

        self.update_cache(
            mention_candidate, entry_point_names, top_k_groundings)
        return top_k_groundings

    def _add_blacklisted_items_to_sorted_groundings(
            self,
            groundings,
            blacklisted_nodes,
            candidate,
            threshold,
            modes=None,
            verbose=0):
        blacklisted_map = {}
        for node in blacklisted_nodes:
            self._compare_mention_with_node(
                candidate,
                node,
                threshold,
                blacklisted_map,
                modes=modes,
                verbose=verbose)
        for grounding, (score, mode) in blacklisted_map.items():
            if verbose > 0:
                print("Blacklisted grounding {} with score {} is in entry point"
                      "s: forcing it into output".format(grounding, score))
            groundings.insert(0, (grounding, score))

    def get_top_k_from_dict(self, groundings_dict):
        return sorted(groundings_dict.items(),
                      key=lambda x: (x[1], x[0]),
                      reverse=True)[:self.MIN_GROUNDINGS_FROM_ENTRY_POINT]

    def get_top_k_from_ep_and_grounded_dicts(
            self, entry_points_dict, groundings_dict):
        """
        keep all types in ep dict, with max score from either dict, with at most
        self.MIN_GROUNDINGS_FROM_ENTRY_POINT keys, as a list.
        """
        groundings_dict = {k: v for k, v in groundings_dict.items()}
        merged = {}
        for concept, score in sorted(
                entry_points_dict.items(), key=lambda x: x[1], reverse=True
        )[:self.MIN_GROUNDINGS_FROM_ENTRY_POINT]:

            merged[concept] = score
            if concept in groundings_dict:
                grounded_score = groundings_dict.pop(concept)
                if grounded_score > score:
                    merged[concept] = grounded_score

        for concept, score in sorted(groundings_dict.items(),
                                     key=lambda x: x[1], reverse=True):
            if len(merged) >= self.MIN_GROUNDINGS_FROM_ENTRY_POINT:
                break
            merged[concept] = score

        return sorted(merged.items(),
                      key=lambda x: (x[1], x[0]),
                      reverse=True)[:self.MIN_GROUNDINGS_FROM_ENTRY_POINT]

    def _compare_mention_with_node(
            self,
            mention_candidate,
            node,
            threshold,
            groundings,
            modes=None,
            initial_mode_weight=1.0,
            verbose=0):

        if modes is None:
            modes = [
                utils.SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXAMPLES_AVG_USING_BERT,
                utils.SimilarityMode.COMPARE_MENTION_KEYWORDS_TO_EXEMPLARS_AVG,
                utils.SimilarityMode.COMPARE_MENTION_STRING_TO_EXEMPLARS_AVG,
                utils.SimilarityMode.COMPARE_MENTION_STRING_TO_TYPE_NAME,
            ]

        # true backoff approach to ground this node
        groundings_key = Grounder.get_grounding_key(node)
        mode_weight = initial_mode_weight
        for mode in modes:
            similarity = utils.get_similarity(
                mention_candidate, node, mode, self._ontology.embeddings)
            similarity *= mode_weight

            if verbose > 0:
                print(
                    "Ontology node: {}\nExemplars:{}\nProcesses:{}\nParticipant"
                    "s:{}\nProperties:{}\nGrounding mode: {}\nSimilarity: {}"
                    "\nMode weight: {}"
                    .format(node.get_path(),
                            node.get_exemplars_with_weights(),
                            node.get_processes(),
                            node.get_participants(),
                            node.get_properties(),
                            mode.name,
                            similarity,
                            mode_weight))

            if groundings_key in groundings:
                if similarity > groundings[groundings_key][0]:
                    if verbose > 0:
                        print("Updating previous score {}"
                              .format(groundings[groundings_key][0]))
                    groundings[groundings_key] = (similarity, mode)
            else:
                groundings[groundings_key] = (similarity, mode)

            # use threshold only to determine backoff strategy
            if similarity > threshold:
                break
            if verbose > 0:
                print("-- No grounding with this mode.  Backing off..."
                      .format(mode.name))

            mode_weight *= 0.9

    def _compare_mention_with_node_recursively(
            self,
            mention_candidate,
            node,
            threshold,
            groundings,
            modes=None,
            initial_mode_weight=1.0,
            verbose=0):

        # recur
        for child in node.get_children():
            self._compare_mention_with_node_recursively(
                mention_candidate,
                child,
                threshold,
                groundings,
                initial_mode_weight=initial_mode_weight,
                modes=modes,
                verbose=verbose)

        # run on current node
        self._compare_mention_with_node(
            mention_candidate,
            node,
            threshold,
            groundings,
            initial_mode_weight=initial_mode_weight,
            modes=modes,
            verbose=verbose)

    @staticmethod
    def get_grounding_key(node):
        return node.get_path()

    def build_grounder(self, keywords, stopwords):
        self.update_keywords(keywords)
        self.update_stopwords(stopwords)
        self.add_structured_data_to_ontology()
        self.remove_stopwords()
        self.remove_stopwords()
