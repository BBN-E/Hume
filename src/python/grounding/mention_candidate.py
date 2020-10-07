
try:
    from . import utils
except ImportError:
    import utils


class MentionCandidate(object):

    def __init__(self, mention_string, sentence_string,
                 value=None,
                 unit=None):
        self._mention_string = mention_string
        self._original_mention_string = mention_string[:]
        self._sentence_string = sentence_string
        self._processes = []
        self._participants = []
        self._properties = []
        self._value = value
        self._unit = unit
        self._groundings = dict()
        self._mention_embedding = None
        self._processes_embedding = None
        self._properties_embedding = None
        self._participants_embedding = None
        self._contextual_embedding = None
        self._contextual_anchor_embeddings = []

    def __str__(self):
        return (
            "<MentionCandidate original_mention_string=`{}` filtered_mention_st"
            "ring=`{}` sentence=`{}` processes={} participants={} properties={}"
            ">".format(
                self._original_mention_string,
                self._mention_string,
                self._sentence_string,
                repr(self._processes),
                repr(self._participants),
                repr(self._properties)))

    def get_original_mention_string(self):
        return self._original_mention_string

    def get_mention_string_embedding(self):
        return self._mention_embedding

    def set_mention_string_embedding(self, vector):
        self._mention_embedding = vector

    def get_contextual_anchor_embeddings(self):
        return self._contextual_anchor_embeddings

    def add_contextual_anchor_embedding(self, vector):
        self._contextual_anchor_embeddings.append(vector)

    def get_contextual_embedding(self):
        return self._contextual_embedding

    def set_contextual_embedding(self, vector):
        self._contextual_embedding = vector

    def get_participants_embedding(self):
        return self._participants_embedding

    def set_participants_embedding(self, vector):
        self._participants_embedding = vector

    def get_properties_embedding(self):
        return self._properties_embedding

    def set_properties_embedding(self, vector):
        self._properties_embedding = vector

    def get_processes_embedding(self):
        return self._processes_embedding

    def set_processes_embedding(self, vector):
        self._processes_embedding = vector

    def remove_stopwords_from_mention(self, stop_set):
        filtered_tokens = utils.ontology_utils.get_filtered_tokens(
            self._mention_string, stopwords=stop_set)
        if len(filtered_tokens) > 0:
            self._mention_string = u" ".join(filtered_tokens)

    def add_structured_data(self, keyword_dict):
        for strucured_data_type in keyword_dict.keys():
            data_type_variable = '_{}'.format(strucured_data_type)
            if hasattr(self, data_type_variable):
                keywords = keyword_dict[strucured_data_type]
                matched_keywords = utils.ontology_utils.get_filtered_tokens(
                    self._mention_string, keywords=keywords)
                getattr(self, data_type_variable).extend(matched_keywords)

    def get_sentence(self):
        return self._sentence_string

    def get_processes(self):
        return self._processes

    def get_participants(self):
        return self._participants

    def get_properties(self):
        return self._properties

    def get_value(self):
        return self._value

    def get_unit(self):
        return self._unit

    def get_mention_string(self):
        return self._mention_string

    def update_groundings(self, groundings_dict):
        utils.merge_groundings(self._groundings, groundings_dict)

    def get_groundings(self):
        return self._groundings
