import os,sys

current_root = os.path.realpath(os.path.join(__file__,os.pardir))

sys.path.append(os.path.join(current_root,os.pardir,'knowledge_base'))

from internal_ontology import Ontology,OntologyMapper

def tree_iterator(root,callback):
    callback(root)
    for child in root.get_children():
        tree_iterator(child,callback)

def main():
    def build_node_set(input_set):
        def print_tree(root):
            input_set.add(root.path)
        return print_tree
    # internal_ontology = Ontology()
    # internal_ontology_path = "/home/hqiu/ld100/Hume_pipeline/Hume/resource/ontologies/internal/hume/event_ontology.yaml"
    # internal_to_external_map = dict()
    # internal_ontology.load_from_internal_yaml(internal_ontology_path,ontology_map=internal_to_external_map)
    # tree_iterator(internal_ontology.get_root(),print_tree)
    # print(internal_to_external_map)

    external_ontology = Ontology()
    external_ontology_path = "/home/criley/repos/WM_Ontologies/wm_with_flattened_interventions_metadata.yml"
    external_ontology.load_from_yaml_with_metadata(external_ontology_path)
    blacklisted_set = set()
    for nodes in [external_ontology.get_nodes_by_name(i) for i in {"migration","human_displacement","interventions","intervention"}]:
        for node in nodes:
            tree_iterator(node,build_node_set(blacklisted_set))
    for i in sorted(blacklisted_set):
        print("\"{}\",".format(i))


if __name__ == "__main__":
    main()