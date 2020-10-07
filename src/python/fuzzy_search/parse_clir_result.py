def filter_and_output(current_ens):
    l = len(current_ens)
    score_to_cnt = dict()
    for q_id, segment_id, score in current_ens:
        score_to_cnt[score] = score_to_cnt.get(score, 0) + 1
    t = sorted(score_to_cnt.keys(), reverse=True)
    score_to_dis = dict()
    acc = 0
    for score in t:
        acc += score_to_cnt[score]
        score_to_dis[score] = acc / l
    output_ens = list()
    for q_id, segment_id, score in current_ens:
        # if score_to_dis[score] < 0.11:
        if score_to_dis[score] < 2:
            output_ens.append((q_id, segment_id, score))
    output_ens = sorted(output_ens, key=lambda x: x[2], reverse=True)
    return output_ens[:100]


def main(result_file, output_file):
    current_q_id = None
    current_ens = list()

    with open(output_file, 'w') as wfp:
        with open(result_file) as fp:
            for i in fp:
                i = i.strip()
                q_id, _, segment_id, _, score, _ = i.split("\t")
                score = float(score)
                if q_id != current_q_id:
                    should_output_ens = filter_and_output(current_ens)
                    current_ens = list()
                    current_q_id = q_id
                    wfp.write("#####################################\n")
                    for q_id, segment_id, score in should_output_ens:
                        wfp.write("{}\t{}\t{}\n".format(q_id, segment_id, score))
                current_ens.append((q_id, segment_id, score))
        should_output_ens = filter_and_output(current_ens)
        wfp.write("#####################################\n")
        for q_id, segment_id, score in should_output_ens:
            wfp.write("{}\t{}\t{}\n".format(q_id, segment_id, score))


if __name__ == "__main__":
    result_file = "/home/hqiu/ld100/clir_110619/expts/output/relevance/lithuanian_analysis_q1_ttable0.001_occur_max_tok/relevance_results/lithuanian_analysis_q1_ttable0.001_occur_max_tok.relevance.txt"

    output_file = "/nfs/raid88/u10/users/hqiu/tmp/clir_baseline.110619.filtered"
    main(result_file, output_file)
