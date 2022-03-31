import sys
import yaml
import json
import argparse
from collections import defaultdict

from knowledge_base.internal_ontology import *


########## External yaml file ############
class ExternalYaml(object):
    def __init__(self, filepath):
        self.ontology = Ontology()
        self.ontology.load_from_yaml_plain(filepath)

    def get_paths(self):
        ret = set()

        nodes = [self.ontology.get_root()]
        while nodes:
            n = nodes.pop()
            nodes.extend(n.get_children())
            ret.add(n.get_path())

        return ret


############ Internal yaml file #############
class InternalYaml(object):
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            self.data = yaml.safe_load(f)
        self.path_to_wm_values = defaultdict(list)

    def get_paths(self):
        root = self.data[0]
        self.parse_yaml_node(root, '')

        internal_wm_values = set()
        for wm_value in self.path_to_wm_values.values():
            internal_wm_values.update(set(wm_value))

        return sorted(internal_wm_values)

    def parse_yaml_node(self, node, parent_name):
        assert isinstance(node, dict)
        assert len(node) == 1

        node_name = list(node.keys())[0]
        path_name = '{}/{}'.format(parent_name, node_name)

        # first get the: _source, _description, _examples
        source_d = None
        description_d = None
        examples_d = None
        alternative_d = None
        children_dicts = []
        for d in node[node_name]:
            assert isinstance(d, dict)
            if '_source' in d:    
                source_d = d
            elif '_description' in d:
                description_d = d
            elif '_examples' in d:
                examples_d = d
            elif '_alternative_id' in d:
                alternative_d = d
            else:
                children_dicts.append(d)

        wm_value = None
        for value in source_d['_source']:
            if value.startswith('WM: '):
                wm_value = value.split(' ')[-1]
        if wm_value is not None:
            self.path_to_wm_values[path_name].append(wm_value)

        if len(children_dicts) == 0:
            return path_name

        for child in children_dicts:
            self.parse_yaml_node(child, path_name)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--internal_yamlfile')
    parser.add_argument('--external_yamlfile')
    args = parser.parse_args()

    internal_yaml = InternalYaml(args.internal_yamlfile)
    internal_paths = internal_yaml.get_paths()

    external_yaml = ExternalYaml(args.external_yamlfile)
    external_paths = external_yaml.get_paths()

    print('====== Internal not in external ========')
    for path in internal_paths:
        if path not in external_paths:
            print(path)

    print('====== External not in internal ========')
    for path in external_paths:
        if path not in internal_paths:
            print(path)

