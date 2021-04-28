#! /usr/bin/env python

import argparse

ACTIONS = 'create read update delete'.split()

ARG_PARSE_DATA = (
    ['groups',         dict(nargs = 2, metavar = 'GRP')],
    ['items',          dict(nargs = 2, metavar = 'IT')],
    ['-s', '--sleep',  dict(type = float, default = 1.0, metavar = 'SEC')],
    ['-y',             dict(type = int, metavar = 'N')],
    ['-d', '--dryrun', dict(action = 'store_true')],
    ['-x',             dict(action = 'append', nargs = 2)],
    ['-z',             dict(nargs = '+')],
    ['--op',           dict(choices = ACTIONS, help = 'The operation to perform')],
    # ['--1h',           dict()],  # works but you must use getattr(opts, '1h').
)

ap = argparse.ArgumentParser()

for xs in ARG_PARSE_DATA:
    kws = xs.pop()
    ap.add_argument(*xs, **kws)

opts = ap.parse_args()
# opts = ap.parse_known_args()

print(opts)

