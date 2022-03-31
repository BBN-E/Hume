import os,sys

hume_root = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir,os.pardir,os.pardir))

from hume_ontology.internal_ontology import build_internal_ontology_tree_without_exampler
from external_ontology import get_all_endpoints_joint_by_slash

def main():
    wm_gitlab_mirror_root = os.path.join(hume_root,"resource",'dependencies','probabilistic_grounding','WM_Ontologies')
    internal_ontology_path = os.path.join(hume_root,"resource/ontologies/internal/hume/compositional_event_ontology.yaml")
    wm_compositional_ontology_metadata_path =  os.path.join(wm_gitlab_mirror_root,'CompositionalOntology_metadata.yml')
    wm_compositional_ontology_path = os.path.join(wm_gitlab_mirror_root, 'CompositionalOntology.yml')
    all_external_ontology_path = get_all_endpoints_joint_by_slash(wm_compositional_ontology_path)
    ontology_tree_root, node_name_to_nodes_mapping = build_internal_ontology_tree_without_exampler(internal_ontology_path)
    internal_node_to_external_nodes = dict()
    for node_name,nodes in node_name_to_nodes_mapping.items():
        for node in nodes:
            WM_endpoint = []
            for s in node._source:
                if "WM" in s:
                    WM_endpoint.append(s.split(":")[1].strip())
            internal_node_to_external_nodes.setdefault(node_name,set()).update(WM_endpoint)
    for event_type,external_types in internal_node_to_external_nodes.items():
        print("{} -> {}".format(event_type, external_types))
    event_type_file = os.path.join(hume_root,"resource/event_consolidation/wm/theme-factor_types.txt")
    white_listed_type = set()
    with open(event_type_file) as fp:
        for i in fp:
            i = i.strip()
            white_listed_type.add(i)
    external_type_to_cnt = dict()
    for event_type in white_listed_type:
        external_types = internal_node_to_external_nodes.get(event_type,set())

        for external_type in external_types:
            external_type_to_cnt[external_type] = external_type_to_cnt.get(external_type,0)+1
    print("###################")
    for external_type in all_external_ontology_path:
        print(external_type)
    print("###################")
    for external_type in external_type_to_cnt.keys():
        print(external_type)
    print("###################")

if __name__ == "__main__":
    main()