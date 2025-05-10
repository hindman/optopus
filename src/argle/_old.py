
import json
import re
import sys
import textwrap
from collections import defaultdict, OrderedDict
from six.moves.collections_abc import Iterable
from copy import deepcopy
from itertools import product

################
# Constants.
################

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

N_ZERO = 0
N_ONE = 1
N_MAX = 999999

ZERO_TUPLE = (N_ZERO, N_ZERO)
ONE_TUPLE = (N_ONE, N_ONE)
ZERO_OR_ONE_TUPLE = (N_ZERO, N_ONE)
ANY_TUPLE = (N_ZERO, N_MAX)

OPT_PREFIX = '-'
UNDERSCORE = '_'
WILDCARD_OPTION = '*'
LONG_OPT_PREFIX = OPT_PREFIX + OPT_PREFIX
SHORT_OPT_PREFIX = OPT_PREFIX
OPT_SPEC_STRIP_CHARS = OPT_PREFIX + '<>'

# Token types
WHITESPACE = 'WHITESPACE'
LONG_OPT   = 'LONG_OPT'
SHORT_OPT  = 'SHORT_OPT'
POS_OPT    = 'POS_OPT'
OPT_ARG    = 'OPT_ARG'
EOF        = 'EOF'

# Regex components.
PATT_END      = r'(?=\s|$)'
PATT_OPT_CHAR = r'[\w\-]+'

# Token types:
# - The type.
# - Whether the RegexLexer should emit the tokens of this type.
# - The regex to match the token.
# - TODO: should create a TokenType data object.
SIMPLE_SPEC_TOKENS = (
    (WHITESPACE, False, re.compile(r'\s+')),
    (LONG_OPT,   True,  re.compile(r'--' + PATT_OPT_CHAR + PATT_END)),
    (SHORT_OPT,  True,  re.compile(r'-' + PATT_OPT_CHAR + PATT_END)),
    (POS_OPT,    True,  re.compile(r'\<' + PATT_OPT_CHAR + r'\>' + PATT_END)),
    (OPT_ARG,    True,  re.compile(r'[A-Z\d_\-]+' + PATT_END)),
)

################
# Parser.
################

class Parser(object):
    '''
    '''

    VALID_KWARGS = {
        'opts',
        'simple_spec',
        'wildcards',
        'sections',
        'formatter_config',
        'program',
        'add_help',
    }

    def __init__(self, *xs, **kws):
        # This signature is bad for documentation.


        for k in kws:
            if k not in self.VALID_KWARGS:
                fmt = 'Parser(): invalid keyword argument: {}'
                msg = fmt.format(k)
                raise ArgleError(msg)

        self.simple_spec      = kws.get('simple_spec', None)
        self.wildcards        = kws.get('wildcards', None)
        self.sections         = kws.get('sections', None)
        self.formatter_config = kws.get('formatter_config', FormatterConfig())
        self.program          = kws.get('program', None)
        self.add_help         = kws.get('add_help', False)

        if self.simple_spec:
            ssp = SimpleSpecParser(self.simple_spec)
            self.opts = []
            for otok in ssp.parse():
                o = Opt(otok.option_spec)
                o.option = otok.option
                o.nargs = otok.nargs
                o.arg_names = otok.arg_names
                self.opts.append(o)

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
                    raise ArgleError(msg)
                self.opts.append(opt)

        if self.add_help:
            opt = Opt('-h --help', text = 'Print help and exit.', tolerant = True)
            self.opts.append(opt)

        seen = set()
        for o in self.opts:
            nm = o.option
            if nm in seen:
                fmt = 'Parser(): duplicate Opt: {}'
                msg = fmt.format(nm)
                raise ArgleError(msg)
            else:
                seen.add(nm)

    def parse(self, args = None, should_exit = True, alt = False):
        # If given no args, get them from sys.argv.
        args = list(sys.argv[1:] if args is None else args)

        # Add the wildcard Opt instances.
        if self.wildcards:
            self._add_wildcard_opts()

        # Try to parse the args.
        HELP = ('HELP',)
        try:
            if alt:
                popts = self._do_alternative_parse(args)
            else:
                popts = self._do_parse(args)
            if self.add_help and popts['help'].value:
                raise ArgleError(HELP)
            return popts
        except ArgleError as e:
            if should_exit:
                if self.add_help and ('-h' in args or '--help' in args):
                    error_msg = HELP
                else:
                    error_msg = e.args[0]
            else:
                raise

        # If we did not return or raise above, it means an
        # error occurred while parsing, and the user wanted the
        # default behavior: print USAGE and exit.
        if error_msg == HELP:
            txt = self._get_help_text()
            print(txt, end = '')
            sys.exit(ExitCode.PARSE_HELP.code)
        else:
            txt = self._get_help_text(SectionName.USAGE, error_msg = error_msg)
            print(txt, end = '')
            sys.exit(ExitCode.PARSE_FAIL.code)

    def _do_parse(self, args):
        subphrases = [Phrase(opt = opt) for opt in self.opts]
        phrase = Phrase(subphrases = subphrases)
        self.parsed_options = ParsedOptions(opts = self.opts, args = args)
        return phrase.parse(args, parsed_options = self.parsed_options)

    def _do_alternative_parse(self, args):
        subphrases = [Phrase(opt = opt) for opt in self.opts]
        self.phrase = Phrase(subphrases = subphrases)
        self.parsed_options = ParsedOptions(opts = self.opts, args = args)
        return self.phrase.parse(args, parsed_options = self.parsed_options)

    def _add_wildcard_opts(self):
        self.opts.extend([
            Opt('<positionals>', nargs = (N_ZERO, N_MAX)),
            Opt(WILDCARD_OPTION),
        ])

    @property
    def wildcards(self):
        # If user has not set the wildcards-mode, we infer it via the presense
        # or absense of opts. Otherwise, we do what the user asked for.
        if self._wildcards is None:
            if self.simple_spec or self.opts:
                return False
            else:
                return True
        else:
            return self._wildcards

    @wildcards.setter
    def wildcards(self, val):
        if val is None:
            self._wildcards = None
        else:
            self._wildcards = bool(val)

    def help_text(self, *section_names):
        return self._get_help_text(*section_names)

    def _get_help_text(self, *section_names, **kws):

        ####
        #
        # Example usages:
        #
        #   - All help-text sections, in order.
        #
        #     p.help_text()
        #
        #   - Specific help-text sections, in the requested order.
        #
        #     p.help_text('usage')
        #     p.help_text('section-foo')
        #     p.help_text('section-foo', 'section-bar')
        #
        # Sections:
        #   - Declared implicitly via Opt instances.
        #   - Declared explicitly via FormatterConfig.
        #   - Defaults via SectionName.
        #
        # Section ordering:
        #   - SectionName.USAGE [unless declared in FormatterConfig]
        #   - FormatterConfig sections, in order
        #   - SectionName.POS [ditto]
        #   - SectionName.OPT [ditto]
        #
        # Issues:
        #   - Opt lacking sections:
        #       - allocate to SectionName.OPT or SectionName.POS.
        #
        #   - FormatterConfig section lacking matching Opt instances:
        #       - prevent via validation
        #
        # Also see misc/examples/help-text.txt : API section.
        #
        ####

        ####
        # Setup the default sections.
        ####

        default_sections = {
            nm : Section(name = nm, label = nm.label)
            for nm in SectionName
        }

        ####
        # Setup all sections that are eligible for use.
        ####

        # A map of section names to Section instances.
        all_sections = OrderedDict()

        # First the USAGE section, unless the user explicitly
        # declared its position in the FormatterConfig.
        nm = SectionName.USAGE
        if nm not in set(s.name for s in self.formatter_config.sections):
            all_sections[nm] = default_sections[nm]

        # Then any sections declared in FormatterConfig.
        for s in self.formatter_config.sections:
            all_sections[s.name] = s

        # Then sections declared indirectly in Opt instances.
        for o in self.opts:
            for nm in o.sections:
                all_sections[nm] = Section(name = nm)

        # Then the default POS and OPT sections, if there are Opt instances lacking sections.
        homeless = [o for o in self.opts if not o.sections]
        needed = [
            (SectionName.POS, any(o for o in homeless if o.is_positional_opt)),
            (SectionName.OPT, any(o for o in homeless if not o.is_positional_opt)),
        ]
        for nm, has_opts in needed:
            if has_opts and nm not in all_sections:
                all_sections[nm] = default_sections[nm]

        # Then an aliases section.
        if self.formatter_config.alias_style == AliasStyle.SEPARATE:
            if any(o.aliases for o in self.opts):
                nm = SectionName.ALIASES
                all_sections[nm] = default_sections[nm]

        ####
        # Validate the section names passed by the caller.
        ####

        invalid = [nm for nm in section_names if nm not in all_sections]
        if invalid:
            fmt = 'Parser.help_text(): invalid sections: {}'
            msg = fmt.format(' '.join(invalid))
            raise ArgleError(msg)

        ####
        # Setup the sections for which we will build help text.
        ####

        sections = OrderedDict(
            (nm, all_sections[nm])
            for nm in (section_names or all_sections)
        )

        ####
        # Add an errors section, if needed.
        ####

        error_msg = kws.get('error_msg', None)
        if error_msg:
            nm = SectionName.ERR
            s = default_sections[nm]
            s.text = error_msg
            sections[nm] = s

        ####
        # Attach Opt instances to those sections.
        ####

        for o in self.opts:
            if o.sections:
                for nm in o.sections:
                    if nm in sections:
                        sections[nm].opts.append(o)
            else:
                nm = SectionName.POS if o.is_positional_opt else SectionName.OPT
                if nm in sections:
                    sections[nm].opts.append(o)

        ####
        # Assemble the lines of help text.
        ####

        MAX_WID = 80
        lines = []

        for nm, s in sections.items():

            # Section label.
            lines.append('')
            lines.append(s.label + ':')

            # The usage section.
            if nm is SectionName.USAGE:
                parts = []
                for o in self.opts:
                    val = o.option_spec
                    if ' ' in val:
                        fmt = '({})' if o.required else '[{}]'
                        parts.append(fmt.format(val))
                    else:
                        parts.append(val)

                prog = self.program or 'cli'
                wid = MAX_WID - len(prog) - 1
                txt = ' '.join(map(str, parts))
                usage_lines = textwrap.wrap(txt, wid)

                fmt = '  {} {}'
                val = prog
                blank = ' ' * len(prog)
                for i, ln in enumerate(usage_lines):
                    lines.append(fmt.format(val, ln))
                    if i == 0:
                        val = blank

            # Aliases section.
            elif nm is SectionName.ALIASES:
                fmt = '  {} {}'
                for o in self.opts:
                    if o.aliases:
                        val = fmt.format(o.option, ' '.join(o.aliases))
                        lines.append(val)

            # A Section with literal text.
            elif s.text:
                fmt = '  {}'
                txt_lines = s.text.split('\n')
                for ln in txt_lines:
                    lines.append(fmt.format(ln))

            # Section with Opt instances.
            else:
                wid = MAX_WID - 23
                fmt = '  {:<20} {}'
                for o in s.opts:
                    opt_lines = textwrap.wrap(o.text or '', wid) or ['']
                    if self.formatter_config.alias_style == AliasStyle.SEPARATE:
                        val = o.option_spec
                    else:
                        # TODO: sloppy code; clean up.
                        val = o.option_spec
                        rest = ' '.join(val.split()[1:])
                        vals = [val]
                        for a in o.aliases:
                            vals.append('{} {}'.format(a, rest))
                        val = ', '.join(vals)

                    if len(val) > 20:
                        lines.append('  {}'.format(val))
                        val = ''
                    for i, ln in enumerate(opt_lines):
                        lines.append(fmt.format(val, ln))
                        if i == 0:
                            val = ''

        ####
        # Return the help text.
        ####

        lines.append('')
        return '\n'.join(ln.rstrip() for ln in lines)

################
# Enum.
################

class Enum(object):

    def __init__(self, enum_name, *members):
        self._enum_name = enum_name
        self._members = OrderedDict()
        for value, d in enumerate(members):
            if not isinstance(d, dict):
                d = dict(name = d)
            em = EnumMember(enum_name, value = value, **d)
            self._members[d['name']] = em
        self._rmembers = OrderedDict(
            (em.value, em)
            for em in self._members.values()
        )

    def __iter__(self):
        return iter(self._members.values())

    def __getattr__(self, name):
        if name in self._members:
            return self._members[name]
        else:
            raise AttributeError(name)

    def __call__(self, value):
        if value in self._rmembers:
            return self._rmembers[value]
        else:
            raise ValueError(value)

################
# EnumMember.
################

class EnumMember(object):

    def __init__(self, enum_name, name, value, **kws):
        self.enum_name = enum_name
        self.name = name
        self.value = value
        for k, v in kws.items():
            setattr(self, k, v)

    def __str__(self):
        fmt = '{}({}, {!r})'
        msg = fmt.format(self.enum_name, self.name, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.value

################
# Enum instances: user facing.
################

AliasStyle = Enum('AliasStyle', 'SEPARATE', 'MERGED')
HelpTextStyle = Enum('HelpTextStyle', 'CLI', 'MAN')
OptTextStyle = Enum('OptTextStyle', 'CLI', 'MAN')

SectionName = Enum(
    'SectionName',
    dict(name = 'USAGE', label = 'Usage'),
    dict(name = 'POS', label = 'Positional arguments'),
    dict(name = 'OPT', label = 'Options'),
    dict(name = 'ALIASES', label = 'Aliases'),
    dict(name = 'ERR', label = 'Errors'),
)

################
# Enum instances: not user facing.
################

OptType = Enum('OptType', 'LONG', 'SHORT', 'POS', 'WILD')
PhraseLogicType = Enum('PhraseLogicType', 'AND', 'OR')
PhraseType = Enum('PhraseType', 'OPT', 'POS', 'PHRASE', 'WILD', 'ZONE')

ExitCode = Enum(
    'ExitCode',
    dict(name = 'SUCCESS', code = 0),
    dict(name = 'PARSE_HELP', code = 0),
    dict(name = 'PARSE_FAIL', code = 2),
)

################
# Errors.
################

class RegexLexerError(Exception):
    pass

class ArgleError(Exception):
    '''
    '''
    pass

################
# FormatterConfig.
################

class FormatterConfig(object):
    '''
    '''

    DEFAULTS = dict(
        program_name        = '',
        section_label_punct = ':',
        after_section_label = '',
        after_section       = '\n',
        program_summary     = '',
        style               = HelpTextStyle.CLI,
        opt_style           = OptTextStyle.CLI,
        alias_style         = AliasStyle.SEPARATE,
    )

    def __init__(self, *sections, **kws):
        self.sections = sections
        for k, v in self.DEFAULTS.items():
            val = kws.get(k, v)
            setattr(self, k, val)

################
# Section.
################

class Section(object):
    '''
    '''

    def __init__(self, name, label = None, text = None, opts = None):
        self.name = name
        self.label = self._default_label if label is None else label
        self.text = text
        self.opts = opts or []

        # TODO: validation: require either text or opts, and not both.

    def __repr__(self):
        return 'Section({})'.format(self.name)

    @property
    def _default_label(self):
        if isinstance(self.name, EnumMember):
            return self.name.label
        else:
            return (
                self.name.
                replace('-', ' ').
                replace('_', ' ').
                capitalize() + ' options'
            )

################
# GrammarSpecParser.
################

class GrammarSpecParser(object):
    pass

################
# Opt.
################

class Opt(object):
    '''
    '''

    def __init__(self,
                 option_spec,
                 nargs = None,
                 ntimes = None,
                 required = None,
                 text = None,
                 sections = None,
                 aliases = None,
                 tolerant = False):

        if option_spec == WILDCARD_OPTION:
            self.option_spec = option_spec
            self.option = option_spec
            self.nargs = nargs or ZERO_TUPLE
            self.destination = None
            self._opt_type = OptType.WILD

        else:
            # Try to parse the option_spec.
            try:
                # TODO: validation. The last OptToken is authoritative.
                # Elements 0..-1 are used only for aliases.
                opts = list(SimpleSpecParser(option_spec).parse())
                assert opts
                otok = opts[-1]
                otok.aliases = [otok.option for otok in opts]
                otok.aliases.pop()
            except (RegexLexerError, AssertionError) as e:
                otok = None

            # Raise if we did not get an OptToken.
            if otok is None:
                fmt = 'Opt: invalid option_spec: {}'
                msg = fmt.format(option_spec)
                raise ArgleError(msg)

            # Assign values from the OptToken to the Opt.
            self.option_spec = otok.option_spec
            self.option = otok.option
            self.nargs = nargs or otok.nargs
            self.arg_names = otok.arg_names
            self.aliases = otok.aliases + (aliases or [])

            # Determine the OptType.
            self.destination = self.option.strip(OPT_SPEC_STRIP_CHARS).replace(OPT_PREFIX, UNDERSCORE)
            self._opt_type = (
                OptType.LONG if self.option.startswith(LONG_OPT_PREFIX) else
                OptType.SHORT if self.option.startswith(SHORT_OPT_PREFIX) else
                OptType.POS
            )

        # Set self.ntimes.
        if required is not None and ntimes is not None:
            msg = 'Opt: do not set both required and ntimes'
            raise ArgleError(msg)
        elif ntimes is not None:
            # If ntimes was given, just set it.
            self.ntimes = ntimes
        elif required is not None:
            # If required was given, use it to set ntimes.
            v0 = N_ONE if required else N_ZERO
            v1 = N_MAX if self.is_wildcard_opt else N_ONE
            self.ntimes = (v0, v1)
        else:
            # Neither was given, so use the defaults.
            self.ntimes = (
                ONE_TUPLE if self.is_positional_opt else
                ANY_TUPLE if self.is_wildcard_opt else
                ZERO_OR_ONE_TUPLE
            )

        self.text = text
        self.sections = list(sections or [])
        self.tolerant = tolerant

    def _concrete_opts(self):

        # TODO: this isn't correct. The cross-product does not make sense at
        # the Opt-level. Rather, it must be done from the top level -- the full
        # cross product of all possibilities (including those where an Opt
        # might appear ntimes=0, which isn't a valid Opt).

        xs = list(range(self.nargs[0], self.nargs[1] + 1))
        ys = list(range(self.ntimes[0], self.ntimes[1] + 1))
        zs = self.aliases or [self.option]

        for nargs, ntimes, option in product(xs, ys, zs):

            if ntimes:
                o = Opt(
                     option,
                     nargs = nargs,
                     ntimes = ntimes,
                     text = self.text,
                     sections = self.sections,
                )

    def __str__(self):
        fmt = 'Opt({})'
        return fmt.format(self.option)

    def __repr__(self):
        return self.__str__()

    @property
    def is_long_opt(self):
        return self._opt_type == OptType.LONG

    @property
    def is_short_opt(self):
        return self._opt_type == OptType.SHORT

    @property
    def is_positional_opt(self):
        return self._opt_type == OptType.POS

    @property
    def is_wildcard_opt(self):
        return self._opt_type == OptType.WILD

    @property
    def nargs(self):
        return self._nargs

    @nargs.setter
    def nargs(self, val):
        self._nargs = self._get_ntuple(val, 'nargs')

    @property
    def ntimes(self):
        return self._ntimes

    @ntimes.setter
    def ntimes(self, val):
        self._ntimes = self._get_ntuple(val, 'ntimes')

    @property
    def required(self):
        return self.ntimes[0] > N_ZERO

    def _get_ntuple(self, val, attr_name):
        #
        # Convert val to a tuple. For example, these are
        # valid inputs: (0, 1), (1, 1), 1, 2, etc.
        if isinstance(val, Iterable):
            tup = tuple(val)
        else:
            tup = (val, val)
        #
        # Get m, n values from the tuple.
        try:
            m, n = map(int, tup)
        except Exception:
            m, n = (None, None)
        #
        # Return the valid tuple or raise.
        invalids = [
            m is None,
            n is None,
            m < N_ZERO,
            n < m,
            (n == N_ZERO and attr_name == 'ntimes'),
        ]
        if any(invalids):
            fmt = 'Invalid {}: {}'
            msg = fmt.format(attr_name, val)
            raise ArgleError(msg)
        else:
            return tup

################
# ParsedOptions.
################

class ParsedOptions(object):
    '''
    '''

    def __init__(self, opts = None, args = None):
        self.parsed_opts = OrderedDict()
        self.args_index = -1
        self.args = args
        for opt in (opts or []):
            po = ParsedOpt(opt, None)
            self.parsed_opts[opt.destination] = po

    def _add_opt(self, opt):
        po = ParsedOpt(opt, None)
        self.parsed_opts[opt.destination] = po

    def _del_opt(self, opt):
        del self.parsed_opts[opt.destination]

    def __getattr__(self, a):
        if a in self.parsed_opts:
            return self.parsed_opts[a].value
        else:
            raise AttributeError(a)

    def __getitem__(self, destination):
        return self.parsed_opts[destination]

    def __iter__(self):
        # User can iterate directory over the ParsedOpt instances.
        # In addition, because ParsedOpt also defines __iter__(), a
        # ParsedOptions instance can be converted directly to a dict.
        return iter(self.parsed_opts.values())

    def _dump(self):
        return dict(
            args = self.args,
            args_index = self.args_index,
            parsed_opts = dict(self),
            parsed_opts_raw = {
                dest : po._values
                for dest, po in self.parsed_opts.items()
            },
        )

################
# ParsedOpt.
################

class ParsedOpt(object):
    '''
    '''

    def __init__(self, opt, value):
        self.destination = opt.destination
        self.opt = opt
        self._values = []

    def __iter__(self):
        tup = (self.destination, self.value)
        return iter(tup)

    def _add_occurrence(self):
        self._values.append([])

    def _add_value(self, val):
        try:
            assert self._values
            vs = self._values[-1]
            assert isinstance(vs, list)
            vs.append(val)
        except AssertionError:
            msg = 'ParsedOpt: cannot _add_value() without any occurrences'
            raise ArgleError(msg)

    @property
    def value(self):
        # Setup.
        mt, nt = self.opt.ntimes
        ma, na = self.opt.nargs
        vs = self._values
        # Multiple ntimes and nargs: return a 2D list.
        if nt > 1 and na > 1:
            return vs or None
        # Multiple ntimes. Return a flat list.
        elif nt > 1:
            return [xs[0] for xs in vs] if vs else None
        # Multiple nargs. Return a flat list.
        elif nt > 1 or na > 1:
            return vs[0] if vs else None
        # Dual option (flag or take a single arg). Return flat list, so that the
        # user can distinguish option-not-given (None) from no-args (empty list).
        elif self.opt.nargs == ZERO_OR_ONE_TUPLE:
            return vs[0] if vs else None
        # Single ntimes and simple option (flag or single-arg). Just return a value.
        else:
            if vs:
                xs = vs[0]
                return xs[0] if xs else None
            else:
                return None

    @property
    def _requires_occurrences(self):
        vs = self._values
        mt, nt = self.opt.ntimes
        n = len(vs)
        return n < mt

    @property
    def _can_occur_again(self):
        vs = self._values
        mt, nt = self.opt.ntimes
        n = len(vs)
        return n < nt

    @property
    def _requires_args(self):
        vs = self._values
        if vs:
            xs = vs[-1]
            ma, na = self.opt.nargs
            n = len(xs)
            return ma > n
        else:
            msg = 'ParsedOpt: cannot _requires_args() without any occurrences'
            raise ArgleError(msg)

    @property
    def _can_take_args(self):
        vs = self._values
        if vs:
            xs = vs[-1]
            ma, na = self.opt.nargs
            n = len(xs)
            return n < na
        else:
            msg = 'ParsedOpt: cannot _can_take_args() without any occurrences'
            raise ArgleError(msg)

    def __str__(self):
        fmt = 'ParsedOpt({}, {!r})'
        msg = fmt.format(self.destination, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

################
# Phrase.
################

class Phrase(object):

    def __init__(self,
                 subphrases = None,
                 opt = None):
        self.subphrases = subphrases or []
        self.opt = opt

    def __str__(self):
        if self.opt:
            fmt = '{}'
            return fmt.format(self.opt)
        else:
            fmt = 'Phrase({})'
            return fmt.format(self.subphrases)

    def __repr__(self):
        return self.__str__()

    @property
    def phrase_type(self):
        if self.opt is None:
            return PhraseType.PHRASE
        elif self.opt.is_wildcard_opt:
            return PhraseType.WILD
        elif self.opt.is_positional_opt:
            return PhraseType.POS
        else:
            return PhraseType.OPT

    def parse(self, args, parsed_options = None):

        # Set up the ParsedOptions that we will return.
        if parsed_options is None:
            opts = [sph.opt for sph in self.subphrases]
            popts = ParsedOptions(opts = opts)
        else:
            popts = parsed_options

        # The expected positional Opt instances.
        pos_opts = [
            sph.opt
            for sph in self.subphrases
            if sph.phrase_type == PhraseType.POS
        ]

        # Bookkeeping variables.
        # - Indexes to args and pos_opts.
        # - The most recently seen Opt (non-positional).
        # - A set of already seen Opt.destination values.
        pos_i = -1
        prev_opt = None
        prev_pos = None
        seen = set()

        # Process the args.
        while True:
            popts.args_index += 1
            try:
                arg = args[popts.args_index]
            except IndexError:
                break

            # The arg is an option.
            if arg.startswith('--') or arg.startswith('-'):

                # Make sure we are not expecting an option-arg.
                if prev_opt and popts[prev_opt]._requires_args:
                    fmt = 'Found option, but expected option-argument: {}'
                    msg = fmt.format(arg)
                    raise ArgleError(msg)

                # Try to find a matching Opt.
                prev_opt = None
                for sph in self.subphrases:
                    if sph.phrase_type == PhraseType.OPT:
                        if sph.opt.option == arg or arg in sph.opt.aliases:
                            prev_opt = sph.opt.destination
                            break
                    elif sph.phrase_type == PhraseType.WILD:
                        opt = Opt(arg)
                        popts._add_opt(opt)
                        prev_opt = opt.destination
                        break

                # Failed to find a match.
                if prev_opt is None:
                    fmt = 'Found unexpected option: {}'
                    msg = fmt.format(arg)
                    raise ArgleError(msg)

                # Found a match, but we've already seen it.
                if prev_opt in seen:
                    fmt = 'Found repeated option: {}'
                    msg = fmt.format(arg)
                    raise ArgleError(msg)

                # Valid Opt.
                seen.add(prev_opt)
                po = popts[prev_opt]
                po._add_occurrence()
                if po.opt.nargs == ZERO_TUPLE:
                    po._add_value(True)
                continue

            # The arg is not an option, but the previous option
            # can still take opt-args.
            elif prev_opt and popts[prev_opt]._can_take_args:
                po = popts[prev_opt]
                po._add_value(arg)
                continue

            # Otherwise, treat the arg as a positional.
            # - Either use the previous positional (if it can take more args).
            # - Or use the next positional (if there is one).
            if prev_pos and popts[prev_pos]._can_take_args:
                po = popts[prev_pos]
            else:
                pos_i += 1
                try:
                    prev_pos = pos_opts[pos_i].destination
                    po = popts[prev_pos]
                    po._add_occurrence()
                except IndexError:
                    prev_pos = None

            # No more positional args are expected.
            if not prev_pos:
                fmt = 'Found unexpected positional argument: {}'
                msg = fmt.format(arg)
                raise ArgleError(msg)

            # Valid positional.
            po._add_value(arg)

        # Delete the wildcard Opt from ParsedOptions.
        wild = None
        for po in popts:
            if po.opt.is_wildcard_opt:
                wild = po.opt
                break
        if wild:
            popts._del_opt(wild)

        # Check that all Opt instances occurred the required ntimes.
        problems = sorted(po.opt.option for po in popts if po._requires_occurrences)
        if problems:
            fmt = 'Did not get expected N of occurrences: {}'
            msg = fmt.format(', '.join(problems))
            raise ArgleError(msg)

        # Check that all Opt instances got the required nargs.
        problems = sorted(po.opt.option for po in popts if po._requires_args)
        if problems:
            fmt = 'Did not get expected N of arguments: {}'
            msg = fmt.format(', '.join(problems))
            raise ArgleError(msg)

        # Return the ParsedOptions.
        return popts

################
# RegexLexer.
################

class RegexLexer(object):

    def __init__(self, text, token_types):
        self.text = text
        self.token_types = token_types
        self.pos = 0
        self.max_pos = len(self.text) - 1
        self.is_eof = None

    def get_next_token(self):
        # Starting at self.pos, try to emit the next Token.
        # If we find a valid token, there are two possibilities:
        #
        # - A Token that we should emit: just return it.
        #
        # - A Token that we should suppress: break out of the for-loop,
        #   but try the while-loop again. This will allow the Lexer
        #   to be able to ignore any number of suppressed tokens.
        #
        tok = True
        while tok:
            for tt, emit, rgx in self.token_types:
                tok = self.match_token(rgx, tt)
                if tok:
                    if emit:
                        return tok
                    else:
                        break
        # If we did not return a Token above, we should be
        # at the end of the input text.
        if self.pos > self.max_pos:
            return Token(EOF, None)
        else:
            self.error()

    def match_token(self, rgx, token_type):
        m = rgx.match(self.text, pos = self.pos)
        if m:
            txt = m.group(0)
            self.pos += len(txt)
            return Token(token_type, txt)
        else:
            return None

    def error(self):
        fmt = 'RegexLexerError: pos={}'
        msg = fmt.format(self.pos)
        raise RegexLexerError(msg)

    def __iter__(self):
        self.is_eof = False
        return self

    def __next__(self):
        if self.is_eof:
            raise StopIteration
        else:
            tok = self.get_next_token()
            if tok.isa(EOF):
                self.is_eof = True
            return tok

################
# GenericParserMixin.
################

class GenericParserMixin(object):

    def parse(self):
        # Setup: have the lexer get the first token.
        self.current_token = self.lexer.get_next_token()
        elem = True
        # Consume and yield as many tokens as we can.
        while elem:
            for func in self.parser_functions:
                elem = func()
                if elem:
                    yield elem
                    break
        # We expect EOF as the final token.
        if not self.current_token.isa(EOF):
            self.error()

    def eat(self, token_type):
        # If the current Token is of the expected type, return it
        # after advancing the lexer. Otherwise, return None.
        tok = self.current_token
        if tok.isa(token_type):
            self.current_token = self.lexer.get_next_token()
            return tok
        else:
            return None

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

################
# SimpleSpecParser.
################

class SimpleSpecParser(GenericParserMixin):

    ####
    #
    # To implement a parser:
    #
    # - Inherit from GenericParserMixin.
    #
    # - Define self.lexer and self.parser_functions.
    #
    # - Each of those functions should return some data element
    #   appropriate for the grammar (if the current Token matches)
    #   or None.
    #
    # Usage example:
    #
    #   txt = '--foo FF GG -x --blort -z Z1 Z2 <q> <r> --debug'
    #   ssp = SimpleSpecParser(txt)
    #   tokens = list(ssp.parse())
    #
    ####

    def __init__(self, text):
        self.lexer = RegexLexer(text, SIMPLE_SPEC_TOKENS)
        self.parser_functions = (
            self.long_opt,
            self.short_opt,
            self.pos_opt,
        )

    def long_opt(self):
        return self._opt(LONG_OPT)

    def short_opt(self):
        return self._opt(SHORT_OPT)

    def pos_opt(self):
        tok = self.eat(POS_OPT)
        if tok:
            otok = OptToken()
            otok.option = tok.value
            otok.option_spec = tok.value
            otok.nargs = ONE_TUPLE
            otok.opt_type = OptType.POS
            otok.arg_names = []
            return otok
        else:
            return None

    def _opt(self, opt_type):
        # If the current Token is not the expected option type, bail out.
        # Otherwise, count the N of OPT_ARG that the OptToken takes.
        tok = self.eat(opt_type)
        if not tok:
            return None
        otok = OptToken()
        otok.option = tok.value
        otok.option_spec = tok.value
        otok.nargs = ZERO_TUPLE
        otok.opt_type = OptType.SHORT if opt_type == SHORT_OPT else OptType.LONG
        otok.arg_names = []
        while tok:
            tok = self.eat(OPT_ARG)
            if tok:
                m, n = otok.nargs
                otok.nargs = (m + 1, n + 1)
                otok.arg_names.append(tok.value)
                otok.option_spec += ' {}'.format(tok.value)
        return otok

################
# Token.
################

class Token(object):

    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def isa(self, *types):
        return self.token_type in types

    def __str__(self):
        fmt = 'Token({}, {!r})'
        msg = fmt.format(self.token_type, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

class OptToken(object):

    def __repr__(self):
        fmt = 'OptToken({})'
        return fmt.format(self.option)

################
# Helpers.
################

################
# Temporary stuff.
################

def dump_em(xs):
    print('\n')
    for x in xs:
        dump(*x, tight = True)
    print('\n')

def dump(x, label = None, tight = False):
    if not tight:
        print('\n')
    if label:
        print(label, '=>', x)
    else:
        print(x)
    if not tight:
        print('\n')

def jdump(d):
    print(json.dumps(d, indent = 4))


