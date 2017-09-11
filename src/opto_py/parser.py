import sys
import json
import re

from .opt import Opt, MAX_INT, WILDCARD_OPTION
from .simple_spec_parser import SimpleSpecParser
from .phrase import Phrase
from .errors import OptoPyError
from .formatter_config import FormatterConfig, Section

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

    VALID_KWARGS = {
        'opts',
        'simple_spec',
        'zero',
        'sections',
        'formatter_config',
    }

    def __init__(self, *xs, **kws):

        for k in kws:
            if k not in self.VALID_KWARGS:
                fmt = 'Parser(): invalid keyword argument: {}'
                msg = fmt.format(k)
                raise OptoPyError(msg)

        self.simple_spec = kws.get('simple_spec', None)
        self.zero = kws.get('zero', None)
        self.sections = kws.get('sections', None)
        self.formatter_config = kws.get('formatter_config', None)

        if self.simple_spec:
            ssp = SimpleSpecParser(self.simple_spec)
            self.opts = [opt for opt in ssp.parse()]

        else:
            opts = list(xs) + list(kws.get('opts', []))
            self.opts = []
            for x in opts:
                if isinstance(x, Opt):
                    opt = x
                elif isinstance(x, dict):
                    opt = Opt(**x)
                else:
                    fmt = 'Parser(): invalid Opt: must be Opt or dict: {}'
                    msg = fmt.format(x)
                    raise OptoPyError(msg)
                self.opts.append(opt)

    def parse(self, args = None):
        if self.zero:
            self.add_wildcard_opts()
        args = list(sys.argv[1:] if args is None else args)
        return self.do_parse(args)

    def do_parse(self, args):
        subphrases = [Phrase(opt = opt) for opt in self.opts]
        phrase = Phrase(subphrases = subphrases)
        return phrase.parse(args)

    def add_wildcard_opts(self):
        self.opts.extend([
            Opt('<positionals>', nargs = (0, MAX_INT)),
            Opt(WILDCARD_OPTION),
        ])

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

    def help_text(self, *section_names):

        # Get sections.
        # - Either user supplied them.
        # - Or we use defaults.
        default_sections = (
            Section('usage', 'Usage'),
            Section('positionals', 'Positional arguments'),
            Section('opts', 'Options'),
        )

        # Get names of sections for this invocation of help_text().
        # - Either user supplied some.
        # - Or we will use all section names (based on the Sections above).
        if not section_names:
            opt_section_names = set(nm for opt in self.opts for nm in opt.sections)
            section_names = opt_section_names or tuple(s.name for s in default_sections)

        # Create a FormatterConfig instance.
        # - The formatting-config dict supplied by user
        # - The Sections that we are going to use.
        fc_dict = self.formatter_config or {}
        fc = FormatterConfig(**fc_dict)

        return 'Usage: blort\n'

