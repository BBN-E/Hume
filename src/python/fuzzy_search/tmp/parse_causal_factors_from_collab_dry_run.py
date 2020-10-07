import os

import json


def parse_future_states(future_state_json_path):
    with open(future_state_json_path) as fp:
        j = json.load(fp)
    nodes = j['nodes']
    groups = j['groups']
    set_of_names = set()
    for group in groups:
        group_member_ids = {i['id'] for i in group['members']}
        for node in nodes:
            node_id = node['id']
            if node_id in group_member_ids:
                set_of_names.add(node['name'])

    return set_of_names

def parse_initial_discourse(initial_discourse_json_path):
    with open(initial_discourse_json_path) as fp:
        j = json.load(fp)
    nodes = j['nodes']
    groups = j['groups']
    set_of_names = set()
    for group in groups:
        group_member_ids = {i['id'] for i in group['members']}
        for node in nodes:
            node_id = node['id']
            if node_id not in group_member_ids:
                set_of_names.add(node['name'])
    return set_of_names

def parse_refined_factor(refined_factor_json_path):
    with open(refined_factor_json_path) as fp:
        j = json.load(fp)
    nodes = j['nodes']
    set_of_names = set()

    for node in nodes:
        node_id = node['id']
        set_of_names.add(node['name'])
    return set_of_names


if __name__ == "__main__":
    cause_work_json_root = "/home/hqiu/massive/Dry_Run_Whiteboards"
    initial_discourse_path = os.path.join(cause_work_json_root,'Initial Discourse.json')
    future_states_path = os.path.join(cause_work_json_root,'Future State.json')
    refined_factor_1_path = os.path.join(cause_work_json_root,'Refined Factors.json')
    refined_factor_2_path = os.path.join(cause_work_json_root,'Refined Factors 2.json')
    all_causal_set = set()
    all_causal_set.update(parse_initial_discourse(initial_discourse_path))
    all_causal_set.update(parse_future_states(future_states_path))
    all_causal_set.update(parse_refined_factor(refined_factor_1_path))
    all_causal_set.update(parse_refined_factor(refined_factor_2_path))
    for i in all_causal_set:
        print(i)
