import io
import sys
from collections import defaultdict
import os


all_counts = defaultdict(int)
all_groundings = {}

for fname in os.listdir(sys.argv[1]):
    if not fname.endswith(".json.frequencies"):
        continue
    with io.open(os.path.join(sys.argv[1], fname), 'r', encoding='utf8') as f:
        grounding_lines = []
        count = 0
        e_type, e_text = None, None
        for line in f:
            if not line.startswith('\t'):
                #print(line)
                if e_type is not None:
                    all_counts[(e_type, e_text)] += count
                    all_groundings[(e_type, e_text)] = grounding_lines
                count, e_type, e_text = line.strip().split('\t', maxsplit=2)
                count = int(count)
                grounding_lines = []
            else:
                grounding_lines.append(line.strip())
        if e_type is not None:
            all_counts[(e_type, e_text)] += count
            all_groundings[(e_type, e_text)] = grounding_lines

with io.open(sys.argv[1] + 'all_caches.frequencies', 'w', encoding='utf8') as f:
    for pair, freq in sorted(all_counts.items(), reverse=True, key=lambda x: x[1]):
        f.write("{}\t{}\t{}\n".format(freq, pair[0], pair[1]))
        for grounding_line in all_groundings[pair]:
            f.write("\t{}\n".format(grounding_line))
