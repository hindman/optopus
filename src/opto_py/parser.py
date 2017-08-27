import sys
import json
import re

from .opt import Opt, MAX_INT, WILDCARD_OPTION
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

    def parse(self, args = None):
        args = list(sys.argv[1:] if args is None else args)
        if self.zero:
            return self.do_parse_zero_mode(args)
        elif self.simple_spec:
            return self.do_parse_simple_mode(args)
        else:
            return self.do_parse_full_mode(args)

    def do_parse_simple_mode(self, args):
        ssp = SimpleSpecParser(self.simple_spec)
        subphrases = [Phrase(opt = opt) for opt in ssp.parse()]
        phrase = Phrase(subphrases = subphrases)
        return phrase.parse(args)

    def do_parse_zero_mode(self, args):
        pos = Opt('<positionals>', nargs = (0, MAX_INT))
        wild = Opt(WILDCARD_OPTION)
        subphrases = [Phrase(opt = opt) for opt in [wild, pos]]
        phrase = Phrase(subphrases = subphrases)
        popts = phrase.parse(args)
        popts.del_opt(wild)
        return popts

    def do_parse_full_mode(self, args):
        # TODO.
        return None

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

