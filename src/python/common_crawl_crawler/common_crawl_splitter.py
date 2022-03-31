import os,json

def list_spliter_by_num_of_batches(my_list, num_of_batches):
    k, m = divmod(len(my_list), num_of_batches)
    return list(my_list[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(num_of_batches))

def split(input_dict,number_split,output_dir,output_prefix):
    splits = list_spliter_by_num_of_batches(list(input_dict.keys()),number_split)
    os.makedirs(output_dir,exist_ok=True)
    for idx,key_bucket in enumerate(splits):
        new_d = dict()
        for k in key_bucket:
            new_d[k] = input_dict[k]
        with open(os.path.join(output_dir,"{}{}.json".format(output_prefix,idx)),'w') as wfp:
            json.dump(new_d,wfp,indent=4,sort_keys=True)

if __name__ == "__main__":
    input_dict_path = "/home/hqiu/wait_for_crawling.json"
    with open(input_dict_path) as fp:
        input_dict = json.load(fp)
    split(input_dict,8,"/home/hqiu/crawling_split2","wait_for_crawling_")