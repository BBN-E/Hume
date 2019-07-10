import os
import argparse
import re
from collections import deque

def get_crp_from_file(file_path):
    crp = None
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        m = re.match(r'class_label #C=(\d+),#R=(\d+),#P=(\d+)',line)
        if m:
            crp = {
                'C':int(m.group(1)),
                'R':int(m.group(2)),
                'P':int(m.group(3))
                }
            break
    return crp, lines

def _main(args):
    crp_total = {
        'C': 0,
        'R': 0,
        'P': 0
    }
    out_lines = deque()
    for file_ in args.input_files:
        crp, lines = get_crp_from_file(file_)
        crp_total['C'] += crp['C']
        crp_total['R'] += crp['R']
        crp_total['P'] += crp['P']
        out_lines.extend(lines)
    P = float(crp_total['C'])/float(crp_total['P']) 
    R = float(crp_total['C'])/float(crp_total['R'])
    F = (2 * P * R) / ( R + P)
    top_line = 'class_label #C={},#R={},#P={} R,P,F={:.2},{:.2},{:.2}\n'.format(
        crp_total['C'],
        crp_total['R'],
        crp_total['P'],
        R,
        P,
        F
    )
    out_lines.appendleft(top_line)
    with open(args.output_file,'w') as f:
        f.writelines(out_lines)
    

def setup_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_files', type=str, nargs='+', required=True)
    parser.add_argument('--output_file', type=str)
    return parser

if __name__=="__main__":
    _main(setup_parse().parse_args())
