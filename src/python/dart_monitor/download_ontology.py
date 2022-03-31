import os
import requests

def download_new_ontology(ontology_retrival_endpoint, ontology_id, output_path,*,u=None, p=None):
    auth_obj = None
    if u is not None and p is not None:
        auth_obj = (u, p)
    r = requests.get(ontology_retrival_endpoint, auth=auth_obj, params={"id": ontology_id})
    ontology_str = r.json()["ontology"]
    with open(output_path, 'w') as wfp:
        wfp.write(ontology_str)


if __name__ == "__main__":
    output_dir = "/nfs/raid88/u10/users/hqiu_ad/data/wm"
    ontology_version = "798361a2-05da-4b12-a2af-c314bcd578c4"
    output_path = os.path.join(output_dir,"ontology_{}.yml".format(ontology_version))
    u = "Redacted"
    p = "Redacted"
    endpoint = "Redacted/dart/api/v1/ontologies"
    download_new_ontology(endpoint, ontology_version, output_path, u=u,p=p)