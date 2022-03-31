from collections import defaultdict

import io
import json
import yaml
import logging

try:
    from internal_ontology import utility
    from internal_ontology import Node
except ImportError:
    from knowledge_base.internal_ontology import utility
    from knowledge_base.internal_ontology import Node

logger = logging.getLogger(__name__)
class Ontology(object):

    # TODO do we want to handle multiple inheritance?

    def __init__(self):
        self.root = None
        self.embeddings = None
        self._as_string = None
        self._exemplar_decay = 0.5

    def get_as_string(self):
        return self._as_string

    def get_root(self):
        return self.root

    def get_nodes_by_name(self, name):

        def _recur_on_node(node, name, found_so_far):
            if node.get_name() == name:
                found_so_far.append(node)
            for child in node.get_children():
                _recur_on_node(child, name, found_so_far)
            return found_so_far

        return _recur_on_node(self.root, name, [])

    def get_paths_by_name(self):
        paths = []
        raise NotImplementedError

    def get_node_by_path(self, path):

        def _recur_on_node(node):
            if path == node.get_path():
                return node
            for child in node.get_children():
                ret = _recur_on_node(child)
                if ret is not None:
                    return ret

        try:
            assert path.startswith(self.root.get_path())

        except AssertionError:
            print(path, 'does not start with', self.root.get_path())
        assert path.startswith(self.root.get_path())
        return _recur_on_node(self.root)

    @staticmethod
    def load_internal_exemplars(exemplars_json):
        exemplars = defaultdict(list)
        with io.open(exemplars_json, 'r', encoding='utf8') as f:
            all_examples_dict = json.load(f)
        for node_name, node_dict in all_examples_dict.items():
            for exemplar_dict in node_dict[u'exemplars']:
                exemplars[node_name].append(exemplar_dict[u'trigger'][u'text'])
        return exemplars

    def load_from_internal_yaml(self, yaml_path, ontology_map=None):

        def _load_node(current_node, child_dicts):
            for child_dict in child_dicts:
                for key, value in child_dict.items():
                    if key.startswith('_'):
                        if key == "_description":
                            current_node.set_description(value)
                        if key == "_examples":
                            for exemplar in value:
                                if exemplar != 'NA':
                                    pass  # This is a different object.
                                    # current_node.add_exemplar(exemplar)
                        if key == "_source" and ontology_map is not None:
                            ontology_map[current_node.get_name()] = value
                    else:
                        new_node = Node(key)
                        new_node.set_path_from_parent(current_node)
                        _load_node(new_node, value)
                        current_node.add_child(new_node)
            for child in current_node.get_children():
                child.update_parent_with_exemplars(current_node, self._exemplar_decay)

        with io.open(yaml_path, encoding='utf8') as y:
            ontology_list = yaml.safe_load(y)
        root_name = list(ontology_list[0].keys())[0]
        self.root = Node(root_name)
        self.root.set_path_from_string('')
        _load_node(self.root, ontology_list[0][root_name])

    @staticmethod
    def _get_yaml_from_string(yaml_str):
        with io.StringIO(yaml_str) as string_handle:
            return yaml.safe_load(string_handle)

    @staticmethod
    def _get_yaml_from_file(yaml_path):
        with io.open(yaml_path, 'r', encoding='utf8') as file_handle:
            return yaml.safe_load(file_handle)

    def add_internal_exemplars_from_json(self, exemplars_json, mapper, flag):
        exemplars = self.load_internal_exemplars(exemplars_json)
        self.add_internal_exemplars(exemplars, mapper, flag)

    def add_internal_exemplars(self, exemplars, mapper, flag):
        for name, exemplars in exemplars.items():
            if mapper is None or flag is None:
                nodes = self.get_nodes_by_name(name)
            else:
                external_paths = mapper.look_up_external_types(name, flag)
                nodes = [self.get_node_by_path(path) for path in external_paths]
                # if None, specified node name is not in this ontology!
                nodes = [n for n in nodes if n is not None]

            for node in nodes:
                for exemplar in exemplars:
                    node.add_exemplar(exemplar)

        # reset and update descendant exemplars (so they don't get duplicated)
        def _recur(parent_node):
            parent_node.reset_descendant_exemplars()
            for child in parent_node.get_children():
                _recur(child)
                child.update_parent_with_exemplars(parent_node, self._exemplar_decay)

        _recur(self.root)

    def load_from_yaml_string_with_metadata(self, yaml_string):

        def _load_node(current_node, child_dicts):
            for child_dict in child_dicts:
                if 'OntologyNode' in child_dict.keys():  # Leaf
                    leaf_name = utility.strip_comments(child_dict['name'])
                    leaf_node = Node(leaf_name)
                    leaf_node.set_path_from_parent(current_node)
                    exemplars = child_dict.get('examples', [])
                    for exemplar in exemplars:
                        leaf_node.add_exemplar(utility.strip_comments(exemplar))
                    current_node.add_child(leaf_node)
                else:
                    for key, value in child_dict.items():
                        new_node = Node(utility.strip_comments(key))
                        new_node.set_path_from_parent(current_node)
                        _load_node(new_node, value)
                        current_node.add_child(new_node)

            for child in current_node.get_children():
                child.update_parent_with_exemplars(current_node, self._exemplar_decay)

        ontology_list = self._get_yaml_from_string(yaml_string)
        root_name = list(ontology_list[0].keys())[0]
        self.root = Node(utility.strip_comments(root_name))
        self.root.set_path_from_string('')
        _load_node(self.root, ontology_list[0][root_name])
        self._as_string = yaml_string

    def load_from_yaml_with_metadata(self, yaml_path):
        raise RuntimeError("This is deprecated!!!")

        def _load_node(current_node, child_dicts):
            for child_dict in child_dicts:
                if 'OntologyNode' in child_dict.keys():  # Leaf
                    leaf_name = utility.strip_comments(child_dict['name'])
                    leaf_node = Node(leaf_name)
                    leaf_node.set_path_from_parent(current_node)
                    exemplars = child_dict.get('examples', [])
                    for exemplar in exemplars:
                        if isinstance(exemplar, str):
                            leaf_node.add_exemplar(utility.strip_comments(exemplar))
                        else:
                            print("WARNING: data corruption at file {} node {}".format(yaml_path, leaf_name))
                    current_node.add_child(leaf_node)
                else:
                    for key, value in child_dict.items():
                        new_node = Node(utility.strip_comments(key))
                        new_node.set_path_from_parent(current_node)
                        _load_node(new_node, value)
                        current_node.add_child(new_node)

            for child in current_node.get_children():
                child.update_parent_with_exemplars(current_node, self._exemplar_decay)

        ontology_list = self._get_yaml_from_file(yaml_path)

        root_name = list(ontology_list[0].keys())[0]
        self.root = Node(utility.strip_comments(root_name))
        self.root.set_path_from_string('')
        _load_node(self.root, ontology_list[0][root_name])

    def load_from_yaml_with_metadata_new(self, yaml_path):
        logger.info("Reading external ontology {}".format(yaml_path))
        def build_ontology_tree(yaml_root, parent_node, current_stack, external_ontology_path_to_node):
            if isinstance(yaml_root, dict):
                assert len(yaml_root.keys()) == 1 and list(yaml_root.keys())[0] == "node"
                real_root = yaml_root["node"]
                current_path = "{}/{}".format(current_stack, real_root['name'])
                if current_path not in external_ontology_path_to_node:
                    leaf_name = utility.strip_comments(real_root['name'])
                    leaf_node = Node(leaf_name)
                    external_ontology_path_to_node[current_path] = leaf_node
                    if parent_node:
                        leaf_node.set_path_from_parent(parent_node)
                    else:
                        leaf_node.set_path_from_string('')
                leaf_node = external_ontology_path_to_node[current_path]
                exemplars = real_root.get('examples', [])
                for exemplar in exemplars or ():
                    if isinstance(exemplar, str):
                        leaf_node.add_exemplar(utility.strip_comments(exemplar))
                    else:
                        print("WARNING: data corruption at file {} node {}".format(yaml_path, real_root['name']))
                if parent_node:
                    parent_node.add_child(leaf_node)
                for child in real_root.get("children", ()) or ():
                    build_ontology_tree(child, leaf_node, current_path, external_ontology_path_to_node)
                for child in leaf_node.get_children():
                    child.update_parent_with_exemplars(leaf_node, self._exemplar_decay)
            else:
                raise NotImplementedError()

        ontology_yaml_root = self._get_yaml_from_file(yaml_path)
        ontology_yaml_root = ontology_yaml_root[0]
        root_node_name = ontology_yaml_root["node"]["name"]
        external_ontology_path_to_node = dict()
        build_ontology_tree(ontology_yaml_root, None, "", external_ontology_path_to_node)
        self.root = external_ontology_path_to_node["/{}".format(root_node_name)]
        logger.info("Finish reading external ontology")

    def load_from_yaml_plain(self, yaml_path):

        def _load_node(current_node, children):

            for child in children:
                if type(child) is dict:
                    for k, v in child.items():
                        node_name = utility.strip_comments(k)
                        new_node = Node(node_name)
                        new_node.set_path_from_parent(current_node)
                        current_node.add_child(new_node)
                        _load_node(new_node, v)
                else:
                    leaf_name = utility.strip_comments(child)
                    leaf_node = Node(leaf_name)
                    leaf_node.set_path_from_parent(current_node)
                    current_node.add_child(leaf_node)

        ontology_list = self._get_yaml_from_file(yaml_path)

        root_name = list(ontology_list[0].keys())[0]
        self.root = Node(utility.strip_comments(root_name))
        self.root.set_path_from_string('')
        _load_node(self.root, ontology_list[0][root_name])

    def add_embeddings_to_nodes(self, node=None):
        if node is None:
            node = self.get_root()
        logger.info("Adding embeddings to node {}".format(node.get_name()))
        node.embed_name(self.embeddings)
        node.embed_exemplars(self.embeddings)
        for child in node.get_children():
            self.add_embeddings_to_nodes(child)

    def init_embeddings(self, embeddings_file):
        self.embeddings = utility.get_embedding_lookup(embeddings_file)
        self.add_embeddings_to_nodes()

    def add_node_contextual_embeddings_with_mapper(
            self, name_to_contextual_embedding, ontology_mapper, flag):
        for internal_name, centroid in name_to_contextual_embedding.items():
            centroid = utility.as_numpy_array(centroid)
            paths = ontology_mapper.look_up_external_types(internal_name, flag)
            for path in paths:
                node = self.get_node_by_path(path)
                node.set_average_contextual_embedding(centroid)

    def add_node_contextual_embeddings_with_name(
            self, name_to_contextual_embedding):
        for internal_name, centroid in name_to_contextual_embedding.items():
            centroid = utility.as_numpy_array(centroid)
            nodes = self.get_nodes_by_name(internal_name)
            for node in nodes:
                node.set_average_contextual_embedding(centroid)


class OntologyMapper(object):
    """For going from node type to source"""

    def __init__(self):
        self.mapping = dict()
        self._root = None
        self._has_dicts_in_mapping = False

    def get_root_name(self):
        return self._root

    def _dictify(self):
        for k, v in self.mapping.items():
            d = dict()
            for source_string in v:
                source_data = source_string.split(': ')
                flag = source_data[0]
                if len(source_data) == 1:
                    source = True
                else:
                    source = source_data[1]
                d.setdefault(flag, []).append(source)
            self.mapping[k] = d
        self._has_dicts_in_mapping = True

    def load_ontology(self, yaml_file):
        """Loads a BBN event_ontology.yaml file"""
        internal_ontology = Ontology()
        internal_ontology.load_from_internal_yaml(yaml_file, ontology_map=self.mapping)
        self._root = internal_ontology.get_root().get_name()
        self._dictify()

    def correct_external_mapping(self, external_ontology, source_flag_care, root_paths):
        """
        Because external ontology can change significantly, we need to remove non-groundable endpoints
        :param external_ontology:
        :param source_flag:
        :return:
        """
        logger.info("Correcting internal->external mappings")
        def dfs_visit_external_ontology(root, path_set):
            path_set.add(root.path)
            for child in root.children:
                dfs_visit_external_ontology(child, path_set)

        path_set = set()
        dfs_visit_external_ontology(external_ontology.root, path_set)
        def find_closest_groundable_endpoint(current_path,path_set):
            while len(current_path) > 1:
                if current_path in path_set:
                    return current_path
                current_path = "/".join(current_path.split("/")[:-1])
            return None
        resolved_mapping = dict()
        for internal_type_string, d in self.mapping.items():
            resolve_en = resolved_mapping.setdefault(internal_type_string, dict())
            for source_flag, l in d.items():
                if source_flag != source_flag_care:
                    resolve_en[source_flag] = l
                else:
                    resolved = []
                    for current_end in l:
                        t = find_closest_groundable_endpoint(current_end, path_set)
                        if t != None:
                            resolved.append(t)
                            if t != current_end:
                                logger.warning("{} is not groundable. Changed it to {}".format(current_end, t))
                        else:
                            logger.warning("{} is not groundable. Change it to root_paths {}".format(current_end, root_paths))
                            resolved.extend(root_paths)
                    resolve_en[source_flag] = list(set(resolved))
        self.mapping = resolved_mapping
        logger.info("Finished correcting internal->external mappings")

    def load_name_to_path_map(self, ontology):

        def _recur(node):
            name = node.get_name()
            path = node.get_path()
            self.mapping.setdefault(name, []).append("SELF: {}".format(path))
            for child in node.get_children():
                _recur(child)

        root = ontology.get_root()
        _recur(root)
        self._root = root.get_name()
        self._dictify()

    def look_up_external_types(self, internal_type_string, source_flag):
        return self.mapping.get(internal_type_string, {}).get(source_flag, [])

    def look_up_internal_types_mapped_to_source(self, source, source_flag):
        ret = []
        for key, values in self.mapping.items():
            if source in values.get(source_flag, []):
                ret.append(key)
        return ret

    def map_internal_paths_to_k_sources(self, paths_and_scores, grounder, flag):
        new_grounded_classes = []
        seen_sources = set()
        for i in range(len(paths_and_scores)):
            grounded_external_sources = []
            grounded_internal_path = paths_and_scores[i][0]
            score = paths_and_scores[i][1]
            while (len(grounded_external_sources) == 0
                   and '/' in grounded_internal_path):
                grounded_name = grounder.get_ontology().get_node_by_path(
                    grounded_internal_path).get_name()
                grounded_external_sources = self.look_up_external_types(
                    grounded_name, flag)
                grounded_internal_path = (
                    grounded_internal_path
                    [:grounded_internal_path.rfind('/')])
                if len(grounded_external_sources) == 0:
                    print("WARNING: tried to look up {} in the internal "
                          "ontology under flag {} and found nothing.  Backing "
                          "up...".format(grounded_name, flag))
            # don't duplicate if mappings overlap
            for grounded_source in grounded_external_sources:
                if grounded_source not in seen_sources:
                    new_grounded_classes.append((grounded_source, score))
                    seen_sources.add(grounded_source)
        # return top_k value to normal
        return new_grounded_classes[:grounder.get_k()]
