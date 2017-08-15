import sys
import json
import re

from .opt import Opt
from .simple_spec_parser import SimpleSpecParser
from .phrase import Phrase

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
        self.simple_spec = simple_spec
        self.zero = zero
        self.opts = []

    def do_parse_simple_mode(self, args):
        ssp = SimpleSpecParser(self.simple_spec)
        subphrases = [Phrase(opt = o) for o in ssp.parse()]
        phrase = Phrase(subphrases = subphrases)
        return phrase.parse(args)

    @property
    def zero(self):
        # If user has not set the zero-mode, we infer
        # the mode by the presense or absense of opts.
        # Otherwise, we do what the user asked for.
        if self._zero is None:
            if self.simple_spec or self.opts:
                return False
            else:
                return True
        else:
            return self._zero

    @zero.setter
    def zero(self, val):
        if val is None:
            self._zero = None
        else:
            self._zero = bool(val)

    def parse(self, args = None):
        args = list(args or [])
        if self.zero:
            return self.do_parse_zero_mode(args)
        elif self.simple_spec:
            return self.do_parse_simple_mode(args)
        else:
            return self.do_parse_full_mode(args)

    def do_parse_zero_mode(self, args):
        # TODO: return ParsedOptions, use Phrase, etc.
        positionals = []
        options = {}
        for a in args:
            k = parse_single_arg('long_opt', a)
            if k:
                options[k] = True
                continue
            k = parse_single_arg('short_opts', a)
            if k:
                for char in k:
                    options[char] = True
                continue
            positionals.append(a)
        options['positionals'] = positionals
        return options

    def do_parse_full_mode(self, args):
        # TODO: return ParsedOptions, use Phrase, etc.

        return None

        def is_option(arg):
            return (
                arg.startswith('--') or
                arg.startswith('-')
            )

        opts = {}
        positionals = []

        exp_opts = {
            o.option : o
            for o in self.opts
            if not o.opt_type == o.POSITIONAL
        }
        exp_positionals = [
            o for o in self.opts
            if o.opt_type == o.POSITIONAL
        ]

        rargs = list(reversed(args))
        while rargs:
            a = pop(rargs)

            if is_option(a):
                if a in exp_opts:
                    opt = exp_opts[a]
                    if not opt.repeatable:
                        del exp_opts[a]
                    if opt.nargs:
                        opts[opt.destination] = []
                        for _ in range(0, opt.nargs or 0):
                            if rargs:
                                opts[opt.destination].append(rargs.pop())
                            else:
                                pass
                                # error
                        if opt.nargs == 1:
                            opts[opt.destination] = opts[opt.destination][0]
                    else:
                        opts[opt.destination] = True
                else:
                    pass
                    # error
            else:
                if expected:
                    accectp
                else:
                    pass
                    # error

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

