import sys
import json
import re
from collections import defaultdict, OrderedDict

from .enums import OptType
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

        ####
        # NOTES:
        #
        #   Example usages:
        #
        #   All help-text section, in order.
        #
        #       p.help_text()
        #
        #   Specific help-text sections, in the requested order.
        #
        #       p.help_text('usage')
        #       p.help_text('section-foo')
        #       p.help_text('section-foo', 'section-bar')
        #
        #   Also see misc/examples/help-text.txt : API section.
        ####

        # Set up the default Section instances.
        default_sections = OrderedDict([
            ('_usage', Section(
                name = '_usage',
                label = 'Usage',
                opts = [],
            )),
            ('_positionals', Section(
                name = '_positionals',
                label = 'Positional arguments',
                opts = [o for o in self.opts if o.opt_type == OptType.POS],
            )),
            ('_opts', Section(
                name = '_opts',
                label = 'Options',
                opts = [o for o in self.opts if o.opt_type != OptType.POS],
            )),
        ])

        # Set up the Section instances declared at the parser-level by the user.
        fc_dict = self.formatter_config or {}
        user_sections = OrderedDict([
            (s.name, s)
            for s in fc_dict.get('sections', [])
        ])

        # TODO: I don't want to use the user_sections directly.
        # At the parser level the user will just declare the name and label.
        # Here we need new Section instances, and we need to attach the Opt
        # instances to them.
        #
        # TODO: maybe sects should map names to Section instances, and it
        # could be used directly when we need to assemble the `sections` list.

        # Create a dict mapping all known Section names to their Opt instance.
        # - (a) The defaults.
        # - (b) Those declared by the user at the Parser level.
        # - (c) Those declared by the user at the Opt level.
        sects = defaultdict(list)
        for nm, s in default_sections.items():
            sects[nm].extend(s.opts)
        for nm, s in user_sections.items():
            sects[nm].extend(s.opts)
        for opt in self.opts:
            for s in opt.sections:
                sects[s].append(opt)

        # Determine which section names we are using.
        # - If none are given, use the defaults.
        # - Otherwise, use the names from the user, if valid.
        if not section_names:
            section_names = list(default_sections)
        else:
            for nm in section_names:
                if nm not in sects:
                    fmt = 'Parser.help_text(): invalid section name: {}'
                    msg = fmt.format(nm)
                    raise OptoPyError(msg)

        # Get the Section instances that we will use.
        sections = []
        for nm in section_names:
            if nm in default_sections:
                sections.append(default_sections[nm])
            elif nm in user_sections:
                sections.append(user_sections[nm])
            else:
                label = nm.replace('-', ' ').replace('_', ' ').capitalize() + ' options'
                s = Section(
                    name = nm,
                    label = label,
                    opts = sects[nm],
                )

        return 'Usage: blort\n'

