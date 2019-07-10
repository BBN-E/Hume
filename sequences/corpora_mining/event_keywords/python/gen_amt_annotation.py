import sys
import json
import codecs
from collections import defaultdict
import os
import re
import random
import io

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        params = json.load(f)

    keywords_file = params['keywords']
    keywords = set([x.strip() for x in io.open(keywords_file, 'r',encoding='utf8').readlines()])
    event_type_to_kw_file = params['event_type_to_kw_file']
    context_dir = params['kw_context_dir']
    aux_context_dir = params['aux_context_dir']
    max_count = params['number_of_examples']
    min_number_example = params['min_number_example']
    outdir = params['outdir']

    with open(event_type_to_kw_file, 'r') as f:
        event_type_to_kw = json.load(f)
    
    kw_to_event_type = defaultdict(set)
    for event_type, keywords in event_type_to_kw.iteritems():
        for keyword in keywords:
            kw_to_event_type[keyword].add(event_type)
    
    examples = []
    examples_keyword = []
    
    for file_ in os.listdir(context_dir):
        with open(os.path.join(context_dir, file_), 'r') as f:
            kw_context = json.load(f)
            examples.extend(kw_context)
            examples_keyword.extend([file_] * len(kw_context))
            
    sample_pop = random.sample(range(len(examples)), max_count)
    
    output_examples = [examples[index] for index in sample_pop]
    
    kw_count = defaultdict(int)
    
    for index in sample_pop:
        kw_count[examples_keyword[index]]+=1

    for kw in keywords:
        count = kw_count[kw]
        if count < min_number_example:
            kw_file = aux_context_dir + '/' + kw
            if os.path.exists(kw_file):
                with open(kw_file, 'r') as f:
                    kw_context = json.load(f)
                    n_needed = max(min_number_example - count, 0)
                    if len(kw_context) > n_needed:
                        kw_context = random.sample(kw_context, n_needed)
                    output_examples.extend(kw_context)
                    kw_count[kw]+= len(kw_context)

    for example in output_examples:
        example['candidate_event_types'] = list(kw_to_event_type[example['text_normalized']])

    with open(os.path.join(outdir,'examples.json'), 'w') as f:
        json.dump(output_examples, f, sort_keys=True, indent=4)

    with open(os.path.join(outdir,'kw_count.json'), 'w') as f:
        json.dump(kw_count, f, sort_keys=True, indent=4)
        
            
            
