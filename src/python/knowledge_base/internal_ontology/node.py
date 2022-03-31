

from internal_ontology import utility
# except ImportError:
#     from knowledge_base.internal_ontology import utility


class Node(object):

    def __init__(self, name):
        self._name = name
        self._name_embeddings = None
        self._exemplar_embedding_lookup = {}
        self._average_exemplar_embedding = None
        self.path = None
        self._exemplars = []
        self._exemplar_weights = []
        self.children = []
        self.description = None
        self._participants = []
        self._participants_weights = []
        self._average_participants_embedding = None
        self._properties = []
        self._properties_weights = []
        self._average_properties_embedding = None
        self._processes = []
        self._processes_weights = []
        self._average_processes_embedding = None
        self._values = []
        self._values_weights = []
        self._average_values_embedding = None
        self._avg_contextual_embedding = None

    def get_participants(self):
            return self._participants

    def get_properties(self):
        return self._properties

    def get_processes(self):
        return self._processes

    def get_average_contextual_embedding(self):
        return self._avg_contextual_embedding

    def reset_descendant_exemplars(self):
        self._exemplars = self.get_exemplars_without_descendants()
        self._exemplar_weights = [1.0, ] * len(self._exemplars)
        self._average_exemplar_embedding = None

    def get_exemplars_without_descendants(self):
        original_exemplars = []
        for exemplar, weight in zip(self._exemplars, self._exemplar_weights):
            if weight == 1.0:
                original_exemplars.append(exemplar)
        return original_exemplars

    def set_average_contextual_embedding(self, vector):
        self._avg_contextual_embedding = vector

    def recursively_remove_stopwords(self, stop_set, embedding_lookup):
        new_exemplars = []
        new_exemplar_weights = []
        for i, ex in enumerate(self._exemplars):
            weight = self._exemplar_weights[i]
            new_ex_tokens = utility.get_filtered_tokens(ex, stopwords=stop_set)
            if len(new_ex_tokens) > 0:
                new_exemplars.append(u" ".join(new_ex_tokens))
                new_exemplar_weights.append(weight)
        self._exemplars = new_exemplars
        self._exemplar_weights = new_exemplar_weights
        self.embed_exemplars(embedding_lookup)
        # Leave name and structured data alone
        for child in self.children:
            child.recursively_remove_stopwords(stop_set, embedding_lookup)

    def get_exemplars(self):
        return self._exemplars

    def get_exemplars_with_weights(self):
        return list(zip(self._exemplars, self._exemplar_weights))

    def get_children(self):
        return self.children

    def add_child(self, node):
        self.children.append(node)

    def get_name(self):
        return self._name

    def get_name_embeddings(self):
        return self._name_embeddings

    def get_description(self):
        pass

    def set_description(self, string):
        self.description = string

    def update_parent_with_exemplars(self, parent_node, decay_factor=0.0):
        for i, exemplar in enumerate(self._exemplars):
            weight = self._exemplar_weights[i]
            weight_for_parent = weight * utility.decay(decay_factor)
            parent_node.add_exemplar(exemplar, weight_for_parent)

    def get_exemplar_to_embeddings(self):
        return self._exemplar_embedding_lookup

    def get_textual_mentions(self):  # real examples
        pass

    def get_path(self):
        return self.path

    def set_path_from_string(self, ancestor_string):
        self.path = '{}/{}'.format(ancestor_string, self.get_name())

    def set_path_from_parent(self, parent):
        self.path = '{}/{}'.format(parent.get_path(), self.get_name())

    def add_exemplar(self, exemplar_string, weight=1.0):
        self._exemplars.append(exemplar_string)
        self._exemplar_weights.append(weight)

    def embed_name(self, embedding_lookup):
        self._name_embeddings = utility.get_embeddings_for_mention_text(
            self._name,
            embedding_lookup,
            tokenization_modes=[
                utility.TokenizationMode.PUNCTUATION,
                utility.TokenizationMode.WHITESPACE])

    def embed_exemplars(self, embedding_lookup):
        if embedding_lookup is None:
            return
        all_exemplar_tokens = []
        all_exemplar_token_weights = []
        # update specific exemplar lookup (used with Max modes)
        for exemplar, weight in zip(self._exemplars, self._exemplar_weights):
            exemplar_embedding = utility.get_embeddings_for_mention_text(
                exemplar, embedding_lookup) * weight
            self._exemplar_embedding_lookup[exemplar] = exemplar_embedding

            exemplar_tokens = utility.get_filtered_tokens(exemplar)
            all_exemplar_tokens.extend(exemplar_tokens)
            all_exemplar_token_weights.extend([weight, ] * len(exemplar_tokens))

        # update centroid
        self._average_exemplar_embedding = utility.get_average_embeddings(
            all_exemplar_tokens,
            embedding_lookup,
            all_exemplar_token_weights)

    def embed_structured_data(self, embedding_lookup, keyword_dict):
        if embedding_lookup is None:
            return
        for strucured_data_type in keyword_dict.keys():
            data_type_variable = '_{}'.format(strucured_data_type)
            data_type_weight_variable = '_{}_weights'.format(strucured_data_type)
            if hasattr(self, data_type_variable):
                keywords = keyword_dict[strucured_data_type]

                # Add name to matches for this structured data type
                matched_name_keywords = utility.get_filtered_tokens(
                    self._name,
                    tokenization_modes=[
                        utility.TokenizationMode.PUNCTUATION,
                        utility.TokenizationMode.WHITESPACE],
                    keywords=keywords)
                getattr(self, data_type_variable).extend(matched_name_keywords)
                getattr(self, data_type_weight_variable).extend(
                    [1.0, ]*len(matched_name_keywords))

                # Add weighted exemplars to matches for this data type
                for i, exemplar in enumerate(self._exemplars):
                    matched_keywords = utility.get_filtered_tokens(
                        exemplar, keywords=keywords)
                    exemplar_weight = self._exemplar_weights[i]
                    getattr(self, data_type_variable).extend(matched_keywords)
                    getattr(self, data_type_weight_variable).extend(
                        [exemplar_weight, ]*len(matched_keywords))

                # get single (weighted average) vector for data type
                if len(getattr(self, data_type_variable)) > 0:
                    vector = utility.get_average_embeddings(
                        getattr(self, data_type_variable),
                        embedding_lookup,
                        getattr(self, data_type_weight_variable))
                    setattr(self, '_average_{}_embedding'.format(
                        strucured_data_type), vector)

    def get_average_exemplar_embeddings(self):
        return self._average_exemplar_embedding

    def get_average_participants_embedding(self):
        return self._average_participants_embedding

    def get_average_processes_embedding(self):
        return self._average_processes_embedding

    def get_average_properties_embedding(self):
        return self._average_properties_embedding

