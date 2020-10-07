import os,sys,json,shutil

hume_root = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir,os.pardir,os.pardir))
project_root = os.path.realpath(os.path.join(__file__,os.pardir))
sys.argv.append(project_root)

from utils import list_spliter_by_batch_size

def simulate_ecopy(dst_folder):
    # shutil.copytree(os.path.join(hume_root,'bin'),os.path.join(dst_folder,'bin'))
    shutil.copytree(os.path.join(hume_root,'lib'),os.path.join(dst_folder,'lib'))
    shutil.copytree(os.path.join(hume_root,'sequences'),os.path.join(dst_folder,'sequences'))
    shutil.copytree(os.path.join(hume_root,'templates'),os.path.join(dst_folder,'templates'))

def main():
    config_file_path = os.path.join(hume_root,'lib','runs','hume_test_cx.par')
    output_dir = "/nfs/raid88/u10/users/hqiu/integration_test/040720"
    input_cdr_list = "/nfs/raid88/u10/users/hqiu/raw_corpus/cx/cx_estonia_cdr.list"


    shutil.rmtree(output_dir,ignore_errors=True)
    os.makedirs(output_dir,exist_ok=True)

    with open(config_file_path) as fp:
        config_file = fp.read()

    cdr_list = list()
    with open(input_cdr_list) as fp:
        for i in fp:
            i = i.strip()
            cdr_list.append(i)

    cdr_lists = list_spliter_by_batch_size(cdr_list,100)
    for idx,cdr_list in enumerate(cdr_lists):
        batch_root = os.path.join(output_dir,"hume_test_cx_040720_{}".format(idx))
        os.makedirs(batch_root)
        simulate_ecopy(batch_root)

        with open(os.path.join(batch_root,'batch_file.list'),'w') as wfp:
            for i in cdr_list:
                wfp.write("{}\n".format(i))

        with open(os.path.join(batch_root,'lib','runs','hume_test_cx.par'),'w') as wfp:
            batch_config = config_file.replace("hume_test.040120.cx.v1","hume_test.040120.cx.v1.{}".format(idx))
            batch_config = batch_config.replace("/nfs/raid88/u10/users/hqiu/raw_corpus/cx/cx_estonia_cdr.list.10doc",os.path.join(batch_root,'batch_file.list'))
            wfp.write(batch_config)

        with open(os.path.join(batch_root,'run.sh'),'w') as wfp:
            wfp.write("#!/bin/bash\n")
            wfp.write("SCRIPTPATH=\"$( cd \"$(dirname \"$0\")\" ; pwd -P )\"\n")
            wfp.write("cd $SCRIPTPATH && perl sequences/run.pl lib/runs/hume_test_cx.par -local\n")
            wfp.write("exit $?\n")
        os.chmod(os.path.join(batch_root,'run.sh'),0o777)



if __name__ == "__main__":
    main()