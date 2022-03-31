import os, sys, copy

current_script_path = __file__
project_root = os.path.realpath(os.path.join(
    current_script_path, os.path.pardir, os.path.pardir, os.path.pardir, os.path.pardir))
sys.path.append(project_root)

class Node(object):
    def __init__(self,node_id):
        self.node_id = node_id
        self.name = node_id
        self.children = dict()
        self.parent = set()
        self.aux = dict()

    def to_tree(self):
        d = dict()
        d["id"] = self.node_id
        d["name"] = self.name
        d["children"] = list()
        for child_id,child_node in self.children.items():
            d["children"].append(child_node.to_tree())
        d["aux"] = copy.deepcopy(self.aux)
        return d

def convert_HAC_output_to_tree(hac_file_path):
    node_id_to_node = dict()
    with open(hac_file_path) as fp:
        for i in fp:
            i = i.strip()
            parent, child = i.split("->")
            parent_node = node_id_to_node.setdefault(parent,Node(parent))
            child_node = node_id_to_node.setdefault(child,Node(child))
            parent_node.children[child] = child_node
            child_node.parent.add(parent)
    return node_id_to_node


