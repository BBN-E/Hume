# from __future__ import print_function
import sys, os, yaml, pprint
import io
import json
from ontology_class import OntologyClass
from collections import defaultdict
from rdflib import Graph, URIRef, RDFS, Literal
from elements.kb_event_mention import KBEventMention
from elements.structured.structured_events import Event as StructuredEvent
from elements.structured.structured_property import Property
from numpy import zeros, exp, ndarray
import re
from elements.structured.structured_entity import EntityData


class InternalOntology:
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))))
        import entity_linking.vector_utils as vecs
    except ImportError as err:
        raise err

    cache_delimiter = "|||"
    oov_token = "<UNK>"

    def __init__(self, yaml_file, examples_file=None, embeddings_file=None,
                 lemma_file=None, stopword_file=None,
                 apply_transformation_indicator_names=False):

        self.keywords = set()

        self.always_event_types = ['Quote',]
        #self.always_event_types = ['Generic', 'Quote', 'Event']

        self.apply_transformation_indicator_names = apply_transformation_indicator_names
        self.examples = self._read_examples(examples_file)

        # print "Loading ontology from: " + yaml_file
        i = io.open(yaml_file, encoding='utf8')
        ont_list = yaml.load(i)
        i.close()

        # Add type text / node ID to class name mapping
        self.type_text_to_class_name = dict()

        # Assume one root
        root_name = ont_list[0].keys()[0]
        self.root = OntologyClass(root_name,None)
        self.load_ontology_class(self.root, ont_list[0][root_name])
        self.rdf, self.class_finder = self._convert_to_ttl()

        if lemma_file is not None:
            self.lemma_map = self._read_lemma_file(lemma_file)
            """:type: dict[str, str] from word variant to lemma"""
        self.stopwords = {
            "make",
            "take",
            "makes",
            "takes",
            "made",
            "took",
            "get",
            "gets",
            "got",
            "see",
            "seen",
            "saw",
            "gotten",
            "taken",
            "call",
            "need",
            "called",
            "needed",
            "calls",
            "needs",

        }
        #if stopword_file is not None:
        #    self.stopwords = self._read_stopword(stopword_file)
        #    """:type: set[str]"""

        if embeddings_file is not None:
            self.embeddings = self.vecs.read_embeddings(embeddings_file)
            self.dimensions = len(self.embeddings.values()[0])
            self.decay = 0.25  # TODO adjust
            # attenuate type embeddings
            self.weight_for_type_embedding = 0.1

            self.get_concept_embeddings(self.root, [], [])
            # self.cache = {}

    ### ready
    def _read_examples(self, path):
        examples = defaultdict(list)
        if path is None:
            return examples

        with io.open(path, 'r', encoding='utf8') as f:
            examples_json = json.load(f)

        for node in examples_json:
            for exemplar in examples_json[node][u'exemplars']:
                example = exemplar[u'trigger'][u'text']
                if self.apply_transformation_indicator_names:
                    example = self.transform_indicator_label(example)

                examples[node].append(example)

                self.keywords.add(example)

            #print repr(node_id), node_id, 'EXEMPLARS:', examples[node_id]
        return examples

    ### ready
    def _read_lemma_file(self, path):
        ret = dict()
        with io.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                tokens = line.strip().split()
                if len(tokens) == 2:
                    ret[tokens[0]] = tokens[1]
        return ret

    ### ready
    def _read_stopword(self, path):
        ret = set()
        with io.open(path, 'r', encoding='utf-8') as f:
            for line in f:
                ret.add(line.strip())
        return ret

    ### ready
    def _convert_to_ttl(self):
        ontology_graph = Graph()
        pairs_seen = set([])
        class_finder = {}

        def go_down(graph, node, parent=None):

            uri = URIRef(node.class_name)

            if (parent is not None and
                    (parent.class_name, node.class_name) in pairs_seen):
                return

            if len(node.children) > 0:
                for child in node.children:
                    go_down(graph, child, node)

            if parent is not None:
                graph.add((uri,
                           RDFS.subClassOf,
                           URIRef(parent.class_name)))
                pairs_seen.add((parent.class_name, node.class_name))

            for source in node.sources:
                graph.add((uri,
                           URIRef("_source"),
                           Literal(source)))

            for example in node.examples:
                graph.add((uri,
                           URIRef("_examples"),
                           Literal(example)))

            for example in self.examples[node.class_name]:
                graph.add((uri,
                           URIRef("_exemplars"),
                           Literal(example)))

            graph.add((uri, URIRef("_description"), Literal(node.description)))

            class_finder[uri] = node
            # print "class_finder: " + str(uri) + " -> " + str(node)

        go_down(ontology_graph, self.root)
        return ontology_graph, class_finder

    ### ready
    def load_ontology_class(self, ont_class, lst):
        for dct in lst:
            for key, value in dct.iteritems():
                if key.startswith("_"):
                    if key == "_description":
                        ont_class.description = value
                    if key == "_examples":
                        ont_class.examples = value
                    if key == "_source":
                        ont_class.sources = value
                else:
                    # print "Adding new child to: " + ont_class.class_name
                    child = OntologyClass(key,ont_class)
                    self.load_ontology_class(child, value)
                    ont_class.children.append(child)

        #print repr(ont_class.id), ont_class.id, "SAVED EXEMPLARS", self.examples[ont_class.id]
        #ont_class.exemplars = self.examples[ont_class.id]

        ont_class.exemplars = self.examples[ont_class.class_name]
        # print ont_class.class_name, "SAVED EXEMPLARS", ont_class.exemplars

    def get_internal_class_of_structured_entity(self, entity_data):
        """
        :type entity_data: EntityData
        :return:
        """
        if entity_data.mar_entity_type:
            source_type = entity_data.mar_entity_type
        else:
            source_type = entity_data.entity_type
        if source_type == 'country':
            name = 'Country'
            # name = 'GeopoliticalEntity'  # IGOR change
        elif source_type == 'city':
            name = 'City'
            # name = 'GeopoliticalEntity'  # IGOR change
        elif source_type == 'location':
            name = 'GeopoliticalEntity'
        else:
            name = 'Actor'
        return self.class_finder.get(URIRef(name))

    def get_internal_class_of_event(self, event_mention):

        type_text = event_mention.event_type

        class_name = None
        if type_text in self.always_event_types:
            class_name = 'Event'
        elif type_text in self.type_text_to_class_name:
            class_name = self.type_text_to_class_name[type_text]
        else:
            print "ERROR: can't look up a class_name for event type: " + type_text

        concept = self.get_internal_class_from_type(class_name)

        return concept

    def get_internal_class_of_property(self, property_type):
        #property_type = property_type[property_type.rfind('#')+1:]
        if URIRef(property_type) in self.class_finder:
            return self.class_finder[URIRef(property_type)]

        print "WARNING: Could not link property mention with type: " + property_type + " to internal ontology"
        return None
        # """always goes to base of trunk, in case extracted type is off"""
        # return self.class_finder.get(URIRef('ReportedProperty'))

    # If you change the ground to external ontology algorithm
    # to depend on different aspects of the event_mention, you 
    # need to update get_cache_key(...)
    # This function is called in
    # external_ontology_cache_serializer.py and in
    # external_ontology_cache_grounder.py
    ### ready
    @classmethod
    def get_grounding_candidate(cls, kb_element):

        old_id_re = re.compile(r'\b(.+?)(_\d+)?\b')

        if isinstance(kb_element, Property):
            trunk = "ReportedProperty"
            concept = kb_element.property_type
            text = kb_element.property_label

        elif isinstance(kb_element, KBEventMention):
            trunk = "Event"
            concept = kb_element.event_type
            concept_match = old_id_re.match(concept)
            if concept_match:
                concept = concept_match.group(1)
            text = kb_element.trigger if kb_element.trigger is not None else ""

        elif isinstance(kb_element, StructuredEvent):
            trunk = "Event"
            concept = kb_element.event_type
            text = kb_element.event_label

        elif isinstance(kb_element, EntityData):
            trunk = "Actor"
            concept = kb_element.entity_type + kb_element.mar_entity_type
            text = kb_element.label

        else:
            raise NotImplementedError(
                "No cache key process has been prepared for data type "
                "{}".format(type(kb_element)))

        return [trunk, concept, text]

    @classmethod
    def get_cache_key(cls, grounding_candidate):
        return cls.cache_delimiter.join(grounding_candidate)

    def ground_event_mention_to_external_ontology_by_similarity(
            self, event_mention, ontology_flag, n_best, threshold=None):
        # has form: [trunk, concept, text]
        # e.g. ['Event', 'Conflict', 'the attack']

        grounding_candidate = self.get_grounding_candidate(event_mention)
        cache_key = self.get_cache_key(grounding_candidate)

        # Quote event type catch/hack
        grounded_types = []

        if event_mention.event_type in self.always_event_types:
            return self.grounding_event_mention_to_external_ontology_by_deterministic_mapping(
                event_mention, ontology_flag)
        else:
            grounded_types = self._ground_type(grounding_candidate, n_best, threshold)
            return cache_key, grounded_types

    ### ready
    def grounding_event_mention_to_external_ontology_by_deterministic_mapping(
            self, event_mention, ontology_flag):

        grounding_candiate = self.get_grounding_candidate(event_mention)
        cache_key = self.get_cache_key(grounding_candiate)

        type_text = event_mention.event_type
        print "type_text: " + type_text

        # Quote event type catch/hack
        if type_text in self.always_event_types:
            concept = self.root
        elif type_text in self.type_text_to_class_name:
            class_name = self.type_text_to_class_name[type_text]
            concept = self.get_internal_class_from_type(class_name)
        else:
            print "type not found in type_text_to_class_name: " + type_text
            return cache_key, []

        print "concept.class_name: " + str(concept.class_name)
        print "concept: " + str(concept)
        print "event_mention.confidence: " + str(event_mention.confidence)

        return cache_key, [(str(concept.class_name), event_mention.confidence)]

    def ground_structured_entity_to_external_ontology(
            self, entity_data, ontology_flag, n_best):
        cache_key = self.get_cache_key(entity_data)
        return self._ground_type(cache_key, ontology_flag, n_best)

    def ground_structured_property_to_external_ontology(
            self, structured_property, ontology_flag, n_best):
        cache_key = self.get_cache_key(structured_property)
        return self._ground_type(cache_key, ontology_flag, n_best)

    ### ready
    def _ground_type(self, grounding_candidate, n_best, threshold, is_event_to_indicator=False):

        class_name = grounding_candidate[1]
        text = grounding_candidate[2]

        # Only ground Generic events if their text has an exact exemplar match
        if class_name == "Event":
            if text not in self.keywords or text in self.stopwords:
                return None
            else:
                # TODO un-hardcode
                threshold = 0.85

        concept_ont_class = self.get_internal_class_from_type(class_name)

        # original class is not in the internal ontology!
        if concept_ont_class is None:
            return None

        concept_embeddings = concept_ont_class.type_embedding

        text_embeddings = self.embed_text(text)
        text_embeddings = self.vecs.average_vectors(text_embeddings)
        extraction_embedding = self.vecs.numpy.concatenate([
            concept_embeddings * self.weight_for_type_embedding,
            text_embeddings])

        grounded = {}
        print "concept_ont_class.class_name: " + str(concept_ont_class.class_name)
        uris_to_search = [self._text_to_uri(concept_ont_class.class_name)]
        print "uris_to_search: " + str(uris_to_search)
        while uris_to_search:
            uri = uris_to_search.pop(0)
            #print 'Comparing with internal type {}...'.format(uri),
            if uri in grounded:
                continue

            candidate = self.class_finder[uri]  # type: OntologyClass
            candidate_embedding = self.vecs.numpy.concatenate(
                [candidate.type_embedding * self.weight_for_type_embedding,
                 candidate.exemplars_embedding])

            similarity = self.vecs.get_vector_similarity(
                extraction_embedding,
                candidate_embedding,
                metric='cosine'
            )

            # check to see if any single exemplar better matches the text
            for exemplar in candidate.exemplars:
                exemplar_embedding = self.embed_text(exemplar)
                if len(exemplar_embedding) > 0:
                    exemplar_embedding = self.vecs.average_vectors(exemplar_embedding)
                else:
                    continue
                exemplar_only_similarity = self.vecs.get_vector_similarity(
                    exemplar_embedding,
                    text_embeddings,
                    metric='cosine')
                if exemplar_only_similarity >= similarity:
                    similarity = exemplar_only_similarity

            #print similarity
            if threshold is None or similarity >= threshold:

                ## TODO remove binning test:
                #if similarity <= threshold + 0.1:
                grounded[str(uri)] = similarity

            for child in self.rdf.subjects(RDFS.subClassOf, uri):
                #print 'checking child of {}: {}'.format(uri, child)
                uris_to_search.append(child)

        return sorted(grounded.items(), key=lambda x: x[1], reverse=True)[:n_best]

    @classmethod
    def get_external_source(
            cls, internal_class_name, ontology_flag, graph, backup_namespace):

        uri = URIRef(internal_class_name)

        for source in graph.objects(uri, URIRef('_source')):
            # TODO: create BBN-specific concepts in the event_ontology.yaml, so the source for serialization always exist
            if source.startswith(ontology_flag + ': '):
                return str(source).split(': ')[1]

        # grounded to a type that the external ontology doesn't know
        return u"{}#{}".format(backup_namespace, internal_class_name)


    ### ready
    def get_concept_embeddings(self,
                               ontology_class,
                               type_embeddings_above,
                               exemplar_embeddings_above):

        current_type = self.camel_to_tokens(ontology_class.class_name)
        current_type_embedding = self.embed_text(current_type)
        current_type_embedding = self.vecs.average_vectors(
            current_type_embedding)
        current_exemplars = ontology_class.exemplars[:]
        #current_exemplars.append(current_type)
        all_exemplars = u' '.join([unicode(e) for e in current_exemplars])
        current_exemplars_embedding = self.embed_text(all_exemplars)
        current_exemplars_embedding = self.vecs.average_vectors(
            current_exemplars_embedding)

        # current embeddings weighted at 100%
        this_type_data = [current_type_embedding, 1.0]
        this_exemplar_data = [current_exemplars_embedding, 1.0]
        # append to ancestors with decay
        type_embeddings = type_embeddings_above + [this_type_data]
        exemplar_embeddings = exemplar_embeddings_above + [this_exemplar_data]

        weights = [0.0] * len(type_embeddings)
        i = len(weights) - 1
        weight = 1.0
        while i >= 0:
            weights[i] = weight
            weight *= exp(-self.decay)
            i -= 1
        W = sum(weights)
        # include decay weights
        for i in range(len(weights)):
            # Take out normalization, so we don't underweigh leaf nodes that are at the end of a long path
            # @criley says: Consider adding normalization back in.  Decay is supposed to take care of this
            # weights[i] /= W  # normalize
            type_embeddings[i][1] = weights[i]  # update
            exemplar_embeddings[i][1] = weights[i]

        # apply decay weights
        current_type_embedding = [v * w for (v, w) in type_embeddings]
        ontology_class.type_embedding = self.vecs.average_vectors(
            current_type_embedding)
        try:
            current_exemplars_embedding = [v * w for (v, w) in
                                           exemplar_embeddings]
        except TypeError:
            raise TypeError("unable to weight exemplar embeddings",
                            repr(exemplar_embeddings), "for class",
                            ontology_class.class_name)
        ontology_class.exemplars_embedding = self.vecs.average_vectors(
            current_exemplars_embedding)

        for child in ontology_class.children:
            self.get_concept_embeddings(
                child, type_embeddings, exemplar_embeddings)

    @classmethod
    def _text_to_uri(cls, text):
        text = cls.camel_to_tokens(text)
        return URIRef(''.join([token.title() for token in text.split()]))

    ### ready
    def embed_text(self, text):
        """
        :rtype: [numpy.ndarray]
        """
        token_embeddings = []
        print text.encode('utf-8'),
        text = '' if not text else text
        tokens = [t.strip().lower() for t in text.split() if t]
        print 'prefilter', tokens,
        tokens = self.filter_words(tokens)
        print 'postfilter', tokens
        for word in tokens:
            if word not in self.embeddings and word in self.lemma_map:
                e = self.get_embedding_for_word(self.lemma_map[word])
            else:
                e = self.get_embedding_for_word(word)
            token_embeddings.append(e)

        # This will happen only if the entire text is filtered out.
        if len(token_embeddings) == 0:
            token_embeddings.append(self.get_embedding_for_word(self.oov_token))

        return token_embeddings

    def get_embedding_for_word(self, word):
        return self.embeddings[word.lower()]

    def filter_words(self, words):
        """For now, we are just filtering on stopwords."""
        ret = []
        print words, '->',
        for word in words:
            if word.lower() not in self.stopwords:
                ret.append(word)
        print ret,
        return ret
    
    def get_internal_class_from_type(self, event_type):
        """:type event_type: str
           :rtype: OntologyClass"""
        if event_type is None:
            return None
        else:
            return self.class_finder.get(URIRef(event_type))

    def call_uri_ref(self, uri):
        return URIRef(uri)

    @staticmethod
    def camel_to_tokens(string):
        old_id_re = re.compile(r'\b(.+?)(_\d+)?\b')
        old_id_match = old_id_re.match(string)
        if old_id_match:
            string = old_id_match.group(1)

        camel_case = re.compile(
            '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
        current = [m.group(0) for m in camel_case.finditer(string)]
        return u' '.join(current)

    @staticmethod
    def transform_indicator_label(label):
        stops = re.compile(r'\b(adjusted|gross|ages?|average|annualized|annual'
                           r'|mean|median|per capita|headcount|ratio|rate'
                           r'|(per \d+))\b')
        end = label.find('(')
        if end > 0:
            label = label[:end]
        end = label.find(',')
        if end > 0:
            label = label[:end]
        label = label.lower()
        label = stops.sub('', label)
        label = label.split('_')[-1]
        return label

