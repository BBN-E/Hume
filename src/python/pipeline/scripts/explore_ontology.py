import yaml
import codecs


# input_path = '/nfs/raid87/u12/ychan/repos/repo_clean_for_exp_wm_m12_hackathon/CauseEx/ontology/internal_ontology/hume/event_ontology.yaml'
input_path = '/nfs/ld100/u10/bmin/repo_clean_for_exp_wm_m12_hackathon/CauseEx/ontology/internal_ontology/event_ontology.yaml'

data = yaml.load(open(input_path,'r'))

id_to_path = []
def traverse_tree(node, list_, prefix):
    #print node.keys()
    # for child in node.values():
    #     if child.

    node_string = node.keys()[0]
    #print(node_string)
    #print(node[node_string][1]['_source'][-1])
    #print(node[node_string][0]['_id'])
    list_.append('.'.join(prefix + [node[node_string][0]['_id']]))

    #path_string_id = '.'.join(prefix + [node[node_string][0]['_id']])
    leaf_id = node[node_string][0]['_id']
    try:
        path_string = node[node_string][1]['_source'][-1][len('CAUSEEX: '):]
        id_to_path.append(leaf_id + '\t' + path_string)
    except:
        print "exception!"


    for el in node[node.keys()[0]]:
        if not el.keys()[0].startswith('_'):
            #traverse_tree(el, list_, prefix + [node_string])
            traverse_tree(el, list_, prefix + [node[node_string][0]['_id']])

list_ = []
prefix = []
#traverse_tree(data[0]['Event'][4], list_, prefix)
traverse_tree(data[0], list_, prefix)

for el in sorted(list_):
    print el


with codecs.open('wm_ontology.id_to_path', 'w', encoding='utf-8') as o:
    for line in id_to_path:
        o.write(line)
        o.write('\n')

