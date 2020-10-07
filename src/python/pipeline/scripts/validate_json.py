
import json
import os
import sys

directory = sys.argv[1]
for p, ds, fs in os.walk(directory):
    for f in fs:
        full_path = os.path.join(p, f)
        msg = "{} is not a valid json".format(full_path)
        with open(full_path, 'r') as fh:
            try:
                j = json.load(fh)
            except ValueError:
                raise ValueError(msg)
