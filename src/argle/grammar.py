
################################
# OLD FILE -- DO NOT EDIT
################################

####
# Imports.
####

import inspect
import re
import sys

from collections import Counter
from dataclasses import dataclass, replace as clone
from short_con import cons, constants

from .errors import ArgleError

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
    # - line and column number (1-based)
    pos: int
    line: int
    col: int

    # Attributes related to the line on which the Token started:
    # - Indentation of the line, in N of spaces.
    # - Whether Token is the first on the line, other than Token(indent).
    indent: int
    isfirst: bool

    def isa(self, *tds):
        return any(self.kind == td.kind for td in tds)

####
#
# Data classes: ParseElems.
#
# These are intermediate objects used during spec-parsing.
# They are not user-facing and they do not end up as elements
# within the ultimate Grammar returned by SpecParser.parser().
#
####

@dataclass
class ParseElem:
    # Just a base class, mostly as a device for terminology.
    pass

@dataclass
class Variant(ParseElem):
    name: str
    is_partial: bool
    elems: list

@dataclass
class OptSpec(ParseElem):
    elems: list[str]
    text: str

@dataclass
class SectionTitle(ParseElem):
    title: str

@dataclass
class QuotedBlock(ParseElem):
    text: str

@dataclass
class QuotedLiteral(ParseElem):
    text: str

@dataclass
class Quantifier(ParseElem):
    m: int
    n: int
    greedy: bool

@dataclass
class PartialUsage(ParseElem):
    text: str

@dataclass
class Parenthesized(ParseElem):
    elems: list
    quantifier: Quantifier

@dataclass
class Bracketed(ParseElem):
    elems: list
    quantifier: Quantifier

@dataclass
class SymDest(ParseElem):
    sym: str
    dest: str
    symlit: str
    val: str
    vals: list

@dataclass
class Positional(ParseElem):
    sym: str
    dest: str
    symlit: str
    choices: list
    quantifier: Quantifier

@dataclass
class Option(ParseElem):
    dest: str
    params: list
    quantifier: Quantifier

@dataclass
class ChoiceSep(ParseElem):
    pass

@dataclass
class PositionalVariant(ParseElem):
    sym: str
    dest: str
    symlit: str
    choice: str

@dataclass
class Parameter(ParseElem):
    sym: str
    dest: str
    symlit: str
    choices: list

@dataclass
class ParameterVariant(ParseElem):
    sym: str
    dest: str
    symlit: str
    choice: str

####
# Grammar.
####

@dataclass
class Grammar:
    elems: list

    @property
    def pp(self):
        # Return the Grammar as pretty-printable text.
        return '\n'.join(Grammar.pp_gen(self))

    @staticmethod
    def pp_gen(elem, level = 0):
        # Setup.
        cls_name = elem.__class__.__name__
        indent1 = '    ' * level
        indent2 = '    ' * (level + 1)
        has_child_elems = ('elems', 'params')

        # Start with the class of the current element.
        yield f'{indent1}{cls_name}('

        # Then basic attributes.
        for attr, v in elem.__dict__.items():
            if attr not in has_child_elems:
                yield f'{indent2}{attr} = {v!r}'

        # Then recurse to child elements.
        for attr in has_child_elems:
            for child in getattr(elem, attr, []):
                yield from Grammar.pp_gen(child, level + 1)

####
# Functions to return constants collections.
####

def define_tokdefs():
    # Returns a constants collections of TokDef instances keyed, by kind.

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
    alphanum = r'[a-z0-9]'
    alphanum0 = fr'{alphanum}*'
    alphanum1 = fr'{alphanum}+'
    number = r'\d+'

    # Valid names.
    valid_name = fr'{alphanum1}(?:[_-]{alphanum1})*'
    captured_name = captured(valid_name)
    prog = fr'{valid_name}(?:\.{alphanum1})?'
    full_sym_dest = captured_name + wrapped_in(whitespace0, captured('[!.]')) + captured_name

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
        vosh = list(Pmodes.values()),
        vos  = [Pmodes.variant, Pmodes.opt_spec, Pmodes.section],
        os   = [Pmodes.opt_spec, Pmodes.section],
        v    = [Pmodes.variant],
        s    = [Pmodes.section],
        h    = [Pmodes.help_text],
        none = [],
    )

    ####
    # Tuples to define TokDef instances.
    ####

    td_tups = [
        # - Quoted.
        ('quoted_block',   '  s ', wrapped_in(backquote3, captured_guts)),
        ('quoted_literal', 'vos ', wrapped_in(backquote1, captured_guts)),
        # - Whitespace.
        ('newline',        'vosh', r'\n'),
        ('indent',         'vosh', start_of_line + whitespace1 + not_whitespace),
        ('whitespace',     'vosh', whitespace1),
        # - Sections.
        ('section_name',   'v   ', captured(prog) + whitespace0 + section_marker),
        ('section_title',  'vos ', captured('.*') + section_marker),
        # - Parens.
        ('paren_open',     'vos ', r'\('),
        ('paren_close',    'vos ', r'\)'),
        ('brack_open',     'vos ', r'\['),
        ('brack_close',    'vos ', r'\]'),
        ('angle_open',     'vos ', '<'),
        ('angle_close',    'vos ', '>'),
        # - Quants.
        ('quant_range',    'vos ', r'\{' + captured(quant_range_guts) + r'\}'),
        ('triple_dot',     'vos ', dot * 3),
        ('question',       'vos ', r'\?'),
        # - Separators.
        ('choice_sep',     'vos ', r'\|'),
        ('assign',         'vos ', '='),
        ('opt_spec_sep',   ' os ', ':'),
        # - Options.
        ('long_option',    'vos ', option_prefix + option_prefix + captured_name),
        ('short_option',   'vos ', option_prefix + captured(r'\w')),
        # - Variants.
        ('partial_def',    'v   ', captured_name + '!' + whitespace0 + ':'),
        ('variant_def',    'v   ', captured_name + whitespace0 + ':'),
        ('partial_usage',  'v   ', captured_name + '!'),
        # - Sym, dest.
        ('sym_dest',       'vos ', full_sym_dest),
        ('dot_dest',       'vos ', dot + whitespace0 + captured_name),
        ('solo_dest',      'vos ', captured_name + whitespace0 + r'(?=[>=])'),
        ('name',           'vos ', valid_name),
        # - Special.
        ('rest_of_line',   '   h', '.+'),
        ('eof',            '    ', ''),
        ('err',            '    ', ''),
    ]

    # Return the TokDefs constants collections.
    NO_EMIT = ('newline', 'indent', 'whitespace', 'eof', 'err')
    return constants({
        kind : TokDef(
            kind = kind,
            emit = kind not in NO_EMIT,
            modes = Modes[modes.replace(' ', '') or 'none'],
            regex = re.compile(pattern),
        )
        for kind, modes, pattern in td_tups
    })

####
# Parsing and grammar constants.
####

Chars = cons(
    space = ' ',
    newline = '\n',
    exclamation = '!',
    comma = ',',
)

Pmodes = cons('variant opt_spec section help_text')

TokDefs = define_tokdefs()
Rgxs = constants({kind : td.regex for kind, td in TokDefs})

ParenPairs = constants({
    TokDefs.paren_open.kind: TokDefs.paren_close,
    TokDefs.brack_open.kind: TokDefs.brack_close,
    TokDefs.angle_open.kind: TokDefs.angle_close,
})

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, validator, tokdefs = None, debug = False):
        # Text to be lexed.
        self.text = text

        # File handle for debug output.
        self.debug_fh = debug

        # TokDefs currently of interest. Modal parsers can change
        # them when the parsing mode changes.
        self.tokdefs = tokdefs

        # A validation function. Called in get_next_token() to ask the parser
        # whether the matched Token is a kind of immediate of interest.
        self.validator = validator

        # Current token and final token, that latter to be set
        # with Token(eof)/Token(err) when lexing finishes.
        self.curr = None
        self.end = None

        # Location and token information:
        # - pos: character index
        # - line: line number
        # - col: column number
        # - indent: width of most recently read Token(indent).
        # - isfirst: True if next Token is first on line, after any indent.
        self.maxpos = len(self.text) - 1
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.isfirst = True

    @property
    def tokdefs(self):
        return self._tokdefs

    @tokdefs.setter
    def tokdefs(self, tokdefs):
        # If TokDefs are changed, clear any cached Token.
        self._tokdefs = tokdefs
        self.curr = None

    def get_next_token(self):
        # This is the method used by the parser during the parsing process.

        # Return if we are already done lexing.
        if self.end:
            return self.end

        # Get the next token, either from self.curr or the matcher.
        if self.curr:
            tok = self.curr
            self.curr = None
        else:
            tok = self.match_token()

        # If we got a Token, ask the parser's validation function
        # whether to return it or cache it in self.curr.
        # If returned, we update location information.
        if tok:
            self.debug(2, lexed = tok.kind)
            if self.validator(tok):
                self.update_location(tok)
                self.curr = None
                self.debug(2, returned = tok.kind)
                return tok
            else:
                self.curr = tok
                return None

        # If we did not get a token, we have lexed as far as
        # we can. Set the end token and return it.
        done = self.pos > self.maxpos
        td = TokDefs.eof if done else TokDefs.err
        tok = self.create_token(td)
        self.curr = None
        self.end = tok
        self.update_location(tok)
        return tok

    def match_token(self):
        # Starting at self.pos, return the next Token.
        #
        # For non-emitted tokens, we break out of the for-loop, but enter the
        # while-loop again. This allows the lexer to be able to ignore 0+
        # non-emitted tokens on each call of the function.
        tok = True
        while tok:
            tok = None
            for td in self.tokdefs:
                m = td.regex.match(self.text, pos = self.pos)
                if m:
                    tok = self.create_token(td, m)
                    if td.emit:
                        return tok
                    else:
                        self.update_location(tok)
                        break
        return None

    def create_token(self, tokdef, m = None):
        # Helper to create Token from a TokDef and a regex Match.
        text = m.group(0) if m else ''
        newline_indexes = [
            i for i, c in enumerate(text)
            if c == Chars.newline
        ]
        return Token(
            kind = tokdef.kind,
            text = text,
            m = m,
            width = len(text),
            pos = self.pos,
            line = self.line,
            col = self.col,
            nlines = len(newline_indexes) + 1,
            isfirst = self.isfirst,
            indent = self.indent,
            newlines = newline_indexes,
        )

    def update_location(self, tok):
        # Update the lexer's position-related info, given that
        # the parser has accepted the Token.
        #
        # New column location when newlines present:
        #
        #     tok.text      | tok.width | tok.newlines | self.col
        #     ---------------------------------------------------
        #     \n            | 1         | (0,)         | 1
        #     fubb\n        | 5         | (4,)         | 1
        #     fubb\nbar     | 8         | (4,)         | 4
        #     fubb\nbar\n   | 9         | (4,8)        | 1
        #     fubb\nbar\nxy | 11        | (4,8)        | 3
        #

        # Character index, line number, column number.
        self.pos += tok.width
        self.line += tok.nlines - 1
        if tok.newlines:
            # Text straddles multiple lines. New column number
            # is the width of the text on the last line.
            self.col = tok.width - tok.newlines[-1]
        else:
            # Easy case: just add the token's width.
            self.col += tok.width

        # Update the parser's indent-related info.
        if tok.isa(TokDefs.newline):
            self.indent = 0
            self.isfirst = True
        elif tok.isa(TokDefs.indent):
            self.indent = tok.width
            self.isfirst = True
        else:
            self.isfirst = False

    def debug(self, n_indent, **kws):
        # Decided whether and where to send debug output.
        if self.debug_fh is True:
            fh = sys.stdout
        elif self.debug_fh:
            fh = self.debug_fh
        else:
            return

        # Log a blank line if no kws.
        if not kws:
            print(file = fh)
            return

        # Otherwise, assemble the message and log it.
        indent = Chars.space * (n_indent * 4)
        func_name = get_caller_name()
        params = ', '.join(
            f'{k} = {v!r}'
            for k, v in kws.items()
        )
        msg = f'{indent}{func_name}({params})'
        print(msg, file = fh)

####
# SpecParser.
####

@dataclass
class Handler:
    # Data object used by SpecParser to manage transitions
    # from one parsing mode to the next. Holds a top-level
    # parsing function and the next mode to advance to if
    # that function finds a match.
    method: object
    next_mode: str

class SpecParser:

    def __init__(self, text, debug = False):
        # The text, whether/where to emit debug output, and the lexer.
        self.text = text
        self.debug_fh = debug
        self.lexer = RegexLexer(text, self.taste, debug = debug)

        # Line and indent from the first Token of the top-level
        # ParseElem currently under construction by the parser.
        # And a flag for special indent validation.
        self.line = None
        self.indent = None
        self.allow_second = False

        # Parsing modes. Each mode has 0+ handlers to try. If a handler finds a
        # match and if the handler has a next-mode, the parser will advance to
        # the next parsing-mode.
        self.handlers = {
            Pmodes.variant: [
                Handler(self.section_title, Pmodes.section),
                Handler(self.variant, None),
            ],
            Pmodes.opt_spec: [
                Handler(self.section_title, Pmodes.section),
                Handler(self.opt_spec, None),
            ],
            Pmodes.section: [
                Handler(self.quoted_block, None),
                Handler(self.section_title, None),
                Handler(self.opt_spec, None),
            ],
            Pmodes.help_text: [],
        }

        # Set the initial mode, which triggers the setter
        # to tell the RegexLexer which TokDefs to use.
        self.mode = Pmodes.variant

        # TokDefs the parser currently trying to eat: these are a subset of
        # those given to the RegexLexer whenever the parsing mode changes.
        self.menu = None

        # Tokens the parser has ever eaten.
        self.eaten = []

    ####
    # Setting the parser mode.
    ####

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        # When the mode changes, we tell RegexLexer
        # which tokens it should be looking for.
        self._mode = mode
        self.lexer.tokdefs = [
            td
            for td in TokDefs.values()
            if mode in td.modes
        ]

    ####
    # Parse a spec.
    ####

    def parse(self):
        # This is the method used by the Argle argument Parser
        # to parse a SPEC.

        # Setup.
        lex = self.lexer
        lex.debug(0)
        lex.debug(0, mode_check = 'started')

        # Determine the parsing mode for the grammar section
        # (opt_spec or variant), and get the program name, if any.
        #
        # Because the first variant can reside on the same line as
        # the program name, we set the allow_second flag.
        #
        # The TokDef used (section_name) is misleading: at this moment,
        # we are looking for the program name [both use the same regex].
        #
        tok = self.eat(TokDefs.section_name)
        if tok:
            self.mode = Pmodes.opt_spec
            prog = tok.m.group(1)
            allow_second = False
        else:
            self.mode = Pmodes.variant
            tok = self.eat(TokDefs.name)
            prog = tok.text if tok else None
            allow_second = bool(tok)
        lex.debug(0, mode = self.mode)

        # Parse everything else in the SPEC into a list of ParseElem.
        elems = list(self.do_parse(allow_second))

        # Raise if we did not parse the full text.
        tok = self.lexer.end
        if not (tok and tok.isa(TokDefs.eof)):
            self.error('Failed to parse the full spec')

        # Convert elems to a Grammar.
        return self.build_grammar(prog, elems)

    def do_parse(self, allow_second):
        # Yields top-level ParseElem (those declared in self.handlers).

        # The first OptSpec or SectionTitle must start on new line.
        # That differs from the first Variant, which is allowed
        # to immediately follow the program name, if any.
        self.indent = None
        self.line = None
        self.allow_second = allow_second

        # Emit all top-level ParseElem that we find.
        elem = True
        while elem:
            elem = False

            # Try the handlers until one succeeds.
            for h in self.handlers[self.mode]:
                self.lexer.debug(0, handler = h.method.__name__)
                elem = h.method()
                if elem:
                    yield elem

                    # Every subsequent top-level ParseElem must start on a fresh line.
                    self.indent = None
                    self.line = None
                    self.allow_second = False

                    # Advance parser mode, if needed.
                    if h.next_mode:
                        self.mode = h.next_mode

                    # If the handler succeeded, we we break from the
                    # inner-loop but stay in the outer-loop.
                    # That allows us to try all handlers again (in order).
                    break

    def build_grammar(self, prog, elems):
        # Converts the AST-style data generated during self.parse() into
        # a proper Grammar instance.
        g = Grammar(elems)
        return g

    ####
    # Eat tokens.
    ####

    def eat(self, *tds):
        # This is the method used by parsing functions to get another Token.

        # The caller provides 1+ TokDefs, which are put in self.menu.
        self.menu = tds
        self.lexer.debug(1, wanted = ','.join(td.kind for td in tds))

        # Ask the RegexLexer for another Token. That won't succeed unless:
        #
        # - Token is in list of TokDefs appropriate to the parsing mode.
        #
        # - Token is of immediate interest to the parsing function that
        #   called eat(), and thus is in self.menu.
        #
        # - Token satifies other criteria (indentation, etc) checked by
        #   the Token validator function: see self.taste() below.
        #
        tok = self.lexer.get_next_token()
        if tok is None:
            return None
        elif tok.isa(TokDefs.eof, TokDefs.err):
            return None
        else:
            self.lexer.debug(
                2,
                eaten = tok.kind,
                text = tok.text,
                pos = tok.pos,
                line = tok.line,
                col = tok.col,
            )
            self.eaten.append(tok)
            return tok

    def taste(self, tok):
        # This is the Token validator function used by RegexLexer. It checks
        # whether the Token is a kind of immediate interest and whether it
        # satisifes the rules regarding indentation and start-of-line status.

        # The most recent eat() call set the menu to contain the TokDefs of
        # immediate interest. Return false if the current Token does not match.
        if not any(tok.isa(td) for td in self.menu):
            return False

        # If SpecParser has no indent yet, we are starting a new
        # top-level ParseElem and thus expect a first-of-line Token.
        # If so, we remember that token's indent and line.
        if self.indent is None:
            if tok.isfirst or self.allow_second:
                self.lexer.debug(2, isfirst = True)
                self.indent = tok.indent
                self.line = tok.line
                return True
            else:
                self.lexer.debug(2, isfirst = False)
                return False

        # For subsequent tokens in the expression, we expect tokens either from
        # the same line or from a continuation line indented farther than the
        # first line of the expression.
        if self.line == tok.line:
            self.lexer.debug(
                2,
                indent_ok = 'line',
                line = self.line,
            )
            return True
        elif self.indent < tok.indent:
            self.lexer.debug(
                2,
                indent_ok = 'indent',
                self_indent = self.indent,
                tok_indent = tok.indent,
            )
            return True
        else:
            self.lexer.debug(
                2,
                indent_ok = False,
                self_indent = self.indent,
                tok_indent = tok.indent,
            )
            return False

    ####
    # Top-level parsing functions.
    ####

    def variant(self):
        # Get variant/partial name, if any.
        tds = (TokDefs.variant_def, TokDefs.partial_def)
        tok = self.eat(*tds)
        if tok:
            name = tok.text
            is_partial = tok.isa(TokDefs.partial_def)
        else:
            name = None
            is_partial = False

        # Collect the ParseElem for the variant.
        elems = self.elems()
        if name is None and not elems:
            return None
        elif elems:
            return Variant(name, is_partial, elems)
        else:
            self.error('A Variant cannot be empty')

    def opt_spec(self):
        # Try to get elements.
        elems = self.elems()
        if not elems:
            return None

        # Try to get the help text and any continuation lines.
        texts = []
        if self.eat(TokDefs.opt_spec_sep):
            self.mode = Pmodes.help_text
            while True:
                tok = self.eat(TokDefs.rest_of_line)
                if tok:
                    texts.append(tok.text.strip())
                else:
                    break
            self.mode = Pmodes.opt_spec

        # Join text parts and return.
        text = Chars.space.join(t for t in texts if t)
        return OptSpec(elems, text)

    def section_title(self):
        tok = self.eat(TokDefs.section_title, TokDefs.section_name)
        if tok:
            return SectionTitle(title = tok.m.group(1).strip())
        else:
            return None

    def quoted_block(self):
        tok = self.eat(TokDefs.quoted_block)
        if tok:
            return QuotedBlock(text = tok.m.group(1))
        else:
            return None

    ####
    # The elems() helper, which deals with parsing functions
    # shared by variants and opt-specs.
    ####

    def elems(self):
        elems = []
        takes_quantifier = (Parenthesized, Bracketed, Positional, Option)
        while True:
            e = self.parse_first(
                self.quoted_literal,
                self.choice_sep,
                self.partial_usage,
                self.paren_expression,
                self.brack_expression,
                self.positional,
                self.long_option,
                self.short_option,
            )
            if e and isinstance(e, takes_quantifier):
                q = self.quantifier()
                if q:
                    e = clone(e, quantifier = q)
                elems.append(e)
            elif e:
                elems.append(e)
            else:
                break
        return elems

    def quoted_literal(self):
        tok = self.eat(TokDefs.quoted_literal)
        if tok:
            return QuotedLiteral(text = tok.m.group(1))
        else:
            return None

    def choice_sep(self):
        tok = self.eat(TokDefs.choice_sep)
        if tok:
            return ChoiceSep()
        else:
            return None

    def partial_usage(self):
        tok = self.eat(TokDefs.partial_usage)
        if tok:
            return PartialUsage(name = tok.m.group(1))
        else:
            return None

    def paren_expression(self):
        elems = self.parenthesized(TokDefs.paren_open, self.elems)
        if elems:
            return Parenthesized(elems, None)
        else:
            return None

    def brack_expression(self):
        elems = self.parenthesized(TokDefs.brack_open, self.elems)
        if elems:
            return Bracketed(elems, None)
        else:
            return None

    def positional(self):
        # Try to get a SymDest elem.
        sd = self.parenthesized(TokDefs.angle_open, self.symdest, for_pos = True)
        if not sd:
            return None

        # Return Positional or PositionalVariant.
        xs = (sd.sym, sd.dest, sd.symlit)
        if sd.val is None:
            return Positional(*xs, choices = sd.vals, quantifier = None)
        else:
            return PositionalVariant(*xs, choice = sd.val)

    def long_option(self):
        return self.option(TokDefs.long_option)

    def short_option(self):
        return self.option(TokDefs.short_option)

    def option(self, tokdef):
        tok = self.eat(tokdef)
        if tok:
            dest = tok.m.group(1)
            params = self.parse_some(self.parameter)
            return Option(dest, params, None)
        else:
            return None

    def parameter(self):
        # Try to get a SymDest elem.
        sd = self.parenthesized(TokDefs.angle_open, self.symdest, empty_ok = True)
        if not sd:
            return None

        # Return Parameter or ParameterVariant.
        xs = (sd.sym, sd.dest, sd.symlit)
        if sd.val is None:
            return Parameter(*xs, choices = sd.vals)
        else:
            return ParameterVariant(*xs, choice = sd.val)

    def symdest(self, for_pos = False):
        # Try to get sym.dest portion.
        sym = None
        dest = None
        symlit = False
        tok = self.eat(TokDefs.sym_dest, TokDefs.dot_dest, TokDefs.solo_dest)
        if tok:
            if tok.isa(TokDefs.sym_dest):
                # Handle <sym.dest> or <sym!dest>.
                sym = tok.m.group(1)
                symlit = tok.m.group(2) == Chars.exclamation
                dest = tok.m.group(3)
            else:
                # Handle <.dest>, <dest>, <dest=> or <sym>.
                txt = tok.m.group(1)
                if for_pos or tok.isa(TokDefs.dot_dest):
                    dest = txt
                else:
                    sym = txt
        elif for_pos:
            self.error('Positionals require at least a dest')

        # Try to get the dest assign equal-sign.
        # For now, treat this as optional.
        assign = self.eat(TokDefs.assign)

        # Try to get choice values.
        vals = []
        tds = (TokDefs.quoted_literal, TokDefs.name, TokDefs.solo_dest)
        while True:
            tok = self.eat(*tds)
            if not tok:
                break

            # If we got one, and if we already had a sym or dest,
            # the assign equal sign becomes required.
            if (sym or dest) and not assign:
                self.error('Found choice values without required equal sign')

            # Consume and store.
            i = 0 if tok.isa(TokDefs.name) else 1
            vals.append(tok.m.group(i))

            # Continue looping if choice_sep is next.
            if not self.eat(TokDefs.choice_sep):
                break

        # Handle single choice value.
        if len(vals) == 1:
            val = vals[0]
            vals = None
        else:
            val = None
            vals = vals

        # Return.
        return SymDest(sym, dest, symlit, val, vals)

    def quantifier(self):
        q = self.parse_first(self.triple_dot, self.quantifier_range)
        if q:
            m, n = q
            greedy = not self.eat(TokDefs.question)
            return Quantifier(m, n, greedy)
        elif self.eat(TokDefs.question):
            return Quantifier(None, None, False)
        else:
            return None

    def triple_dot(self):
        tok = self.eat(TokDefs.triple_dot)
        return (1, None) if tok else None

    def quantifier_range(self):
        tok = self.eat(TokDefs.quant_range)
        if tok:
            text = TokDefs.whitespace.regex.sub('', tok.m.group(1))
            xs = [
                None if x == '' else int(x)
                for x in text.split(Chars.comma)
            ]
            if len(xs) == 1:
                return (xs[0], xs[0])
            else:
                return (xs[0], xs[1])
        else:
            return None

    def parenthesized(self, td_open, method, empty_ok = False, **kws):
        td_close = ParenPairs[td_open.kind]
        tok = self.eat(td_open)
        if tok:
            elem = method(**kws)
            if not (elem or empty_ok):
                self.error('Empty parenthesized expression')
            elif self.eat(td_close):
                return elem
            else:
                self.error(
                    msg = 'Failed to find closing paren/bracket',
                    expected = td_close,
                )
        else:
            return None

    ####
    # Other stuff.
    ####

    def error(self, msg, **kws):
        # Called when spec-parsing fails.
        # Raises ArgleError with kws, plus position/token info.
        lex = self.lexer
        kws.update(
            msg = msg,
            pos = lex.pos,
            line = lex.line,
            col = lex.col,
            current_token = lex.curr.kind if lex.curr else None,
        )
        raise ArgleError(**kws)

    def parse_first(self, *methods):
        # Takes 1+ parsing functions.
        # Returns the elem from the first that succeeds.
        elem = None
        for m in methods:
            elem = m()
            if elem:
                break
        return elem

    def parse_some(self, method):
        # Takes a parsing function.
        # Collects as many elems as possible and returns them.
        elems = []
        while True:
            e = method()
            if e:
                elems.append(e)
            else:
                break
        return elems

def get_caller_name(offset = 2):
    # Get the name of a calling function.
    x = inspect.currentframe()
    for _ in range(offset):
        x = x.f_back
    x = x.f_code.co_name
    return x

