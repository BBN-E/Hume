
import codecs
import os
import re
import sys


filelist = sys.argv[1]
npzs = sys.argv[2]

docid_re = re.compile(r'/([^/ ]+?)(\.serifxml|\.sgm\.xml|\.xml|\.npz)? *$')

docid_to_npz = {}
with codecs.open(npzs, 'r', encoding='utf8') as f:
    for line in f:
        docid = docid_re.search(line).group(1).strip()
        docid_to_npz[docid] = line.strip()

with codecs.open(filelist, 'r', encoding='utf8') as f:
    for line in f:
        docid = docid_re.search(line).group(1).strip()
        print("{} EMBEDDING:{}".format(line.strip(), docid_to_npz[docid]))
