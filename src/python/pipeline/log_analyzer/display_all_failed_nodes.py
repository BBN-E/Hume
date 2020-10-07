import os

from log_analyzer.utils import get_job_info


def main(log_root):
    fail_nodes = set()
    successed_nodes = set()
    node_to_cnt = dict()
    for root,dirs,files in os.walk(log_root):
        for file in files:
            if file.endswith(".log") and "run_bert" in file:
                with open(os.path.join(root,file)) as fp:
                    t = fp.readlines()
                scheduled_machine,started_time,possible_end_time = get_job_info(t)
                if possible_end_time is None:
                    fail_nodes.add(scheduled_machine)
                else:
                    successed_nodes.add(scheduled_machine)
                    node_to_cnt[scheduled_machine] = node_to_cnt.get(scheduled_machine,0)+1
                # if scheduled_machine == "mr304.bbn.com":
                #     print(os.path.join(root,file))
    for node in fail_nodes:
        print(node)
    for scheduled_machine in sorted(node_to_cnt.keys(),key=lambda x:node_to_cnt[x],reverse=True):
        cnt = node_to_cnt[scheduled_machine]
        print("{}: {}".format(scheduled_machine,cnt))
    # print(successed_nodes)


if __name__ == "__main__":
    log_root = "/home/hqiu/ld100/Hume_pipeline_2/Hume/logfiles/causeex_sams_baltic.120719.120919/bert"
    main(log_root)