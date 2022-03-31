import json,zlib,copy

def parse_label_mappings(mappings_path):
    resolved_positive_event_mentions = list()
    with open(mappings_path, 'rb') as fp:
        z = json.loads(zlib.decompress(fp.read()).decode('utf-8'))
        mappings = z[1]
        label_mappings = mappings['patternInstanceMap'][1]['data'][1]
        key_id_to_key = dict()
        val_id_to_val = dict()
        for idx, k in enumerate(label_mappings['keyList'][1]):
            key_id_to_key[idx] = k
        for idx, v in enumerate(label_mappings['valList'][1]):
            val_id_to_val[idx] = v
        k_vals_map = dict()
        for idx, en in enumerate(label_mappings['entries'][1]):
            key = en[1]['key']
            vals = [v for v in en[1]['values'][1]]
            k_vals_map[key] = vals
        for k, vals in k_vals_map.items():
            learnit_instance_identifier = key_id_to_key[k]
            instance_identifier = {
                'docid': learnit_instance_identifier['docid'],
                'sent_idx': learnit_instance_identifier['sentid'],
                'trig_idx_start': learnit_instance_identifier['slot0Start'],
                'trig_idx_end': learnit_instance_identifier['slot0End'],
                'right_idx_start': learnit_instance_identifier['slot1Start'],
                'right_idx_end': learnit_instance_identifier['slot1End'],

            }
            for v in vals:
                label_pattern = val_id_to_val[v][1]
                event_type = label_pattern['relationType']['string']
                frozen_state = label_pattern['frozenState']
                if frozen_state == "FROZEN_GOOD":
                    en = copy.deepcopy(instance_identifier)
                    en['event_type'] = event_type
                    resolved_positive_event_mentions.append(en)
    return resolved_positive_event_mentions

def main():
    labeled_mappings = {
        "/export/u10/hqiu/repos/learnit/inputs/legacy_unary_event_annotation/unary_event_wm.sjson",
        "/export/u10/hqiu/repos/learnit/inputs/domains/WM/labeled_mappings/wm_dart382.090920.sjson",
        "/export/u10/hqiu/repos/learnit/inputs/domains/WM/labeled_mappings/wm_dart_101519_vexpt1.sjson",
        "/export/u10/hqiu/repos/learnit/inputs/domains/WM/labeled_mappings/wm_factiva.120919.sjson",
    }
    type_to_ens = dict()
    mentioned_doc_ids = set()
    for labeled_mapping_path in labeled_mappings:
        positive_event_mentions = parse_label_mappings(labeled_mapping_path)
        for event_mention in positive_event_mentions:
            if event_mention['right_idx_start'] == -1:
                type_to_ens.setdefault(event_mention['event_type'],list()).append(event_mention)
                mentioned_doc_ids.add(event_mention['docid'])
    print(mentioned_doc_ids)
    print(len(mentioned_doc_ids))
    for t in type_to_ens.keys():
        print("{}: {}".format(t,len(type_to_ens[t])))
    with open("/home/hqiu/tmp/mentioned_docids",'w') as wfp:
        for i in mentioned_doc_ids:
            wfp.write("{}\n".format(i))
    with open("/nfs/raid88/u10/users/hqiu_ad/annotation/WM/030921/annotation.ljson",'w') as wfp:
        for event_type,ens in type_to_ens.items():
            for en in ens:
                wfp.write("{}\n".format(json.dumps(en)))

if __name__ == "__main__":
    main()