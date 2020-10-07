import os,sys,json,time,shutil,requests,io

from domain_factory import domain

def upload_file_to_dart(serialization_dir,upload_uri,hume_version,file_suffix):
    for root,dirs,files in os.walk(serialization_dir):
        for file in files:
            if file.endswith(file_suffix):
                doc_uuid = file[:-len(file_suffix)]
                print("Handling {}".format(doc_uuid))
                with open(os.path.join(root, file),'rb') as fp:
                    metadata = {"identity":"hume","version":hume_version,"document_id":doc_uuid}
                    metadata_io = io.BytesIO(json.dumps(metadata,ensure_ascii=False).encode("utf-8"))
                    metadata_io.seek(0)
                    r = requests.post("{}/upload".format(upload_uri),files={
                        "metadata":(None,json.dumps(metadata,ensure_ascii=False)),
                        "file":fp
                    })
                    print(r.text)

def upstream_main(config_path,should_upload):
    with open(config_path) as fp:
        config = json.load(fp)
    hume_root_in_docker = "/wm_rootfs/git/Hume"
    result_root = os.path.join(config['hume.tmp_dir'],'results')
    current_result_root = os.path.join(result_root,str(int(time.time())))
    # Preserve log files
    if os.path.exists(os.path.join(hume_root_in_docker,'logfiles')):
        os.makedirs(current_result_root, exist_ok=True)
        shutil.move(os.path.join(hume_root_in_docker,'logfiles'),os.path.join(current_result_root,'logfiles'))
    # copy result files
    file_suffix = domain[config['hume.domain']]['suffix']
    domain_expt_name = domain[config['hume.domain']]['job_name']
    serialization_folder = os.path.join(hume_root_in_docker,'expts/{}/serialization'.format(domain_expt_name))
    handled_files = 0
    if os.path.exists(serialization_folder):
        current_result_file_root = os.path.join(current_result_root,'results')
        os.makedirs(current_result_file_root,exist_ok=True)
        # get current hume version
        hume_version = sorted(os.listdir("/d4m/nlp/releases/Hume/"))[-1]
        for root, dirs, files in os.walk(serialization_folder):
            for file in files:
                if file.endswith(file_suffix):
                    doc_uuid = os.path.basename(root)
                    shutil.move(os.path.join(root, file), os.path.join(current_result_file_root, "{}{}".format(doc_uuid,file_suffix)))
                    handled_files += 1
        if handled_files > 0 and should_upload:
            upload_file_to_dart(current_result_file_root, config['DART_upload'], hume_version, file_suffix)

