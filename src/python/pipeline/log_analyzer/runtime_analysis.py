import os
import datetime
from log_analyzer.utils import get_job_info


def main(log_root):
    total_second = 0
    total_cnt = 0
    should_break = False
    for root,dirs,files in os.walk(log_root):
        if should_break:
            break
        for file in files:
            if file.endswith(".log") and "add_causal_relation" in file:
                with open(os.path.join(root,file)) as fp:
                    t = fp.readlines()
                scheduled_machine,started_time,possible_end_time = get_job_info(t)
                if possible_end_time:
                    job_second = (possible_end_time - started_time).total_seconds()
                    print("Start time: {}, end time: {}".format(started_time,possible_end_time))
                    print("{} :{}".format(file,job_second))
                    total_second += job_second
                    total_cnt += 1
                    if total_cnt > 200:
                        should_break = True
                        break
    print(total_second)
    print(total_cnt)
    print(total_second/total_cnt)


if __name__ == "__main__":
    log_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/logfiles/causeex_sams_baltic.120719.121919/event_event_relation"
    main(log_root)