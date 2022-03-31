import json

class Node():
    def __init__(self ,id ,type ,aux=None):
        self.id = id
        self.type = type
        if aux is None:
            aux = dict()
        self.aux = aux

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        if isinstance(other ,Node) is False:
            return False
        return self.id == other.id

    def get_name(self):
        return self.aux['name']

    def set_name(self,name):
        self.aux['name'] = name

    def repr_cyto_json(self):
        return{
            "classes" :" ".join(self.aux['classes']),
            "data" :{
                "id" :self.id,
                "name" :self.aux['name'],
                "cnt": self.aux['cnt'],
                "type": "Node",
                "mentioned_location": list(self.aux.get("mentioned_location",set())),
                "source_state_cnt": self.aux.get('source_state_cnt',dict())
            }
        }


class Edge():
    def __init__(self ,id ,type ,left_node,right_node,aux = None):
        self.id = id
        self.type = type
        assert isinstance(left_node,Node)
        assert isinstance(right_node,Node)
        self.left_node = left_node
        self.right_node = right_node
        if aux is None:
            aux = dict()
        self.aux = aux

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        if isinstance(other,Edge) is False:
            return False
        return self.id == other.id

    def get_name(self):
        return self.aux['name']

    def set_name(self,name):
        self.aux['name'] = name

    def get_left_node_obj(self):
        return self.left_node

    def get_right_node_obj(self):
        return self.right_node

    def get_score(self):
        return self.aux['score']

    def set_score(self,score):
        self.aux['score'] = score

    def repr_cyto_json(self):
        return{
            "classes":" ".join(self.aux['classes']),
            "data":{
                "id":self.id,
                "name":self.aux['name'],
                "source":self.left_node.id,
                "target":self.right_node.id,
                "cnt":self.aux['cnt'],
                "type": "Edge"
            }
        }


def read_json_graph(json_graph_path):
    node_id_to_node = dict()
    edge_id_to_edge = dict()
    elem_to_examples = dict()

    with open(json_graph_path) as fp:
        graph = json.load(fp)
        nodes = graph['nodes']
        edges = graph['edges']

        for node in nodes:
            aux = {
                "name":node['node_name'],
                "classes":[node["node_type"]],
                "cnt":node['cnt']
            }
            node_obj = Node(node['node_id'],node['node_type'],aux)
            node_id_to_node[node_obj.id] = node_obj
            for example in node['examples']:
                elem_to_examples.setdefault(node['node_id'],set()).add(example)

        for edge in edges:
            aux = {
                "name": edge['edge_name'],
                "classes": [edge['edge_type']],
                "score": 0,
                "cnt":edge['cnt']
            }
            edge_id = "{}_{}_{}_{}".format(edge['left_node_id'],edge['right_node_id'],edge['edge_name'],edge['edge_type'])
            edge_obj = Edge(edge_id, edge['edge_type'], node_id_to_node[edge['left_node_id']],
                                            node_id_to_node[edge['right_node_id']], aux)
            edge_id_to_edge[edge_id] = edge_obj
            for example in edge['examples']:
                elem_to_examples.setdefault(edge_id,set()).add(example)

    nodes = set(node_id_to_node.values())
    edges = set(edge_id_to_edge.values())
    return nodes, edges,elem_to_examples

def main():
    cag_json_path = "/d4m/ears/expts/48076.cord19.full.021621.v1//expts/test_pl/merge_visualization_graph/output_eer.json"
    nodes,edges,elem_to_examples = read_json_graph(cag_json_path)
    edge_type_to_edges = dict()
    for edge in edges:
        edge_type_to_edges.setdefault(edge.get_name(),set()).add(edge)

    for edge_type,edges in edge_type_to_edges.items():
        cnt = 0
        sentence_examples = set()
        for edge in edges:
            cnt += edge.aux['cnt']
            sentence_examples.update(list(elem_to_examples.get(edge.id, set())))
        print("Edge type {} cnt {}".format(edge_type,cnt))
        for idx, sent in enumerate(list(sentence_examples)[:20]):
            print("{}: {}".format(idx,sent.replace("\n"," ")))

        print("#########")



if __name__ == "__main__":
    main()