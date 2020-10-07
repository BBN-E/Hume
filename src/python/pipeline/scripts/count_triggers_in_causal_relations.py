# sample call:
# python /nfs/raid66/u14/users/azamania/scripts/count_triggers_in_causal_relations.py /nfs/raid87/u14/users/azamania/runjobs/expts/causeex_pipeline/causeex_m9_eval_0621f_new_nn_events/regular_learnit/learnit_event_event_relations_file.json /nfs/raid66/u14/users/azamania/git/CauseEx/util/python/knowledge_base/data_files/event_triggers_in_causal_relations.txt

import sys, os, codecs, json, operator

if len(sys.argv) != 3:
    print("Usage: input-learnit-relations-json-file output-counts-file")
    sys.exit(1)

input_file, output_file = sys.argv[1:]
i = codecs.open(input_file, 'r', encoding='utf8')
o = codecs.open(output_file, 'w', encoding='utf8')

json_obj = json.loads(i.read())
i.close()

counts = dict()
sorted_counts = []
for rel in json_obj:
    arg1_trigger = rel["arg1_text"]
    if arg1_trigger not in counts:
        counts[arg1_trigger] = 0
    counts[arg1_trigger] += 1

    arg2_trigger = rel["arg2_text"]
    if arg2_trigger not in counts:
        counts[arg2_trigger] = 0
    counts[arg2_trigger] += 1

    sorted_counts = sorted(counts.items(), key=operator.itemgetter(1))

for pair in reversed(sorted_counts):
    o.write(str(pair[1]) + " " + pair[0] + "\n")

o.close()
