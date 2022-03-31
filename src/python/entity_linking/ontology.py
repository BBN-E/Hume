from collections import defaultdict, OrderedDict
import yaml
import sys

def __read_tree(node,result,parents):

    def add_to_result(label):
        xpath = "/"+label
        if parents:
            xpath = '/'+'/'.join(parents)+xpath
        result[label].add(xpath)

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
    print "Reading the ontology file..."
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
        for xpath in ontology_dict[concept]:
            xpath = xpath.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/")
            normalized_concept = concept.replace("wikidata.","").replace("/_source/","/").replace("/_description/","/").replace("_"," ").lower()
            concept_tree[normalized_concept].append((xpath))
    for concept in sorted(concept_tree.keys()):
	output = [concept]
        for term in sorted(concept_tree[concept]):
            output.append(term)
        print "    ".join(output)
