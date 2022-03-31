import os,sys
import yaml

hume_root = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir,os.pardir,os.pardir))

def dfs_visit(root,current_stack,result_set):
    if isinstance(root,list):
        for child in root:
            if isinstance(child, str):
                result_set.add("{}/{}".format(current_stack,child))
            elif isinstance(child,dict):
                dfs_visit(child,"{}".format(current_stack),result_set)
            else:
                raise NotImplementedError
    elif isinstance(root,dict):
        for k,v in root.items():
            result_set.add("{}/{}".format(current_stack,k))
            if isinstance(v,list):
                for child in v:
                    dfs_visit(child,"{}/{}".format(current_stack,k),result_set)
            else:
                assert isinstance(v,str)
                result_set.add("{}/{}/{}".format(current_stack,k,v))
    else:
        assert isinstance(root,str)
        result_set.add("{}/{}".format(current_stack,root))


def main():
    wm_gitlab_mirror_root = os.path.join(hume_root,"resource",'dependencies','probabilistic_grounding','WM_Ontologies')
    file_root = os.path.join(wm_gitlab_mirror_root,'CompositionalOntology.yml')
    with open(file_root) as fp:
        ontology_root = yaml.safe_load(fp)
    result_set = set()
    dfs_visit(ontology_root,"",result_set)
    for point in sorted(result_set):
        print(point)

if __name__ == "__main__":
    main()