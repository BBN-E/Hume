import os
import yaml

hume_root = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir, os.pardir))


def dfs_visit(root, current_stack, result_set):
    if isinstance(root, list):
        for child in root:
            if isinstance(child, str):
                result_set.add("{}/{}".format(current_stack, child))
            elif isinstance(child, dict):
                dfs_visit(child, "{}".format(current_stack), result_set)
            else:
                raise NotImplementedError
    elif isinstance(root, dict):
        for k, v in root.items():
            result_set.add("{}/{}".format(current_stack, k))
            if isinstance(v, list):
                for child in v:
                    dfs_visit(child, "{}/{}".format(current_stack, k), result_set)
            else:
                assert isinstance(v, str)
                result_set.add("{}/{}/{}".format(current_stack, k, v))
    else:
        assert isinstance(root, str)
        result_set.add("{}/{}".format(current_stack, root))


def get_all_endpoints_joint_by_slash(external_ontology_yml_path):
    with open(external_ontology_yml_path) as fp:
        ontology_root = yaml.safe_load(fp)
    result_set = set()
    dfs_visit(ontology_root, "", result_set)
    return result_set


class ExternalOntologyNode(object):
    def __init__(self):
        self.examples = set()
        self.definition = None
        self.descriptions = list()
        self.name = None
        self.path = None
        self.polarity = None
        self.patterns = set()


def dfs_visit_ontology_metadata(root, current_stack, external_ontology_path_to_node):
    if isinstance(root, list):
        for child in root:
            dfs_visit_ontology_metadata(child, current_stack, external_ontology_path_to_node)
    elif isinstance(root, dict):
        if len({"name", "examples", "definition", "polarity", "pattern"}.intersection(root.keys())) > 0:
            # Leaf/groundable
            current_path = "{}/{}".format(current_stack, root['name'])
            if current_path not in external_ontology_path_to_node:
                external_node = ExternalOntologyNode()
                external_ontology_path_to_node[current_path] = external_node
            external_node = external_ontology_path_to_node[current_path]
            external_node.examples.update(root['examples'])
            external_node.definition = root.get("definition", None)
            external_node.name = root['name']
            external_node.path = current_path
            external_node.polarity = root.get("polarity", None)
            external_node.patterns.update(root.get('pattern', set()))

        for k, v in root.items():
            if k not in {"name", "examples", "definition", "definiton", "polarity", "pattern", "OntologyNode",
                         "semantic type"}:
                # Create intermediate nodes if not exist
                current_path = "{}/{}".format(current_stack, k)
                if current_path not in external_ontology_path_to_node:
                    external_node = ExternalOntologyNode()
                    external_ontology_path_to_node[current_path] = external_node
                    external_node.name = k
                    external_node.path = current_path
                dfs_visit_ontology_metadata(v, "{}/{}".format(current_stack, k), external_ontology_path_to_node)

    else:
        raise ValueError(root)


def parse_external_ontology_metadata(external_ontology_metadata_path):
    raise RuntimeError("This is deprecated!!!")
    with open(external_ontology_metadata_path) as fp:
        ontology_yaml_root = yaml.safe_load(fp)
    ret = dict()
    dfs_visit_ontology_metadata(ontology_yaml_root, "", ret)
    return ret


def dfs_visit_ontology_metadata_new(root, current_stack, external_ontology_path_to_node):
    if isinstance(root, dict):
        assert len(root.keys()) == 1 and list(root.keys())[0] == "node"
        real_root = root["node"]
        current_path = "{}/{}".format(current_stack, real_root['name'])
        if current_path not in external_ontology_path_to_node:
            external_node = ExternalOntologyNode()
            external_ontology_path_to_node[current_path] = external_node
        external_node = external_ontology_path_to_node[current_path]
        external_node.name = real_root['name']
        external_node.examples.update(real_root.get("examples", ()))
        external_node.descriptions = real_root.get("descriptions", list())
        external_node.path = current_path
        external_node.polarity = real_root.get("polarity", None)
        external_node.patterns.update(real_root.get('patterns', set()))
        external_node.semantic_type = real_root.get("semantic type", None)
        # print(set(real_root.keys()).difference({"name","examples","descriptions","polarity","patterns","semantic type","children"}))
        for child in real_root.get("children", ()):
            dfs_visit_ontology_metadata_new(child, current_path, external_ontology_path_to_node)
    else:
        raise NotImplementedError()


def parse_external_ontology_metadata_new(external_ontology_metadata_path):
    with open(external_ontology_metadata_path) as fp:
        ontology_yaml_root = yaml.safe_load(fp)
    ret = dict()
    dfs_visit_ontology_metadata_new(ontology_yaml_root[0], "", ret)
    return ret

def print_examplers_to_endpoints(ontology_path_to_ontology_node):
    existed_nouns = set()
    with open(os.path.join(hume_root,"resource/generic_events/generic_event.whitelist.wn-fn.variants")) as fp:
        for i in fp:
            i = i.strip()
            if i.startswith("#") is False:
                existed_nouns.add(i)
    noun_to_cnt = dict()
    with open("/home/hqiu/tmp/all_mentions.dump") as fp:
        for i in fp:
            i = i.strip()
            i = i.lower()
            for t in i.split(" "):
                t = t.strip()
                if len(t) > 0:
                    noun_to_cnt[t] = noun_to_cnt.get(t,0) + 1
    exampler_to_endpoint = dict()
    for ontology_path, ontology_node in ontology_path_to_ontology_node.items():
        for example in ontology_node.examples:
            for token in example.split(" "):
                if len(token.strip()) > 0:
                    exampler_to_endpoint.setdefault(token, list()).append(ontology_path)
    for token, ontology_paths in sorted(exampler_to_endpoint.items(),key=lambda x:noun_to_cnt.get(x[0].lower().strip(),0),reverse=True):
        if token not in existed_nouns:
            print("{}: {} {} {}".format(token, len(ontology_paths), noun_to_cnt.get(token.lower().strip(),0),list(set(ontology_paths))[:5]))

if __name__ == "__main__":
    # wm_gitlab_mirror_root = os.path.join(hume_root, "resource", 'dependencies', 'probabilistic_grounding',
    #                                      'WM_Ontologies')
    # wm_gitlab_mirror_root = "/nfs/raid88/u10/users/hqiu_ad/repos/Ontologies/"
    # file_root = os.path.join(wm_gitlab_mirror_root, 'CompositionalOntology_metadata.yml')
    # path_to_node_1 = parse_external_ontology_metadata(file_root)

    # wm_gitlab_mirror_root = "/nfs/raid88/u10/users/hqiu_ad/repos/Ontologies/"
    # file_root = os.path.join(wm_gitlab_mirror_root, 'CompositionalOntology_metadata.yml')
    file_root = "/nfs/raid88/u10/users/hqiu_ad/data/wm/ontology_49277ea4-7182-46d2-ba4e-87800ee5a315.yml"
    path_to_node_2 = parse_external_ontology_metadata_new(file_root)
    # file_root = os.path.join(wm_gitlab_mirror_root, 'CompositionalOntology.yml')
    # external_ontology_paths = get_all_endpoints_joint_by_slash(file_root)
    for ontology_path, ontology_node in path_to_node_2.items():
        print("{}: {}".format(ontology_path,ontology_node.examples))

    print_examplers_to_endpoints(path_to_node_2)
