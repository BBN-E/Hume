import yaml

class OntologyTreeNode(object):
    def __init__(self,**kwargs):
        self.__dict__.update(kwargs)

class InternalOntologyTreeNode(OntologyTreeNode):
    pass

def dfs_visit_build_internal_ontology_treenode(root,node_name_to_nodes_mapping,current_node_key):
    children = list()
    key_dict = dict()
    for dct in root:
        for key, value in dct.items():
            if key.startswith("_"):
                key_dict[key] = value
            else:
                children.append(dfs_visit_build_internal_ontology_treenode(value,node_name_to_nodes_mapping,key))
    new_internal_ontology_node = InternalOntologyTreeNode(**key_dict)
    new_internal_ontology_node.parent = None
    new_internal_ontology_node.children = children
    new_internal_ontology_node.exemplars = set()
    for i in children:
        i.parent = new_internal_ontology_node
    new_internal_ontology_node.original_key = current_node_key
    node_name_to_nodes_mapping.setdefault(current_node_key,set()).add(new_internal_ontology_node)
    return new_internal_ontology_node

def build_internal_ontology_tree_without_exampler(yaml_path):
    with open(yaml_path,'r') as fp:
        y = yaml.safe_load(fp)
    node_name_to_nodes_mapping = dict()
    yaml_root = y[0]['Event']
    ontology_tree_root = dfs_visit_build_internal_ontology_treenode(yaml_root,node_name_to_nodes_mapping,"Event")
    return ontology_tree_root,node_name_to_nodes_mapping

if __name__ == "__main__":
    yaml_path = "/nfs/raid88/u10/users/hqiu_ad/repos/learnit/inputs/domains/CORD_19/ontology/unary_event_ontology.yaml"
    ontology_tree_root, node_name_to_nodes_mapping = build_internal_ontology_tree_without_exampler(yaml_path)
    for node_name,nodes in node_name_to_nodes_mapping.items():
        print(node_name)