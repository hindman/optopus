import sys
import json
import re

LONG_OPT_RGX  = re.compile(r'^--(\w[\w\-]*)$')
SHORT_OPT_RGX = re.compile(r'^-(\w+)$')

class Parser(object):

    def __init__(self):
        pass

    def parse(self, args = None):
        ps = []
        opts = {}
        for a in args:

            m = LONG_OPT_RGX.search(a)
            if m:
                k = m.group(1).replace('-', '_')
                opts[k] = True
                continue

            m = SHORT_OPT_RGX.search(a)
            if m:
                k = m.group(1)
                for char in k:
                    opts[char] = True
                continue

            ps.append(a)

        opts['positionals'] = ps
        return opts

