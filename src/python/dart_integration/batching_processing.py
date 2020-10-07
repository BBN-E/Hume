import os,sys,json,shutil

current_script_path = __file__
sys.path.append(os.path.realpath(os.path.join(current_script_path,os.path.pardir)))

from multiprocessing import Manager,Process
from downstream import kafka_consumer_batching_main,cdr_retrive_batching
from main_executor import main_executor
from upstream import upstream_main

def main():
    config_path = "/extra/config.json"
    with open(config_path) as fp:
        config = json.load(fp)
    with Manager() as manager:
        p = Process(target=kafka_consumer_batching_main, args=(config_path,))
        p.start()
        p.join(config.get("hume.batching.kafka_timeout",60))
        p.terminate()
    cdr_retrive_batching(config_path)
    cdr_storage_dir_tmp = os.path.join(config['hume.tmp_dir'], 'cdrs_tmp')
    file_size_list = []
    for file in os.listdir(cdr_storage_dir_tmp):
        p = os.path.join(cdr_storage_dir_tmp,file)
        file_size_list.append([p,os.stat(p).st_size])
    file_size_list = sorted(file_size_list,key=lambda x:x[1],reverse=False)
    num_of_cdrs_for_processing = len(file_size_list)
    if config.get("hume.batching.maximum_num_of_cdrs_for_processing",None) is not None:
        num_of_cdrs_for_processing = min(config.get("hume.batching.maximum_num_of_cdrs_for_processing",None),len(file_size_list))
    file_size_list = file_size_list[:num_of_cdrs_for_processing]
    processing_list_path = os.path.join(config['hume.tmp_dir'],'processing.list')
    with open(processing_list_path,'w') as wfp:
        for i in file_size_list:
            wfp.write("{}\n".format(i[0]))
    main_executor(config_path,processing_list_path)
    upstream_main(config_path,True)

if __name__ == "__main__":
    main()