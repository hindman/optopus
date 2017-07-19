import sys
import json
import re

PATTERNS = dict(
    simple = dict(
        long_opt   = r'--(\w[\w\-]*)',
        short_opts = r'-(\w+)',
        short_opt  = r'-(\w)',
        opt_arg    = r'([A-Z][A-Z\d]*)',
        pos_arg    = r'\<([\w]+)\>',
    ),
)

PATTERNS['anchored'] = {
    k : r'\A' + v + r'\Z'
    for k, v in PATTERNS['simple'].items()
}


class Parser(object):

    def __init__(self,
                 simple_spec = None,
                 zero = None):
        if simple_spec:
            self.simple_spec = SimpleSpec(simple_spec)
            self.opts = self.simple_spec.opts
        else:
            self.simple_spec = None
            self.opts = {}
        self.zero = bool(
            zero or
            (zero is None and not self.opts)
        )

    def parse(self, args = None):
        if self.zero:
            return self.zero_parse(args)
        else:
            return {}

    def zero_parse(self, args):
        ps = []
        opts = {}
        for a in args:
            k = parse_single_arg('long_opt', a)
            if k:
                opts[k] = True
                continue
            k = parse_single_arg('short_opts', a)
            if k:
                for char in k:
                    opts[char] = True
                continue
            ps.append(a)
        opts['positionals'] = ps
        return opts

def parse_single_arg(patt, arg, hyphens = True, anchored = True, prefix = False):
    k = 'anchored' if anchored else 'simple'
    rgx = re.compile(PATTERNS[k][patt])
    m = rgx.search(arg)
    if m:
        full = m.group(0)
        name = m.group(1)
        if hyphens:
            name = name.replace('-', '_')
        if prefix:
            if patt == 'long_opt':
                name = '--' + name
            elif patt.startswith('short_opt'):
                name = '-' + name
        return name
    else:
        return None

class SimpleSpec(object):

    def __init__(self, spec):
        tokens = self.get_tokens(spec)
        opts = self.get_opts(tokens)
        self.spec = spec
        self.tokens = tokens
        self.opts = opts

    def get_tokens(self, spec):
        toks = []
        ks = ('long_opt', 'short_opt', 'opt_arg', 'pos_arg')
        for i, a in enumerate(spec.split()):
            t = None
            for k in ks:
                name = parse_single_arg(k, a, prefix = True)
                if name:
                    t = (k, name, i)
                    break
            toks.append(t or ('unknown', a, i))
        return toks

    def get_opts(self, tokens):
        i = 0
        len_tokens = len(tokens)
        curr_opt = None
        opts = []
        while i < len_tokens:
            k, name, index = tokens[i]
            if k.endswith('_opt'):
                curr_opt = Opt(option = name)
                opts.append(curr_opt)
            elif k == 'opt_arg':
                curr_opt.nargs += 1
            elif k == 'pos_arg':
                curr_opt = Opt(option = name, nargs = 1)
                opts.append(curr_opt)
                curr_opt = None
            else:
                raise ValueError(tokens[i])
            i += 1
        return opts


class Opt(object):

    def __init__(self,
                 option,
                 nargs = 0,
                 repeatable = False,
                 tolerant = False,
                 required = False):

        opt_type = (
            'long' if option.startswith('--') else
            'short' if option.startswith('-') else
            'positional'
        )

        self.option = option
        self.opt_type = opt_type
        self.nargs = nargs
        self.repeatable = repeatable
        self.tolerant = tolerant
        self.required = required

    def __repr__(self):
        fmt = 'Opt({}, opt_type = {}, nargs = {})'
        return fmt.format(self.option, self.opt_type, self.nargs)

