
import re

from dataclasses import dataclass

from short_con import cons, constants

from .constants import Pmodes, Chars
from .utils import to_repr

####
# Data classes: TokDef and Token.
####

@dataclass
class TokDef:
    # Defines how to find and process a Token.

    # Token kind/name.
    kind: str

    # Regex to match the token.
    regex: re.Pattern

    # Parsing modes that use the Token.
    modes: list[str]

    # Whether the RegexLexer should emit the Token back to the
    # SpecParser (or just consume it and update lexer position).
    emit: bool

    def isa(self, *tds):
        return any(self.kind == td.kind for td in tds)

@dataclass
class Token:

    # Token kind/name.
    kind: str

    # The actual text and the Match object that found it.
    # For Token(eof) and Token(err), m=None.
    text: str
    m: re.Match

    # Width of text, N of lines in it, and indexes of newline chars.
    width: int
    nlines: int
    newlines: list[int]

    # Position of the matched text within the larger corpus.
    # - character index (0-based)
    # - line and column number (1-based; user-facing)
    pos: int
    line: int
    col: int

    # Attributes related to the line on which the Token started:
    # - Indentation of the line, in N of spaces.
    # - Whether Token is the first on the line, other than Token(indent).
    indent: int
    is_first: bool

    def isa(self, *ts):
        return any(self.kind == t.kind for t in ts)

    @property
    def brief(self):
        ks = 'kind text pos line col indent is_first'.split()
        return to_repr(self, *ks)

####
# Helper to define TokDefs.
####

def define_tokdefs():
    # Returns a constants collections of TokDef instances, keyed by kind.

    ####
    # Python regex notes/reminders:
    #     - Non-capturing group | (?:foo)
    #     - Look-ahead          | (?=foo) (?!foo)
    #     - Look-behind         | (?<foo) (?<!foo)
    #     - Multi-line mode     | (?m)
    ####

    ####
    # Helpers to build regex patterns.
    ####

    captured = lambda s: f'({s})'
    wrapped_in = lambda wrap, guts: f'{wrap}{guts}{wrap}'

    ####
    # Regex patterns.
    #
    # Some of these are building blocks in larger patterns.
    # Others are patterns used to define TokDefs.
    ####

    # Letters, digits, and numbers.
    letter_under = r'[A-Za-z_]'
    name_char = r'[A-Za-z0-9_-]'
    glob_char = r'[A-Za-z0-9?*_-]'
    number = r'\d+'

    # Names.
    valid_name = fr'{letter_under}{name_char}*'
    captured_name = captured(valid_name)

    # Brackets.
    paren_open = r'\('
    brack_open = r'\['
    angle_open = '<'
    paren_close = r'\)'
    brack_close = r'\]'
    angle_close = '>'
    paren_open_named = captured(valid_name) + r'=\('
    brack_open_named = captured(valid_name) + r'=\['

    # Whitespace: simple.
    whitespace0 = r'[ \t]*'
    whitespace1 = r'[ \t]+'
    whitespace = whitespace1
    newline = r'\n'

    # Lines.
    start_of_line = '(?m)^'
    end_of_line = fr'{whitespace0}(?=\n)'
    rest_of_line = '.+'

    # Whitespace: other.
    not_whitespace = r'(?=\S)'
    indent = start_of_line + whitespace1 + not_whitespace

    # Special: end of file and error.
    eof = ''
    err = ''

    # Backquotes and the stuff inside of them.
    literal_backslash = r'\\\\'
    literal_backquote1 = r'\\`'
    literal_backquote3 = r'\\```'
    backquote1 = r'`'
    backquote3 = r'```'
    backquote3_no_wrap = r'```!'
    backquote3_comment = r'```#'
    quoted_char1 = r'[^`\t\n]'
    quoted_char3 = r'[^`]'

    # Var-inputs.
    choice_sep = r'\|'
    assign = '='

    # Options and opt-specs.
    option_prefix = '-'
    long_option  = option_prefix + option_prefix + captured_name
    short_option = option_prefix + captured(r'\w')
    opt_spec_sep = ':'

    # Scopes.
    scope_marker = '>>'
    query_elem = fr'{glob_char}+'
    query_path = fr'{query_elem}(?:\.{query_elem})*'
    scope0 = scope_marker
    scope1 = captured(query_path) + wrapped_in(whitespace0, scope_marker)
    opt_spec_scope_empty = scope0
    opt_spec_scope = scope1

    # Section title, heading.
    section_marker = '::' + end_of_line
    heading_marker = ':::' + end_of_line
    heading = captured('.*[^:]') + heading_marker
    section_title = captured('.*[^:]') + section_marker
    scoped_section_title = scope1 + section_title

    # Quantifers.
    triple_dot = r'\.' * 3
    question = r'\?'
    comma_sep = wrapped_in(whitespace0, ',')
    quant_range_guts = wrapped_in(whitespace0, '|'.join((
        number + comma_sep + number,
        number + comma_sep,
        number,
        comma_sep + number,
        comma_sep,
    )))
    quant_range = r'\{' + captured(quant_range_guts) + r'\}'

    # Variants.
    variant_def = captured(valid_name + '!?') + whitespace0 + ':'
    partial_usage = captured_name + '!'

    ####
    # Tuples to define TokDef instances. Each has:
    #
    # - TokDef kind.
    # - Parse-mode abbreviations.
    # - Emit flag.
    ####

    ModeLookup = cons(
        g = Pmodes.grammar,
        h = Pmodes.help_text,
        q = Pmodes.quoted,
    )

    td_tups = [
        # - Quoted.
        ('backquote3_no_wrap',    'g  ', True),
        ('backquote3_comment',    'g  ', True),
        ('backquote3',            'g q', True),
        ('backquote1',            'g q', True),
        ('literal_backslash',     '  q', True),
        ('literal_backquote3',    '  q', True),
        ('literal_backquote1',    '  q', True),
        ('quoted_char1',          '  q', True),
        ('quoted_char3',          '  q', True),
        # - Whitespace.
        ('newline',               'gh ', False),
        ('indent',                'gh ', False),
        ('whitespace',            'gh ', False),
        # - Sections.
        ('scoped_section_title',  'g  ', True),
        ('section_title',         'g  ', True),
        ('heading',               'g  ', True),
        # - Opt-spec scopes.
        ('opt_spec_scope',        'g  ', True),
        ('opt_spec_scope_empty',  'g  ', True),
        # - Parens.
        ('paren_open',            'g  ', True),
        ('brack_open',            'g  ', True),
        ('angle_open',            'g  ', True),
        ('paren_open_named',      'g  ', True),
        ('brack_open_named',      'g  ', True),
        ('paren_close',           'g  ', True),
        ('brack_close',           'g  ', True),
        ('angle_close',           'g  ', True),
        # - Quants.
        ('quant_range',           'g  ', True),
        ('triple_dot',            'g  ', True),
        ('question',              'g  ', True),
        # - Separators.
        ('choice_sep',            'g  ', True),
        ('assign',                'g  ', True),
        ('opt_spec_sep',          'g  ', True),
        # - Options.
        ('long_option',           'g  ', True),
        ('short_option',          'g  ', True),
        # - Variants.
        ('variant_def',           'g  ', True),
        ('partial_usage',         'g  ', True),
        # - Names.
        ('valid_name',            'g  ', True),
        # - Special.
        ('rest_of_line',          ' h ', True),
        ('eof',                   '   ', False),
        ('err',                   '   ', False),
    ]

    ####
    # Create the TokDef instances, then return them
    # as a constants collection.
    ####

    LOCS = locals()
    tds = [
        TokDef(
            kind = kind,
            emit = emit,
            modes = [ModeLookup[a] for a in abbrevs if a.isalpha()],
            regex = re.compile(LOCS[kind]),
        )
        for kind, abbrevs, emit in td_tups
    ]
    return constants({td.kind : td for td in tds})

####
# TokDefs and Rgxs.
####

TokDefs = define_tokdefs()

Rgxs = constants({kind : td.regex for kind, td in TokDefs})

