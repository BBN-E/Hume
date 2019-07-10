
import sys
import json
import codecs
import glob
from collections import defaultdict

from nlplingo.common.io_utils import ComplexEncoder

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        params = json.load(f)


    kw_dict = defaultdict(list)
    for filepath in glob.glob(params['chunks_dir'] + '/*/*'):
        with codecs.open(filepath, 'r', encoding='utf-8') as f:
            datas = json.load(f)
        for data in datas:
            key = data['text_normalized'].replace(' ', '_')
            kw_dict[key].append(data)

    for kw in kw_dict.keys():
        with codecs.open(params['outdir'] + '/' + kw, 'w', encoding='utf-8') as o:
            o.write(json.dumps(kw_dict[kw], indent=4, cls=ComplexEncoder, ensure_ascii=False))



