import sys
import json
import re

LONG_OPT_RGX  = re.compile(r'^--(\w[\w\-]*)$')
SHORT_OPT_RGX = re.compile(r'^-(\w+)$')
OPT_ARG_RGX   = re.compile(r'^([A-Z][A-Z\d]*)$')
POS_ARG_RGX   = re.compile(r'^\<([\w]+)\>$')

class Parser(object):

    def __init__(self,
                 simple_spec = None,
                 zero = None):
        if simple_spec:
            self.simple_spec = simple_spec
            self.opts = ...
        else:
            self.simple_spec = None
            self.opts = []
        self.zero = bool(
            zero or
            (zero is None and not self.opts)
        )

    def parse(self, args = None):
        ps = []
        opts = {}
        for a in args:

            k = parse_long_opt(a)
            if k:
                opts[k] = True
                continue

            k = parse_short_opt(a)
            if k:
                for char in k:
                    opts[char] = True
                continue

            ps.append(a)

        opts['positionals'] = ps
        return opts

def parse_long_opt(a):
    m = LONG_OPT_RGX.search(a)
    if m:
        return m.group(1).replace('-', '_')
    else:
        return None

def parse_short_opt(a):
    m = SHORT_OPT_RGX.search(a)
    if m:
        return tuple(m.group(1))
    else:
        return None

def parse_opt_arg(a):
    m = OPT_ARG_RGX.search(a)
    if m:
        return m.group(1).lower()
    else:
        return None

def parse_pos_arg(a):
    m = POS_ARG_RGX.search(a)
    if m:
        return m.group(1).lower()
    else:
        return None

class SimpleSpec(object):

    def __init__(self, spec):
        self.tokens = self.parse_spec(spec)

    def parse_spec(self, spec):
        toks = []
        for a in spec.split():

            k = parse_long_opt(a)
            if k:
                t = ('long-opt', k)
                toks.append(t)
                continue

            k = parse_short_opt(a)
            if k:
                for char in k:
                    t = ('short-opt', char)
                    toks.append(t)
                continue

            k = parse_opt_arg(a)
            if k:
                t = ('opt-arg', k)
                toks.append(t)
                continue

            k = parse_pos_arg(a)
            if k:
                t = ('pos-arg', k)
                toks.append(t)
                continue

            t = ('unknown', k)
            toks.append(t)

        return toks

