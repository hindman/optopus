
import re

from dataclasses import dataclass

from short_con import cons, constants

from .constants import Pmodes
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
    # Building blocks use to assemble larger regex patterns.
    ####

    # Whitespace.
    whitespace0 = r'[ \t]*'
    whitespace1 = r'[ \t]+'
    not_whitespace = r'(?=\S)'

    # Letters, digits, and numbers.
    letter_under = r'[A-Za-z_]'
    name_char = r'[A-Za-z0-9_-]'
    glob_char = r'[A-Za-z0-9?*_-]'
    number = r'\d+'

    # Names.
    valid_name = fr'{letter_under}{name_char}*'
    captured_name = captured(valid_name)

    # Start and end of line.
    start_of_line = '(?m)^'
    end_of_line = fr'{whitespace0}(?=\n)'

    # Backquotes and the stuff inside of them.
    not_backslash = r'(?<!\\)'
    backquote = r'`'
    backquote1 = not_backslash + backquote
    backquote3 = not_backslash + (backquote * 3)
    captured_guts = captured(r'[\s\S]*?')

    # Punctuation.
    option_prefix = '-'
    dot = r'\.'
    comma_sep = wrapped_in(whitespace0, ',')
    section_marker = '::' + end_of_line
    heading_marker = ':::' + end_of_line

    # Scopes.
    scope_marker = '>>'
    query_elem = fr'{glob_char}+'
    query_path = fr'{query_elem}(?:\.{query_elem})*'
    scope0 = scope_marker
    scope1 = captured(query_path) + wrapped_in(whitespace0, scope_marker)

    # Section title, heading.
    section_title = captured('.*[^:]') + section_marker
    heading = captured('.*[^:]') + heading_marker

    # Stuff inside a quantifier range.
    quant_range_guts  = (
        whitespace0 +
        '|'.join((
            number + comma_sep + number,
            number + comma_sep,
            number,
            comma_sep + number,
            comma_sep,
        )) +
        whitespace0
    )

    ####
    # Combos of parsing modes used by the TokDefs.
    ####

    Modes = cons(
        none = [],
        g = [Pmodes.grammar],
        h = [Pmodes.help_text],
        gh = list(Pmodes.values()),
    )

    ####
    # Tuples to define TokDef instances.
    ####

    td_tups = [
        # - Quoted.
        ('quoted_block',          'g ', wrapped_in(backquote3, captured_guts)),
        ('quoted_literal',        'g ', wrapped_in(backquote1, captured_guts)),
        # - Whitespace.
        ('newline',               'gh', r'\n'),
        ('indent',                'gh', start_of_line + whitespace1 + not_whitespace),
        ('whitespace',            'gh', whitespace1),
        # - Sections.
        ('scoped_section_title',  'g ', scope1 + section_title),
        ('section_title',         'g ', section_title),
        ('heading',               'g ', heading),
        # - Opt-spec scopes.
        ('opt_spec_scope',        'g ', scope1),
        ('opt_spec_scope_empty',  'g ', scope0),
        # - Parens.
        ('paren_open',            'g ', r'\('),
        ('brack_open',            'g ', r'\['),
        ('angle_open',            'g ', '<'),
        ('paren_open_named',      'g ', captured(valid_name) + r'=\('),
        ('brack_open_named',      'g ', captured(valid_name) + r'=\['),
        ('paren_close',           'g ', r'\)'),
        ('brack_close',           'g ', r'\]'),
        ('angle_close',           'g ', '>'),
        # - Quants.
        ('quant_range',           'g ', r'\{' + captured(quant_range_guts) + r'\}'),
        ('triple_dot',            'g ', dot * 3),
        ('question',              'g ', r'\?'),
        # - Separators.
        ('choice_sep',            'g ', r'\|'),
        ('assign',                'g ', '='),
        ('opt_spec_sep',          'g ', ':'),
        # - Options.
        ('long_option',           'g ', option_prefix + option_prefix + captured_name),
        ('short_option',          'g ', option_prefix + captured(r'\w')),
        # - Variants.
        ('variant_def',           'g ', captured(valid_name + '!?') + whitespace0 + ':'),
        ('partial_usage',         'g ', captured_name + '!'),
        # - Names.
        ('valid_name',            'g ', valid_name),
        # - Special.
        ('rest_of_line',          ' h', '.+'),
        ('eof',                   '  ', ''),
        ('err',                   '  ', ''),
    ]

    ####
    # Create the TokDef instances, then return them
    # as a constants collection.
    ####

    NO_EMIT = ('newline', 'indent', 'whitespace', 'eof', 'err')

    tds = [
        TokDef(
            kind = kind,
            emit = kind not in NO_EMIT,
            modes = Modes[modes.replace(' ', '') or 'none'],
            regex = re.compile(pattern),
        )
        for kind, modes, pattern in td_tups
    ]

    return constants({td.kind : td for td in tds})

####
# TokDefs and Rgxs.
####

TokDefs = define_tokdefs()

Rgxs = constants({kind : td.regex for kind, td in TokDefs})

