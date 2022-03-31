
from external_ontology import get_all_endpoints_joint_by_slash

def main():
    wm_compositional_ontology_current_path = "/nfs/raid88/u10/users/hqiu_ad/repos/Hume/resource/dependencies/probabilistic_grounding/WM_Ontologies/CompositionalOntology.yml"
    all_external_ontology_path_current = get_all_endpoints_joint_by_slash(wm_compositional_ontology_current_path)
    wm_compositional_ontology_prev_path = "/home/hqiu/tmp/Ontologies/CompositionalOntology_v2.1.yml"
    all_external_ontology_path_prev = get_all_endpoints_joint_by_slash(wm_compositional_ontology_prev_path)

    last_two_suffix_set = set()
    for p in all_external_ontology_path_prev:
        last_two_suffix_set.add(tuple(p.split("/")[-2:]))

    print("###############")
    for p in all_external_ontology_path_current.difference(all_external_ontology_path_prev):
        last_two_suffix = tuple(p.split("/")[-2:])
        if last_two_suffix not in last_two_suffix_set:
            print(p)
    # print("###############")
    # for p in all_external_ontology_path_prev.difference(all_external_ontology_path_current):
    #     print(p)

if __name__ == "__main__":
    main()