import json
import re
import sys
from collections import defaultdict, OrderedDict, Iterable

################
# Classes.
################

# Parser
# Enum
# EnumMember
# RegexLexerError
# OptoPyError
# FormatterConfig
# Section
# GenericParser
# GrammarSpecParser
# Opt
# ParsedOptions
# ParsedOpt
# Phrase
# RegexLexer
# SimpleSpecParser
# Token

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

ZERO_TUPLE = (0, 0)
ONE_TUPLE = (1, 1)
MAX_INT = 999999

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

    VALID_KWARGS = {
        'opts',
        'simple_spec',
        'zero',
        'sections',
        'formatter_config',
        'program',
    }

    def __init__(self, *xs, **kws):

        for k in kws:
            if k not in self.VALID_KWARGS:
                fmt = 'Parser(): invalid keyword argument: {}'
                msg = fmt.format(k)
                raise OptoPyError(msg)

        self.simple_spec      = kws.get('simple_spec', None)
        self.zero             = kws.get('zero', None)
        self.sections         = kws.get('sections', None)
        self.formatter_config = kws.get('formatter_config', FormatterConfig())
        self.program          = kws.get('program', None)

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
            nm : Section(name = nm, label = lab)
            for nm, lab in (
                (SectionName.USAGE, 'Usage'),
                (SectionName.POS, 'Positional arguments'),
                (SectionName.OPT, 'Options'),
            )
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

        # Then sections inferred from the Opt instances.
        # - Either those declared by the user.
        # - Or the default POS or OPT sections.
        for o in self.opts:
            if o.sections:
                for nm in o.sections:
                    all_sections[nm] = Section(name = nm)
            else:
                if o.opt_type == OptType.POS:
                    nm = SectionName.POS
                    all_sections[nm] = default_sections[nm]
                else:
                    nm = SectionName.OPT
                    all_sections[nm] = default_sections[nm]

        ####
        # Validate the section names passed by the caller.
        ####

        invalid = [nm for nm in section_names if nm not in all_sections]
        if invalid:
            fmt = 'Parser.help_text(): invalid sections: {}'
            msg = fmt.format(' '.join(invalid))
            raise OptoPyError(msg)

        ####
        # Setup the sections for which we will build help text.
        ####

        sections = OrderedDict(
            (nm, all_sections[nm])
            for nm in (section_names or all_sections)
        )

        ####
        # Attach Opt instances to those sections.
        ####

        for o in self.opts:
            if o.sections:
                for nm in o.sections:
                    if nm in sections:
                        sections[nm].opts.append(o)
            else:
                nm = SectionName.POS if o.opt_type == OptType.POS else SectionName.OPT
                if nm in sections:
                    sections[nm].opts.append(o)

        ####
        # Assemble the lines of help text.
        ####

        lines = []
        for nm, s in sections.items():

            # Section label.
            lines.append('')
            lines.append(s.label + ':')

            # The usage section.
            if nm is SectionName.USAGE:
                parts = [' ', self.program or 'cli']
                for o in self.opts:
                    parts.append(o.option_spec)
                lines.append(' '.join(map(str, parts)))

            # A Section with literal text.
            elif s.text:
                lines.extend(s.text.split('\n'))

            # Section with Opt instances.
            else:
                for o in s.opts:
                    fmt = '  {:<20} {}'
                    lines.append(fmt.format(o.option_spec, o.text or ''))

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
        self._members = OrderedDict(
            (name, EnumMember(enum_name, name, value))
            for value, name in enumerate(members)
        )
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

    def __init__(self, enum_name, name, value):
        self.enum_name = enum_name
        self.name = name
        self.value = value

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
# Enum instances.
################

OptType         = Enum('OptType', 'LONG', 'SHORT', 'POS', 'WILD')
PhraseType      = Enum('PhraseType', 'OPT', 'POS', 'PHRASE', 'WILD', 'ZONE')
PhraseLogicType = Enum('PhraseLogicType', 'AND', 'OR')
HelpTextStyle   = Enum('HelpTextStyle', 'CLI', 'MAN')
OptTextStyle    = Enum('OptTextStyle', 'CLI', 'MAN')
SectionName     = Enum('SectionName', 'USAGE', 'POS', 'OPT')

################
# Errors.
################

class RegexLexerError(Exception):
    pass

class OptoPyError(Exception):
    pass

################
# FormatterConfig.
################

class FormatterConfig(object):

    DEFAULTS = dict(
        program_name        = '',
        section_label_punct = ':',
        after_section_label = '',
        after_section       = '\n',
        program_summary     = '',
        style               = HelpTextStyle.CLI,
        opt_style           = OptTextStyle.CLI,
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
        return (
            self.name.
            replace('-', ' ').
            replace('_', ' ').
            capitalize() + ' options'
        )

################
# GenericParser.
################

class GenericParser(object):

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.parser_functions = tuple()

    def parse(self):
        elem = True
        while elem:
            for func in self.parser_functions:
                elem = func()
                if elem:
                    yield elem
                    break
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
# GrammarSpecParser.
################

class GrammarSpecParser(object):
    pass

################
# Opt.
################

class Opt(object):

    def __init__(self,
                 option_spec,
                 nargs = ZERO_TUPLE,
                 ntimes = (0, 1),
                 text = None,
                 sections = None,
                 tolerant = False):

        self.option_spec = option_spec
        self.option = option_spec
        self.nargs = nargs
        self.ntimes = ntimes      # Not supported now.
        self.text = text
        self.sections = list(sections or [])
        self.tolerant = tolerant

        if self.option == WILDCARD_OPTION:
            self.destination = None
            self.opt_type = OptType.WILD
        else:
            self.destination = self.option.strip(OPT_SPEC_STRIP_CHARS).replace(OPT_PREFIX, UNDERSCORE)
            self.opt_type = (
                OptType.LONG if self.option.startswith(LONG_OPT_PREFIX) else
                OptType.SHORT if self.option.startswith(SHORT_OPT_PREFIX) else
                OptType.POS
            )

        if self.opt_type == OptType.POS and self.nargs == ZERO_TUPLE:
            self.nargs = ONE_TUPLE

    def __repr__(self):
        fmt = 'Opt({})'
        return fmt.format(self.option)

    @property
    def is_long_opt(self):
        return self.opt_type == OptType.LONG

    @property
    def is_short_opt(self):
        return self.opt_type == OptType.SHORT

    @property
    def is_positional_opt(self):
        return self.opt_type == OptType.POS

    @property
    def is_wildcard_opt(self):
        return self.opt_type == OptType.WILD

    @property
    def nargs(self):
        return self._nargs

    @nargs.setter
    def nargs(self, val):
        self._nargs = self._get_nx_tuple(val, 'nargs')

    @property
    def ntimes(self):
        return self._ntimes

    @ntimes.setter
    def ntimes(self, val):
        self._ntimes = self._get_nx_tuple(val, 'ntimes')

    def _get_nx_tuple(self, val, attr_name):
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
        if m is None or m < 0 or m > n:
            fmt = 'Invalid {}: {}'
            msg = fmt.format(attr_name, val)
            raise OptoPyError(msg)
        else:
            return tup

################
# ParsedOptions.
################

class ParsedOptions(object):

    def __init__(self, opts = None):
        self.parsed_opts = OrderedDict()
        for opt in (opts or []):
            po = ParsedOpt(opt, None)
            self.parsed_opts[opt.destination] = po

    def add_opt(self, opt):
        po = ParsedOpt(opt, None)
        self.parsed_opts[opt.destination] = po

    def del_opt(self, opt):
        del self.parsed_opts[opt.destination]

    def __getitem__(self, destination):
        return self.parsed_opts[destination]

    def __iter__(self):
        # User can iterate directory over the ParsedOpt instances.
        # In addition, because ParsedOpt also defines __iter__(), a
        # ParsedOptions instance can be converted directly to a dict.
        return iter(self.parsed_opts.values())

################
# ParsedOpt.
################

class ParsedOpt(object):

    def __init__(self, opt, value):
        self.destination = opt.destination
        self.opt = opt
        self._values = []

    def __iter__(self):
        tup = (self.destination, self.value)
        return iter(tup)

    def add_value(self, val):
        self._values.append(val)

    @property
    def value(self):
        m, n = self.opt.nargs
        if n > 1:
            return self._values
        elif len(self._values) == 0:
            return None
        else:
            return self._values[0]

    @property
    def requires_args(self):
        m, n = self.opt.nargs
        v = len(self._values)
        return m > v

    @property
    def can_take_args(self):
        m, n = self.opt.nargs
        v = len(self._values)
        return v < n

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

    def parse(self, args):

        # Set up the ParsedOptions that we will return.
        opts = [sph.opt for sph in self.subphrases]
        popts = ParsedOptions(opts = opts)

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
        arg_i = -1
        pos_i = -1
        prev_opt = None
        prev_pos = None
        seen = set()

        # Process the args.
        while True:
            arg_i += 1
            try:
                arg = args[arg_i]
            except IndexError:
                break

            # The arg is an option.
            if arg.startswith('--') or arg.startswith('-'):

                # Make sure we are not expecting an option-arg.
                if prev_opt and popts[prev_opt].requires_args:
                    fmt = 'Found option, but expected option-argument: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Try to find a matching Opt.
                prev_opt = None
                for sph in self.subphrases:
                    if sph.phrase_type == PhraseType.WILD:
                        opt = Opt(arg)
                        popts.add_opt(opt)
                        prev_opt = opt.destination
                        break
                    elif sph.phrase_type == PhraseType.OPT:
                        if sph.opt.option == arg:
                            prev_opt = sph.opt.destination
                            break

                # Failed to find a match.
                if prev_opt is None:
                    fmt = 'Found unexpected option: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Found a match, but we've already seen it.
                if prev_opt in seen:
                    fmt = 'Found repeated option: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Valid Opt.
                seen.add(prev_opt)
                po = popts[prev_opt]
                if po.opt.nargs == ZERO_TUPLE:
                    po.add_value(True)
                continue

            # The arg is not an option, but the previous option
            # can still take opt-args.
            elif prev_opt and popts[prev_opt].can_take_args:
                po = popts[prev_opt]
                po.add_value(arg)
                continue

            # Otherwise, treat the arg as a positional.
            # - Either use the previous positional (if it can take more args).
            # - Or use the next positional (if there is one).
            if prev_pos and popts[prev_pos].can_take_args:
                pass
            else:
                pos_i += 1
                try:
                    prev_pos = pos_opts[pos_i].destination
                except IndexError:
                    prev_pos = None

            # No more positional args are expected.
            if not prev_pos:
                fmt = 'Found unexpected positional argument: {}'
                msg = fmt.format(arg)
                raise OptoPyError(msg)

            # Valid positional.
            po = popts[prev_pos]
            po.add_value(arg)

        # Delete the wildcard Opt from ParsedOptions.
        wild = None
        for po in popts:
            if po.opt.is_wildcard_opt:
                wild = po.opt
                break
        if wild:
            popts.del_opt(wild)

        # Check that all Opt instances got the required nargs.
        for po in popts:
            if po.requires_args:
                fmt = 'Did not get expected N of arguments: {}'
                msg = fmt.format(po.opt.option)
                raise OptoPyError(msg)

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
# SimpleSpecParser.
################

class SimpleSpecParser(GenericParser):

    ####
    #
    # To implement a parser:
    #
    # - Inherit from GenericParser.
    #
    # - Define one or more parser_functions.
    #
    # - Each of those functions should return some data element
    #   appropriate for the grammar (if the current Token matches)
    #   or None.
    #
    ####

    def __init__(self, text):
        lexer = RegexLexer(text, SIMPLE_SPEC_TOKENS)
        super(SimpleSpecParser, self).__init__(lexer)
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
            return Opt(tok.value, nargs = 1)
        else:
            return None

    def _opt(self, opt_type):
        # If the current Token is not the expected option type, bail out.
        # Otherwise, count the N of OPT_ARG that the Opt takes.
        tok = self.eat(opt_type)
        if not tok:
            return None
        opt = Opt(tok.value)
        while tok:
            tok = self.eat(OPT_ARG)
            if tok:
                m, n = opt.nargs
                opt.nargs = (m + 1, n + 1)
        return opt

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

