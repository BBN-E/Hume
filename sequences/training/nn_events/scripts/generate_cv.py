import os
import sys
import codecs
import re
import glob
from random import shuffle
from collections import defaultdict



input_dir = sys.argv[1]
output_prefix = sys.argv[2]
n_folds = int(sys.argv[3])
serif_dir = input_dir + '/serifxml'

#n_folds = 3

for fold_index in range(n_folds):

    et_to_docids = defaultdict(set)
    for filepath in glob.glob(input_dir + '/*.span'):
        filename = os.path.basename(filepath)
        docid = re.search(r'^(.*).span$', filename).group(1)

        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if 'Event type=' in line:
                    et = re.search(r'Event type="(.*?)"', line).group(1)
                    et_to_docids[et].add(docid)


    test_docids = set()
    for et in et_to_docids:
        docids = list(et_to_docids[et])
        shuffle(docids)

        test_size = int(0.3 * len(docids) + 0.5)	# 0.5 is for rounding float to int. Assume leave 30% for testing
        test_docids.update(docids[0:test_size])


    test_lines = []
    train_lines = []
    for filepath in glob.glob(input_dir + '/*.span'):
        filename = os.path.basename(filepath)
        docid = re.search(r'^(.*).span$', filename).group(1)
        if docid in test_docids:
            test_lines.append('SPAN:' + filepath + ' SERIF:' + serif_dir + '/' + docid)
        else:
            train_lines.append('SPAN:' + filepath + ' SERIF:' + serif_dir + '/' + docid)

    fold_output_prefix = '{}.fold_{}'.format(output_prefix, fold_index)
    with codecs.open(fold_output_prefix + '.train', 'w', encoding='utf-8') as o:
        for line in train_lines:
            o.write(line)
            o.write('\n')

    with codecs.open(fold_output_prefix + '.test', 'w', encoding='utf-8') as o:
        for line in test_lines:
            o.write(line)
            o.write('\n')


