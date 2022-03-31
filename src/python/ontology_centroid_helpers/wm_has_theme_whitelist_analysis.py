import os, sys

hume_root = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, os.pardir))

from ontology_centroid_helpers.hume_ontology.internal_ontology import build_internal_ontology_tree_without_exampler, return_node_name_joint_path_str
from ontology_centroid_helpers.external_ontology import parse_external_ontology_metadata_new

def main():
    internal_ontology_path = os.path.join(hume_root, "resource/ontologies/internal/hume/compositional_event_ontology.yaml")
    external_ontology_path = "/nfs/raid88/u10/users/hqiu_ad/data/wm/ontology_49277ea4-7182-46d2-ba4e-87800ee5a315.yml"
    ontology_tree_root, node_name_to_nodes_mapping = build_internal_ontology_tree_without_exampler(internal_ontology_path)
    external_path_to_external_node = parse_external_ontology_metadata_new(external_ontology_path)
    external_path_to_internal_node = dict()
    for internal_node_name, internal_nodes in node_name_to_nodes_mapping.items():
        for internal_node in internal_nodes:
            for source in internal_node._source:
                if "WM:" in source:
                    external_path = source.replace("WM:","").strip()
                    if external_path in external_path_to_external_node:
                        external_path_to_internal_node.setdefault(external_path, set()).add(internal_node)
    has_theme_whitelist_path = os.path.join(hume_root,"resource/event_consolidation/wm/theme-factor_types_external.txt")
    has_included = set()
    with open(has_theme_whitelist_path) as fp:
        for i in fp:
            i = i.strip()
            if i not in external_path_to_external_node:
                # print(i)
                pass
            else:
                has_included.add(i)
    for i in external_path_to_external_node.keys():
        if i not in has_included:
            print(i)

if __name__ == "__main__":
    main()