from collections import defaultdict, OrderedDict
import yaml
import sys, os
import numpy as np
import re
import codecs
from rdflib import Graph, Literal, BNode, Namespace, RDF, RDFS, URIRef, XSD

from vector_utils import compute_average_vector, get_vector_similarity, read_embeddings, get_embedding_for_word, average_vector, is_zero_vector


class Ontology:

    def __init__(self, ontology_file_path, indicator_map_file, word_embeddings_file, lemma_file, stopword_file):
        self.ontology_file_path = ontology_file_path
        self.indicator_map_file = indicator_map_file
        self.word_embeddings_file = word_embeddings_file
        print "Reading the ontology file..."
        self.parent_to_children_nodes, self.all_leaf_nodes = self.__read_ontology()

        print('YS: type(self.parent_to_children_nodes)={}'.format(type(self.parent_to_children_nodes)))
        for parent in self.parent_to_children_nodes:
            print('YS: parent={}'.format(parent))
            for child in self.parent_to_children_nodes[parent]:
                print('YS:    child={}'.format(child))
        print('YS: type(self.all_leaf_nodes)={}'.format(type(self.all_leaf_nodes)))
        for leaf in self.all_leaf_nodes:
            print('YS: leaf={}'.format(leaf))

        self.lemma_map = self.__read_lemma_file(lemma_file)
        """:type: dict[str, str]
        from word variant to lemma
        """
        self.stopwords = self.__read_stopword(stopword_file)
        """:type: set[str]"""

        print "Reading indicator mappings..."
        self.indicator_dict = self.__read_indicator_map()
        print "Reading word embeddings..."
        self.word_embeddings = read_embeddings(self.word_embeddings_file)
        print "Calculating concept embeddings..."
        self.parent_to_children_embeddings = self.get_concept_embeddings()

    def __yamlify_ontology(self):
        """build class hierarchy in yaml from ttl.
        Adapted from the work of Josh Fasching"""

        def camel_case_split(identifier):
            matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
            return [m.group(0) for m in matches]

        def get_lines(name, offset, leaf):
            leaf_line = u' ' * (offset + 2) + u'- "' + name + u'"'
            if leaf:
                return [leaf_line]
            else:
                return [u' ' * offset + u'- ' + name + u':', leaf_line]

        def descend_class(g, ont_class, lines, offset=0):
            current = ont_class.rsplit(u'#', 1)[-1].rsplit(u'/', 1)[-1]
            current = u' '.join(camel_case_split(current)).lower()
            if (None, RDFS.subClassOf, ont_class) in g:
                lines.extend(get_lines(current, offset, False))
            else:
                lines.extend(get_lines(current, offset, True))
            for s_c in g.subjects(RDFS.subClassOf, ont_class):
                descend_class(g, s_c, lines, offset + 2)

        graph = Graph()
        graph.parse(self.ontology_file_path, format='turtle')
        event_path = os.path.join(os.path.split(self.ontology_file_path)[0],
                                  'Event.ttl')
        graph.parse(event_path, format='turtle')
        EVENT = Namespace("http://ontology.causeex.com/ontology/odps/Event#")

        yamlified_lines = []
        descend_class(graph, EVENT.Event, yamlified_lines)
        return u'\n'.join(yamlified_lines)

    def __read_lemma_file(self, filepath):
        ret = dict()
        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                tokens = line.strip().split()
                if len(tokens) == 2:
                    ret[tokens[0]] = tokens[1]
        return ret

    def __read_stopword(self, filepath):
        ret = set()
        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                ret.add(line.strip())
        return ret

    def __read_ontology(self):
        parent_to_children_nodes = defaultdict(list)
        all_leaf_nodes = []
        format = self.__ontology_format()
        if format == 'yaml':
            return self.__read_yaml(parent_to_children_nodes, all_leaf_nodes)
        elif format == 'ttl':
            return self.__read_ttl(parent_to_children_nodes, all_leaf_nodes)

    def __ontology_format(self):
        return self.ontology_file_path.rsplit('.')[-1].lower()

    def __read_yaml(self, parent_to_children_nodes, all_leaf_nodes):
        with open(self.ontology_file_path) as ontology_fp:
            yaml_ontology = yaml.safe_load(ontology_fp)
            self.__read_tree(yaml_ontology, parent_to_children_nodes, [], all_leaf_nodes)
        return parent_to_children_nodes, all_leaf_nodes

    def __read_ttl(self, parent_to_children_nodes, all_leaf_nodes):
        yamlified = self.__yamlify_ontology()
        yaml_ontology = yaml.safe_load(yamlified)
        self.__read_tree(yaml_ontology, parent_to_children_nodes, [], all_leaf_nodes)
        return parent_to_children_nodes, all_leaf_nodes

    def __read_indicator_map(self):
        indicator_dict = defaultdict(list)
        with open(self.indicator_map_file) as fp:
            for line in fp:
                line=line[:-1].strip()
                if not line or line.startswith("#"):
                    continue
                items = line.split("\t")
                terms = items[0].split(",")
                indicators = [x.strip() for x in items[1].split(",")]
                for term in terms:
                    term = term.strip().lower()
                    if term:
                        indicator_dict[term] = indicators
        return indicator_dict


    def __read_tree(self, node, parent_to_children_nodes, parents, all_leaf_nodes):
        child_list = []

        def add_to_result(label,is_leaf=False):
            path_to_self = "/"+label
            if parents:
                path_to_self = '/'+'/'.join(parents)+path_to_self
            # add as parent
            parent_to_children_nodes[path_to_self]=child_list
            # add as child
            child_list.append(path_to_self)
            if is_leaf:
                # this is a leaf node
                all_leaf_nodes.append(path_to_self)
            return

        if isinstance(node,str):  # leaf concept
            if node.startswith("wikidata") or node.startswith("_source") or node.startswith("_description") \
                or node.startswith("indicator"):
                return
            add_to_result(node,is_leaf=True)
            return child_list

        children = node if isinstance(node,list) else node.values()[0]
        self_added_as_parent = False
        node_label = None

        if isinstance(node,dict):
            if len(node.keys())>1:
                raise ValueError(str(node)+' is a dict with multiple keys')
            node_label = node.keys()[0]
            if node_label.startswith("wikidata") or node_label.startswith("_source") or \
                    node_label.startswith("_description") \
                    or node_label.startswith("indicator"):
                return
            # add_to_result(node_label)
            parents.append(node_label)
            self_added_as_parent = True

        for child in children:
            grand_children = self.__read_tree(child, parent_to_children_nodes, parents, all_leaf_nodes)
            if not grand_children:
                continue
            for gc in grand_children:
                child_list.append(gc)
        if self_added_as_parent:
            parents.pop()

        if node_label:
            add_to_result(node_label)
            return child_list

        return child_list

    def get_concept_embeddings(self):
        print('YS: in get_concept_embeddings')
        parent_to_children_embeddings = defaultdict(list)
        for parent in self.parent_to_children_nodes:
            print('YS: parent={}'.format(parent))
            children_embeddings = []
            for child in self.parent_to_children_nodes[parent]:
                print('YS:    child={}'.format(child))
                # print "\t"+child
                child_str = child.replace(parent,"").strip()
                if not child_str:
                    # this is the same as parent
                    child_str = parent
                print('YS:    child_str={}'.format(child_str))
                child_tokens = [t.strip() for t in child.split("/") if t]
                print('YS:    child_tokens = [{}]'.format(','.join(child_tokens)))

                child_weights = [0.0] * len(child_tokens)
                i = len(child_weights) - 1
                current_weight = 1.0
                while i >= 0:
                    child_weights[i] = current_weight
                    current_weight -= 0.2
                    i -= 1
                # now, normalize the child_weights
                W = 0
                for w in child_weights:
                    W += w
                for i in range(len(child_weights)):
                    child_weights[i] = child_weights[i] / W

                # some nodes in the ontology are represented by phrases, so we split on white space
                child_embedding = []
                for i, child_token in enumerate(child_tokens):
                    weight = child_weights[i]
                    my_tokens = [t for t in child_token.split(' ') if len(t.strip())>0]
                    if len(my_tokens) > 0:
                        e = compute_average_vector(my_tokens, self.word_embeddings)
                        if not is_zero_vector(e):
                            child_embedding.append((e, weight))

                #child_embedding = compute_average_vector(node_tokens, self.word_embeddings)
                children_embeddings.append((child, child_embedding))
                print('YS:    computed an average embeddings for child={}'.format(child))
            parent_to_children_embeddings[parent]=children_embeddings
        print('YS: exiting get_concept_embeddings')
        return parent_to_children_embeddings

    def print_ontology_dict(self,file_name):
        fp = open("/nfs/raid87/u15/users/msrivast/CauseEx/experiments/causeex_pipeline/"+file_name,"w")
        all_parents = sorted(self.parent_to_children_nodes.keys(), key = lambda x: len(x))
        for parent in all_parents:
            if parent.endswith("_source") or parent.endswith("_description"):
                continue
            if parent.startswith("/entity"):
                continue
            # parent = xpath.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/")
            fp.write(parent+"\n")
            sorted_children = sorted(self.parent_to_children_nodes[parent],key = lambda x: len(x))
            for xpath in sorted_children:
                # xpath = xpath.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/")
                fp.write("\t"+xpath+"\n")
        fp.close()
        return

    def filter_words(self, words):
        """For now, we are just filtering on stopwords."""
        ret = []
        for word in words:
            if word.lower() not in self.stopwords:
                ret.append(word)
        return ret

    def get_grounding(self, trigger, mapped_type):

        name_tokens = [t.strip().lower() for t in trigger.split() if t]
        name_tokens = self.filter_words(name_tokens)

        trigger_word_embeddings = []
        for word in name_tokens:
            e = get_embedding_for_word(word, self.word_embeddings)
            if e is not None:
                trigger_word_embeddings.append(e)
            elif e is None and word in self.lemma_map:
                lemma = self.lemma_map[word]
                e = get_embedding_for_word(lemma, self.word_embeddings)
                if e is not None:
                    trigger_word_embeddings.append(e)

        if "/factor" in mapped_type:
            mapped_type = "/event"

        if len(trigger_word_embeddings) == 0:
            children_embeddings = self.parent_to_children_embeddings[mapped_type]
            for (child, child_embedding) in children_embeddings:
                print('YS: len(trigger_word_embeddings)==0, child={}'.format(child))
            return  [OntologyNodeInfo('/event', False, 0.0)]

        name_embedding = average_vector(trigger_word_embeddings)
        #name_embedding = compute_average_vector(name_tokens,self.word_embeddings)

        children_embeddings = self.parent_to_children_embeddings[mapped_type]
        similarity_row = []
        for (child, child_embedding) in children_embeddings:
            score = 0
            for e, w in child_embedding:
                score += get_vector_similarity(name_embedding, e) * w
            #score = get_vector_similarity(name_embedding,child_embedding)
            similarity_row.append((child, score))
        similarity_row = sorted(similarity_row, key=lambda x: x[1], reverse=True)
        list_to_return = []
        for (c,s) in similarity_row:
            node_info = OntologyNodeInfo(c, c in self.all_leaf_nodes, s)
            list_to_return.append(node_info)

        return list_to_return


class OntologyNodeInfo:

    def __init__(self, path_to_node, is_leaf, similarity_score=None):
        if path_to_node.endswith("/"):
            path_to_node = path_to_node[:-1]
        self.path_to_node = path_to_node
        self.is_leaf = is_leaf
        self.similarity_score = similarity_score
        self.type = None

    def get_type(self):
        if not self.is_leaf:
            self.type = self.path_to_node
        else:
            parent_path = self.path_to_node
            parent_path = parent_path[1:]  # get rid of first "/"
            parts = parent_path.split("/")
            # if len(parts)<2:
            #     raise ValueError("No parent can be found for "+self.path_to_node)
            self.type = "/"+"/".join(parts[:-1])
        return self.type

    def get_indicators(self,indicator_map):
        parts = self.path_to_node.split("/")
        term_for_lookup = parts[-1]
        if not term_for_lookup in indicator_map:
            if len(parts)>=2:
                term_for_lookup = parts[-2]
            else:
                term_for_lookup = None
        if term_for_lookup and term_for_lookup in indicator_map:
            return indicator_map[term_for_lookup]
        return None

if __name__=='__main__':
    indicator_map_file = os.path.dirname(os.path.realpath(__file__)) \
                         + "/../config_files/wm/triggering_phrase_to_indicators.txt"
    ontology_file = os.path.dirname(os.path.realpath(__file__)) + "/../config_files/wm/hume_ontology.yaml"
    word_embeddings_file = "/nfs/raid87/u14/learnit_similarity_data/glove_6B_50d_embeddings/glove.6B.50d.p"
    ontology = Ontology(ontology_file,indicator_map_file,word_embeddings_file)

    ontology.print_ontology_dict("output_new.txt")
    # sys.exit(0)

    def run_test(event_trigger, mapped_type):
        print "Trigger: "+event_trigger+" type: "+mapped_type
        grounded_concepts = ontology.get_grounding(event_trigger, mapped_type) # should return sorted list

        type_for_node =  grounded_concepts[0].get_type()
        print "Type from ontology: "+type_for_node
        for ontology_node_info in grounded_concepts:
            print "Grounded concept: "+ontology_node_info.path_to_node
            print "Confidence: "+str(float(ontology_node_info.similarity_score))
            indicators = ontology_node_info.get_indicators(ontology.indicator_dict)
            one_best_indicator = None
            if indicators:
                one_best_indicator = indicators[0]
            print "Indicator: "+str(one_best_indicator)
            print ""

    event_trigger = "flood"
    mapped_type = "/event/weather"
    run_test(event_trigger,mapped_type)
    print ""
    event_trigger = "meet"
    mapped_type = "/event/personal/meet"
    run_test(event_trigger,mapped_type)
