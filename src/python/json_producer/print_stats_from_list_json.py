import json
from pprint import pprint

n_accent_events=0
n_entities=0
n_mentions=0
n_relations=0
n_events=0


accent_events_t=dict()
entities_t=dict()
entities_sub_t=dict()
relations_t=dict()
events_t=dict()

file_list_json_files="/nfs/mercury-05/u34/CauseEx/data/month_1_deliverables/json_for_1500_docs.list"

with open(file_list_json_files) as list_json_files:
    lines = list_json_files.readlines()
    for line in lines:
        line = line.strip()
        print(line.strip())
        with open(line) as data_file:    
            try:
                data = json.load(data_file)
            except ValueError:
                print("skip line: " + line)
                next
            

            n_accent_events+=len(data['accent_events'])
            n_entities+=len(data['entities'])
            n_relations+=len(data['relations'])
            n_events+=len(data['events'])

            for item in data['accent_events']:
                print("accent_event: " + str(item))
                # print("adding " + item['event_name'] + " , before: " + str(accent_events_t.get(item['event_name'], 0)))
                accent_events_t[item['event_code'] + ' ' + item['event_name']] = accent_events_t.get(item['event_code'] + ' ' + item['event_name'], 0) + 1
                # print("adding " + item['event_name'] + " , after: " + str(accent_events_t[item['event_name']]))
            for item in data['entities']:
                print("entity: " + str(item))
                entities_t[item['entity_type']+"."+item['entity_subtype']] = entities_t.get(item['entity_type']+"."+item['entity_subtype'], 0) + 1
#            for item in data['entities']:
#                entities_sub_t[item['entity_subtype']] = entities_sub_t.get(item['entity_subtype'], 0) + 1
            for item in data['relations']:
                print("relation: " + str(item))
                relations_t[item['relation_type']] = relations_t.get(item['relation_type'], 0) + 1
            for item in data['events']:
                print("event: " + str(item))
                events_t[item['event_type']] = events_t.get(item['event_type'], 0) + 1

            for entity in data['entities']:
                n_mentions+=len(entity['mentions'])

    print('=== accent_events: ' + str(n_accent_events))
    for key in accent_events_t.keys():
        print('  ' + str(accent_events_t[key]) + '  ' + key)
    print('=== entities: ' + str(n_entities))
    for key in entities_t.keys():
        print('  ' + str(entities_t[key]) + '  ' + key)
#    for key in entities_sub_t.keys():
#        print('  ' + str(entities_sub_t[key]) + '  ' + key)
    print('=== relations: ' + str(n_relations))
    for key in relations_t.keys():
        print('  ' + str(relations_t[key]) + '  ' + key)
    print('=== events: ' + str(n_events))
    for key in events_t.keys():
        print('  ' + str(events_t[key]) + '  ' + key)
