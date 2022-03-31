from collections import defaultdict, OrderedDict
import yaml
import sys

def __read_tree(node,result,parents):

    def add_to_result(label):
        # xpath = "/"+label
        all_labels = [label]
        parent_xpath = None
        if parents:
            parent_xpath = '/'+'/'.join(parents)
            # xpath = '/'+'/'.join(parents)+xpath
            all_labels.extend(parents)
        all_labels = set(all_labels)
        if parent_xpath:
            for lb in all_labels:
                result[parent_xpath].add(lb)

    if isinstance(node,str):  # leaf concept
        add_to_result(node)
        return
    children = node if isinstance(node,list) else node.values()[0]
    self_added_as_parent = False
    if isinstance(node,dict):
        if len(node.keys())>1:
            raise ValueError(str(node)+' is a dict with multiple keys')
        node_label = node.keys()[0]
        add_to_result(node_label)
        parents.append(node_label)
        self_added_as_parent = True
    for child in children:
        __read_tree(child,result,parents)
    if self_added_as_parent:
        parents.pop()

def read_ontology(ontology_file_path):
    # expand ontology
    # print "Reading the ontology file..."
    ontology_dict = defaultdict(set)
    with open(ontology_file_path) as ontology_fp:
        ontology = yaml.safe_load(ontology_fp)
        __read_tree(ontology,ontology_dict,[])
    return ontology_dict


if __name__=='__main__':
    ontology_dict =  read_ontology(sys.argv[1])
    concept_tree = defaultdict(list)
    for concept in sorted(ontology_dict.keys()):
        if concept.endswith("_source") or concept.endswith("_description"):
            continue
        concept = concept.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/")
        # normalized_concept = concept.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/").replace("_"," ").lower()
        for label in ontology_dict[concept]:
            # xpath = xpath.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/")
            # normalized_concept = concept.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/").replace("_"," ").lower()
            concept_tree[concept].append((label))
    for concept in sorted(concept_tree.keys()):
	output = []
        for term in sorted(concept_tree[concept]):
            if term=='_source' or term=='_description':
                continue
            output.append(term)
        print concept+"\t"+",".join(output)
