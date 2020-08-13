#!/usr/bin/env python3

import os
import sys
import glob
import yaml
import argparse

def parse_args(args):
    parser = argparse.ArgumentParser("Generate the yaml file required by the aligner.")
    parser.add_argument("input_dir", type=str, help="Path to the directory containing input txt files.")
    args = parser.parse_args()
    if args.input_dir.endswith('/'):
        args.input_dir = args.input_dir[:-1]
    return args

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    
    pattern = args.input_dir + '/*.txt'
    globs = glob.glob(pattern)

    yaml_file = args.input_dir + '/' + os.path.basename(args.input_dir) + '.yaml'
    text_list = []
    for i, fname in enumerate(globs):
        with open(fname,'r') as f:
            text = f.read()
        text_list.append({'id': 'd'+ str(i), 'text': text})

    with open(yaml_file, 'w') as f:
        documents = yaml.dump(text_list, f)

        
