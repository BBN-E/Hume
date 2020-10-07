import os,sys,json,shutil

import datetime


def filter_logic(event_frame):
    try:
        start_time = datetime.datetime.utcfromtimestamp(event_frame['startTime']/1000)
        end_time = datetime.datetime.utcfromtimestamp(event_frame['endTime']/1000)
    except ValueError:
        return True
    if start_time.year < 1995 or end_time.year >= 2025:
        return True
    if end_time - start_time > datetime.timedelta(days=31):
        return True
    if event_frame['eventType'] == "/wm/concept/causal_factor":
        return True
    return False



def main():
    jsonl_path = "/home/hqiu/ld100/Hume_pipeline_2/Hume/expts/wm_thanksgiving.121019.121619.v1/event_timeline.ljson"
    output_folder = "/nfs/raid88/u10/users/hqiu/event_timeline.021820"
    shutil.rmtree(output_folder,ignore_errors=True)
    event_frame_root = os.path.join(output_folder,'event_frame')
    sent_info_root = os.path.join(output_folder,'sent_info_root')
    os.makedirs(event_frame_root,exist_ok=True)
    os.makedirs(sent_info_root,exist_ok=True)
    doc_id_to_sent_id_to_sent_token = dict()
    event_type_to_year_to_month = dict()
    event_type_to_year_to_mount_cnt = dict()
    with open(jsonl_path) as fp:
        for i in fp:
            event_frame = json.loads(i)
            if filter_logic(event_frame) is True:
                continue
            event_happen_time = datetime.datetime.utcfromtimestamp(event_frame['startTime']/1000)
            event_happen_year = event_happen_time.year
            event_happen_month = event_happen_time.month
            doc_id = event_frame['docId']
            sent_id = event_frame['sentIdx']
            doc_id_to_sent_id_to_sent_token.setdefault(doc_id,dict())[sent_id] = event_frame['sentInTokens']
            event_frame['arguments'].append({"type":"trigger","canonicalText":" ".join(event_frame['sentInTokens'][event_frame['anchorStartIdx']:event_frame['anchorEndIdx'] + 1])})
            del event_frame['sentInTokens']
            escaped_event_type = event_frame['eventType'].split("/")[-1]
            event_type_to_year_to_month.setdefault(escaped_event_type,dict()).setdefault(event_happen_year,dict()).setdefault(event_happen_month,list()).append(event_frame)
    for doc_id in doc_id_to_sent_id_to_sent_token.keys():
        with open(os.path.join(sent_info_root,doc_id),'w') as fp:
            json.dump(doc_id_to_sent_id_to_sent_token[doc_id],fp,indent=4,ensure_ascii=False)
    for event_type in event_type_to_year_to_month.keys():
        for year in event_type_to_year_to_month[event_type].keys():
            for month in event_type_to_year_to_month[event_type][year].keys():
                os.makedirs(os.path.join(event_frame_root, event_type, str(year),str(month)), exist_ok=True)
                for event_frame in event_type_to_year_to_month[event_type][year][month]:
                    event_id = "{}_{}_{}_{}".format(event_frame['docId'],event_frame['sentIdx'],event_frame['anchorStartIdx'],event_frame['anchorEndIdx'])
                    with open(os.path.join(event_frame_root,event_type,str(year),str(month),event_id),'w') as wfp:
                        json.dump(event_frame,wfp,indent=4,ensure_ascii=False)
                event_type_to_year_to_mount_cnt.setdefault(event_type,dict()).setdefault(year,dict())[month] = len(event_type_to_year_to_month[event_type][year][month])
    with open(os.path.join(output_folder,'event_type_year_month_cnt.json'),'w') as wfp:
        json.dump(event_type_to_year_to_mount_cnt,wfp,indent=4,ensure_ascii=False)
if __name__ == "__main__":
    main()