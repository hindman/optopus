#! /usr/bin/env python

import sys
import argparse

ARG_PARSE_DATA = [
    [['url_groups'],     dict(nargs = '*', choices = ['A', 'B'])],
    [['-s', '--sleep'],  dict(type = float, default = 1.0, metavar = 'SEC')],
    [['-d', '--dryrun'], dict(action = 'store_true')],
    [['-x'],             dict(action = 'append', nargs = 2)],
]

ap = argparse.ArgumentParser()

for xs, kws in ARG_PARSE_DATA:
    ap.add_argument(*xs, **kws)

opts = ap.parse_args()

print(opts)

