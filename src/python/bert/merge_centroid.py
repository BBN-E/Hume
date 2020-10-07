import numpy as np
import json


def main(list_of_centroid_file,output_centroid_json_path):
    type_to_sum = dict()
    type_to_cnt = dict()

    for centroid_file in list_of_centroid_file:
        with open(centroid_file) as fp:
            centroid_original = json.load(fp)
        for event_type,ens in centroid_original.items():
            current_vec = np.array(ens['sum'])
            current_cnt = ens['cnt']
            current_sum = type_to_sum.get(event_type, np.zeros(current_vec.shape[0]))
            current_sum += current_vec
            type_to_sum[event_type] = current_sum
            type_to_cnt[event_type] = type_to_cnt.get(event_type, 0) + current_cnt
    final_type_to_vec = dict()
    for event_type in type_to_sum.keys():
        vec = np.true_divide(type_to_sum[event_type], type_to_cnt[event_type])
        final_type_to_vec[event_type] = vec.tolist()
    with open(output_centroid_json_path, 'w') as fp:
        json.dump(final_type_to_vec, fp, indent=4, sort_keys=True)

if __name__ == "__main__":
    list_of_centroid_file = {
        "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/bert_centroid.cx.icm.LCC.121319/centroid.json",
        "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/bert_centroid.cx.icm.internal.121319/bert/centroid.json"
    }
    output_centroid_json_path = "/nfs/raid88/u10/users/hqiu/archive/centroids/icm_lcc_internal.121319.centroid.json"
    main(list_of_centroid_file,output_centroid_json_path)