'''

This script walks through the Event internal ontology looking 
for 'NN' tags in source to create a list of Event classes to 
train using nlplingo.

'''
import yaml
import sys

input_path = sys.argv[1]

data = yaml.load(open(input_path,'r'))

def traverse_tree(node, list_):
    
    node_string = node.keys()[0]
    found = False

    for el in node[node.keys()[0]]:
        if el.keys()[0].startswith('_source'):
            if 'NN' in el['_source']:
                found = True

    for el in node[node.keys()[0]]:
        if el.keys()[0].startswith('_id') and found == True:
            list_.append(el['_id'])

    for el in node[node.keys()[0]]:
        if not el.keys()[0].startswith('_'):
            traverse_tree(el, list_)

list_ = []
prefix = []
traverse_tree(data[0], list_)

for el in sorted(list_):
    print el
