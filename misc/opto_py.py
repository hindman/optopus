#! /usr/bin/env python

# A quick implementation of zero-config option parsing.

import sys
import json
import re

LONG_OPT_RGX  = re.compile(r'^--(\w[\w\-]*)$')
SHORT_OPT_RGX = re.compile(r'^-(\w+)$')

def parse_args(args):
    opts = dict(args = [])
    for a in args:

        m = LONG_OPT_RGX.search(a)
        if m:
            k = m.group(1)
            opts[k] = True
            continue

        m = SHORT_OPT_RGX.search(a)
        if m:
            k = m.group(1)
            for char in k:
                opts[char] = True
            continue

        opts['args'].append(a)

    return opts

def main(args):
    opts = parse_args(args)
    print json.dumps(opts, indent = 4)

if __name__ == '__main__':
    main(sys.argv[1:])


