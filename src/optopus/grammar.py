
'''

----
Spec-parsing overview
----

TokDefs and Tokens:

    - These are the atomic entitites of the parsing process:

        Kind         | Example text
        ----------------------------
        long_option  | --foo
        short_option | -x
        newline      | \n
        paren_open   | (
        brack_close  | ]

    - TokDef:
        - Has a kind attribute a regex.
        - Used by RegexLexer to hunt for tokens of interest.

    - Token:
        - Emitted by RegexLexer when it finds a match.
        - Has a kind attribute paralleling the TokDef.
        - Contains the matched text, plus information about the position of
          that match within the larger corpus (line, col, etc).

SpecParser and RegexLexer: overview:

    - The RegexLexer:
        - Works with atomic units: Tokens.
        - Its primary function is get_next_token().

    - The SpecParser:
        - Works with more meaningful grammatical units.
        - Those units are expressed in various parsing functions.
        - Examples:
            - variant()
            - opt_spec()
            - section_title()
            - quoted_block()

        - Parsing functions are hierarchical:
            - Some match large things: eg variants or opt-specs.
            - Others match small things within those larger grammatical
              units: eg, long options, positional, parameters, etc.

        - The spec-syntax requires contextual parsing:
            - The SpecParser uses a mode attribute to manage context.
            - When the mode changes:
                - The parser tells the lexer which TokDefs to search for.
                - The parser changes which parsing functions to call.

            - The parser uses self.handlers to manage contextual parsing:
                - It is a dict mapping each parsing mode to one or more Handler
                  instances.
                - Each Handler holds a parsing function to try and, optionally,
                  and parsing mode to advance to next if that parsing function
                  finds a match.

Spec-parsing: the process:

    - Intialization:
        - SpecParser sets itself up.
        - It creates self.lexer holding a RegexLexer.
        - The RegexLexer is given two things:
            - The text to be processed.
            - A validator function: Lexer.taste() [details below].

    - SpecParser.parse() is invoked:

        - That invocation occurs in two context:
            - Unit tests for SpecParser.
            - By a user: p = Parser(SPEC)

        - The parse() method:
            - Does some preliminary work.
            - Then it calls do_parse().

        - The do_parse() method:
            - This method orchestates the contextual parsing process.
            - It tries relevant Handlers [details below].
            - And it switches parsing mode as needed if a Handler is matched.

    - When do_parse() tries a Handler:
        - It calls the Handler's parsing function.

    - When a parsing function is called:
        - It calls eat(), passing in 1+ TokDefs.
        - Those TokDefs are a subset of the broader list of TokDefs that the
          RegexLexer was given when the parsing mode was set.
        - The eat() method assigns those TokDefs to self.menu.
        - Then it calls RegexLexer.get_next_token().

    - When get_next_token() is called:
        - The lexer tries each TokDef in self.tokdefs.
        - When it finds a match:
            - It creates a Token.
            - It calls self.validator() with that Token.
            - In effect, it says to the SpecParser:
                - I found a Token relevant for the current parsing mode.
                - But is it the right kind, given the current context?

        - The validator function is SpecParser.taste():
            - It first checks whether the matched Token is on self.menu.
            - Then it checks other contextual details related to line
              indentation and start-of-line status.
            - It returns True is all criteria are met.

        - Then get_next_token() reacts to that bool:
            - If True:
                - It updates its own location information (line, col, etc).
                - Returns the Token.
            - If False:
                - It just stores the Token in self.curr.
                - And it returns None.
                - Storing the Token is self.curr is just an optimization:
                    - The next call to get_next_token() will immediately use
                      self.curr rather than checking the self.tokdefs.

    - The parsing function keeps going:
        - A parsing function might need to uses self.eat() multiple times to
          assemble the grammatical entity it is trying to match.
        - It those eat() calls lead down a successful path, it eventually
          returns the relevant ParseElem.
        - Otherwise it returns None.

        * Currently, ParseElem is just a conceptual device representing various
          dataclasses comprising the various grammatical entities. As the
          refactoring moves forward, I might make ParseElem an official base
          class.

'''

####
# Imports.
####

import inspect
import re
import sys

from collections import OrderedDict, Counter
from dataclasses import dataclass, replace as clone
from functools import cache
from short_con import cons, constants

from .errors import OptopusError

####
# Data classes.
####

@dataclass(frozen = True)
class TokDef:
    # Defines how to find and process a Token.

    # Token kind/name.
    kind: str

    # Regex to match the token.
    regex: re.Pattern

    # Parsing modes that use the Token.
    modes: tuple[str]

    # Whether the RegexLexer should emit the Token back to the
    # SpecParser (or just consume it and update lexer position).
    emit: bool

@dataclass(frozen = True)
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
    newlines: tuple[int]

    # Position of the matched text within the larger corpus.
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

@dataclass(frozen = True)
class Prog:
    # TODO: seems unused.
    # Probably not needed with the new spec-syntax.
    name: str

@dataclass(frozen = True)
class Variant:
    name: str
    is_partial: bool
    elems: list

@dataclass(frozen = True)
class OptHelp:
    elems: list[str]
    text: str

@dataclass(frozen = True)
class SectionTitle:
    title: str

@dataclass(frozen = True)
class QuotedBlock:
    text: str

@dataclass(frozen = True)
class QuotedLiteral:
    text: str

@dataclass(frozen = True)
class Quantifier:
    m: int
    n: int
    greedy: bool

@dataclass(frozen = True)
class PartialUsage:
    text: str

@dataclass(frozen = True)
class Parenthesized:
    elems: list
    quantifier: Quantifier

@dataclass(frozen = True)
class Bracketed:
    elems: list
    quantifier: Quantifier

@dataclass(frozen = True)
class SymDest:
    sym: str
    dest: str
    symlit: str
    val: str
    vals: list

@dataclass(frozen = True)
class Positional:
    sym: str
    dest: str
    symlit: str
    choices: list
    quantifier: Quantifier

@dataclass(frozen = True)
class Option:
    dest: str
    params: list
    quantifier: Quantifier

@dataclass(frozen = True)
class ChoiceSep:
    pass

@dataclass(frozen = True)
class PositionalVariant:
    sym: str
    dest: str
    symlit: str
    choice: str

@dataclass(frozen = True)
class Parameter:
    sym: str
    dest: str
    symlit: str
    choices: list

@dataclass(frozen = True)
class ParameterVariant:
    sym: str
    dest: str
    symlit: str
    choice: str

@dataclass(frozen = True)
class Grammar:
    elems: list

    @property
    def pp(self):
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

class Rgxs:
    # TODO:
    # - Make the names of the regex patterns less cryptic.
    # - Pull the patterns in define_tokdefs() into this data as well, so that
    #   function can be simplified to focus purely on TokDef definition.

    '''

    Python regex notes:
        - Non-capturing group: (?:foo)
        - Look-ahead: (?=foo)  (?!foo)
        - Look-behind: (?<foo) (?<!foo)
        - Multi-line mode: (?m)          #  So ^$ match start/end of any line.

    TODO:
        - Can names start with numbers?
        - Why are there RGXS in constants and Rgxs here?
        - When dropping prog, figure out why section_name and prog are
          intertwined in the code.

    '''

    captured = lambda s: f'({s})'
    wrapped_in = lambda wrap, guts: f'{wrap}{guts}{wrap}'

    whitespace0 = r'[ \t]*'
    whitespace1 = r'[ \t]+'
    alphanum  = r'[a-z0-9]'
    alphanum0 = fr'{alphanum}*'
    alphanum1 = fr'{alphanum}+'

    valid_name = fr'{alphanum1}(?:[_-]{alphanum1})*'
    captured_name = captured(valid_name)

    number = r'\d+'
    comma_sep = wrapped_in(whitespace0, ',')
    option_prefix    = '-'


    prog   = fr'{valid_name}(?:\.{alphanum1})?'
    end_of_line    = fr'{whitespace0}(?=\n)'

    not_backslash = r'(?<!\\)'
    backquote = r'`'
    backquote1 = not_backslash + backquote
    backquote3 = not_backslash + (backquote * 3)

    start_of_line   = '(?m)^'

    captured_guts = captured(r'[\s\S]*?')

    not_whitespace = r'(?=\S)'

    section_marker = '::' + end_of_line

    dot = r'\.'
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


    # Rgxs used by TokDefs.
    # - Quoted.
    quoted_block   = wrapped_in(backquote3, captured_guts)
    quoted_literal = wrapped_in(backquote1, captured_guts)
    # - Whitespace.
    newline        =  r'\n'
    indent         = start_of_line + whitespace1 + not_whitespace
    whitespace     = whitespace1
    # - Sections.
    section_name   = captured(prog) + whitespace0 + section_marker
    section_title  = captured('.*') + section_marker
    # - Parens.
    paren_open     =  r'\('
    paren_close    =  r'\)'
    brack_open     =  r'\['
    brack_close    =  r'\]'
    angle_open     =  '<'
    angle_close    =  '>'
    # - Quants.
    quant_range    =  r'\{' + captured(quant_range_guts) + r'\}'
    triple_dot     = dot * 3
    question       =  r'\?'
    # - Separators.
    choice_sep     =  r'\|'
    assign         =  '='
    opt_spec_sep   =  ':'
    # - Options.
    long_option    = option_prefix + option_prefix + captured_name
    short_option   = option_prefix + captured(r'\w')
    # - Variants.
    partial_def    = captured_name + '!' + whitespace0 + ':'
    variant_def    = captured_name + whitespace0 + ':'
    partial_usage  = captured_name + '!'
    # - Sym,           dest.
    sym_dest       = captured_name + wrapped_in(whitespace0, captured('[!.]')) + captured_name
    dot_dest       = dot + whitespace0 + captured_name
    solo_dest      = captured_name + whitespace0 + r'(?=[>=])'
    name           = valid_name
    # - Special.
    rest_of_line   =  '.+'
    eof            =  ''
    err            =  ''

@cache
def define_tokdefs():

    # Combos of parsing modes used by the TokDefs.
    Modes = cons(
        vosh = list(Pmodes.values()),
        vos  = [Pmodes.variant, Pmodes.opt_spec, Pmodes.section],
        os   = [Pmodes.opt_spec, Pmodes.section],
        v    = [Pmodes.variant],
        s    = [Pmodes.section],
        h    = [Pmodes.help_text],
        none = [],
    )

    # Tuples to define TokDefs: kind, emit, and modes.
    td_tups = [
        # - Quoted.
        ('quoted_block',   True,  Modes.s),
        ('quoted_literal', True,  Modes.vos),
        # - Whitespace.
        ('newline',        False, Modes.vosh),
        ('indent',         False, Modes.vosh),
        ('whitespace',     False, Modes.vosh),
        # - Sections.
        ('section_name',   True,  Modes.v),
        ('section_title',  True,  Modes.vos),
        # - Parens.
        ('paren_open',     True,  Modes.vos),
        ('paren_close',    True,  Modes.vos),
        ('brack_open',     True,  Modes.vos),
        ('brack_close',    True,  Modes.vos),
        ('angle_open',     True,  Modes.vos),
        ('angle_close',    True,  Modes.vos),
        # - Quants.
        ('quant_range',    True,  Modes.vos),
        ('triple_dot',     True,  Modes.vos),
        ('question',       True,  Modes.vos),
        # - Separators.
        ('choice_sep',     True,  Modes.vos),
        ('assign',         True,  Modes.vos),
        ('opt_spec_sep',   True,  Modes.os),
        # - Options.
        ('long_option',    True,  Modes.vos),
        ('short_option',   True,  Modes.vos),
        # - Variants.
        ('partial_def',    True,  Modes.v),
        ('variant_def',    True,  Modes.v),
        ('partial_usage',  True,  Modes.v),
        # - Sym,           dest.
        ('sym_dest',       True,  Modes.vos),
        ('dot_dest',       True,  Modes.vos),
        ('solo_dest',      True,  Modes.vos),
        ('name',           True,  Modes.vos),
        # - Special.
        ('rest_of_line',   True,  Modes.h),
        ('eof',            False, Modes.none),
        ('err',            False, Modes.none),
    ]

    # Return a constants collection of TokDefs, keyed by kind.
    return constants({
        kind : TokDef(
            kind = kind,
            emit = emit,
            modes = tuple(modes),
            regex = re.compile(getattr(Rgxs, kind)),
        )
        for kind, emit, modes in td_tups
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

ParenPairs = {
    TokDefs.paren_open: TokDefs.paren_close,
    TokDefs.brack_open: TokDefs.brack_close,
    TokDefs.angle_open: TokDefs.angle_close,
}

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, validator, tokdefs = None, debug = False):
        # Inputs:
        # - Text to be lexed.
        # - Validator function from parser to validate tokens.
        # - TokDefs currently of interest.
        #
        # TODO:
        #   - why is tokdefs a supported arg?
        #   - it's not used here
        #   - for testing only?
        #   - maybe because the SpecParser does set RegexLexer.tokdefs
        #     whenever the parsing-mode changes. So it's contemplated
        #     that a future RegexLexer might want to set them during
        #     creation?
        #
        self.text = text
        self.validator = validator
        self.tokdefs = tokdefs
        self.debug_fh = debug

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
        # Return if we are already done lexing.
        if self.end:
            return self.end

        # Get the next token, either from self.curr or the matcher.
        if self.curr:
            tok = self.curr
            self.curr = None
        else:
            tok = self.match_token()

        # If we got a Token, return either the token or None --
        # the latter if the parser is not happy with it.
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

        # And if we didn't get a token, we have lexed as far as
        # we can. Set the end token and return it.
        #
        # TODO: this is opaque:
        #  - Modify create_token() to handle m = None.
        #  - There is no need for a final re.Match object.
        #
        td = (TokDefs.err, TokDefs.eof)[self.pos > self.maxpos]
        m = re.search('^$', '')
        tok = self.create_token(td, m)
        self.curr = None
        self.end = tok
        self.update_location(tok)
        return tok

    def match_token(self):
        # Starting at self.pos, return the next Token.
        #
        # For non-emitted tokens, we break out of the for-loop,
        # but enter the while-loop again. This allows the lexer
        # to be able to ignore any number of non-emitted tokens
        # on each call of the function.
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

    def create_token(self, tokdef, m):
        # Helper to create Token from a TokDef and a regex Match.
        text = m.group(0)
        newlines = tuple(
            i for i, c in enumerate(text)
            if c == Chars.newline
        )
        return Token(
            kind = tokdef.kind,
            text = text,
            m = m,
            width = len(text),
            pos = self.pos,
            line = self.line,
            col = self.col,
            nlines = len(newlines) + 1,
            isfirst = self.isfirst,
            indent = self.indent,
            newlines = newlines,
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
        self.pos += tok.width
        self.line += tok.nlines - 1
        self.col = (
            tok.width - tok.newlines[-1] if tok.newlines
            else self.col + tok.width
        )

        # Update indent-related info.
        if tok.isa(TokDefs.newline):
            self.indent = 0
            self.isfirst = True
        elif tok.isa(TokDefs.indent):
            self.indent = tok.width
            self.isfirst = True
        else:
            self.isfirst = False

    def debug(self, n_indent, **kws):
        if not self.debug_fh:
            return

        if self.debug_fh is True:
            fh = sys.stdout
        elif self.debug_fh:
            fh = self.debug_fh
        else:
            return


        if not kws:
            print(file = fh)
            return

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

@dataclass(frozen = True)
class Handler:
    method: object
    next_mode: str

class SpecParser:

    def __init__(self, text, debug = False):
        # The text and the lexer.
        self.text = text
        self.debug_fh = debug
        self.lexer = RegexLexer(text, self.taste, debug = debug)

        # Line and indent from the first Token of the top-level
        # ParseElem currently under construction by the parser.
        # And a flag for special indent validation.
        self.line = None
        self.indent = None
        self.allow_second = False

        # Parsing modes. First define the handlers for each mode.
        self.handlers = {
            Pmodes.variant: (
                Handler(self.section_title, Pmodes.section),
                Handler(self.variant, None),
            ),
            Pmodes.opt_spec: (
                Handler(self.section_title, Pmodes.section),
                Handler(self.opt_spec, None),
            ),
            Pmodes.section: (
                Handler(self.quoted_block, None),
                Handler(self.section_title, None),
                Handler(self.opt_spec, None),
            ),
            Pmodes.help_text: tuple(),
        }

        # Set the initial mode (see the setter).
        self.mode = Pmodes.variant

        # Tokens the parser has ever eaten and TokDefs
        # it is currently trying to eat.
        self.eaten = []
        self.menu = None

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
        self.lexer.tokdefs = tuple(
            td for td in TokDefs.values()
            if mode in td.modes
        )

    ####
    # Parse a spec.
    ####

    def parse(self):
        # Determine the parsing mode for the grammar section
        # (opt_spec or variant), and get the program name, if any.
        # Because the first variant can reside on the same line as
        # the program name, we set the allow_second flag.
        lex = self.lexer
        lex.debug(0)
        lex.debug(0, mode_check = 'started')
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

        # Parse everything into a list of ParseElem.
        elems = list(self.do_parse(allow_second))

        # Raise if we did not parse the full text.
        tok = self.lexer.end
        if not (tok and tok.isa(TokDefs.eof)):
            self.error('Failed to parse the full spec')

        # Convert elems to a Grammar.
        return self.build_grammar(prog, elems)

    def do_parse(self, allow_second):
        # Yields top-level ParseElem (those declared in self.handlers).

        # The first OptHelp or SectionTitle must start on new line.
        # That differs from the first Variant, which is allowed
        # to immediately follow the program name, if any.

        self.indent = None
        self.line = None
        self.allow_second = allow_second

        # Emit all ParseElem that we find.
        elem = True
        while elem:
            elem = False
            # Try the handlers until one succeeds. When that occurs,
            # we break from the loop and then re-enter it. If no handlers
            # succeed, we will exit the outer loop.
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
                    break

    def build_grammar(self, prog, elems):
        g = Grammar(elems)

        return g

        '''

        Partition elems on the first SectionTitle:

            gelems : grammar section (all Variant or OptHelp)
            selems : other

        Convert selems into groups, one per section:

            SectionTitle
            0+ QuotedBlock
            0+ OptHelp        # Can be full or mere references.

        At this point, we will have:

            prog : name or None
            variants : 0+
            opthelps : 0+
            sections : 0+

        If no variants:
            If no opthelps:
                - No-config parsing?
                - Or raise?
            Else:
                - Create one Variant from the opthelps.

        Processing a sequence of elems:

            - Applies to Variant, Parenthesized, Bracketed.

            - Organize into groups, partitioning on ChoiceSep.
            - If multiple groups, we will end up with Group(mutext=True)

            ...

        Sections:
            - An ordered list of section-elems.
            - Where each section-elem is: QuotedBlock or Opt-reference.

        '''

        # ParseElem: top-level:
        #     Variant: name is_partial elems
        #     OptHelp: elems text
        #     SectionTitle: title
        #     QuotedBlock: text
        #
        # ParseElem: elems:
        #     ChoiceSep:
        #     QuotedLiteral: text
        #         - Becomes an Opt.
        #         - But has no dest.
        #         - Essentially requires the variant to include a positional constant.
        #         - Does that make it like a PositionalVariant with one choice and no dest or sym?
        #     PartialUsage: name
        #         - Insert the elems from the Variant(partial=True)
        #     Parenthesized: elems quantifier
        #         - Convert to Group or quantified Opt.
        #     Bracketed: elems quantifier
        #         - Convert to Group or quantified Opt.
        #     Option: dest params quantifier
        #     Positional: sym dest symlit choices quantifier
        #     PositionalVariant: sym dest symlit choice
        #     Parameter: sym dest symlit choices
        #     ParameterVariant: sym dest symlit choice
        #
        # ParseElem: subcomponents:
        #     SymDest: sym dest symlit val vals
        #     Quantifier: m n greedy
        #     QuotedLiteral: text

    ####
    # Eat tokens.
    ####

    def eat(self, *tds):
        self.menu = tds
        self.lexer.debug(1, wanted = ','.join(td.kind for td in tds))
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
        # Returns true if the next token from the lexer is the
        # right kind, based on last eat() call, and if it adheres
        # to rules regarding indentation and start-of-line status.
        #
        # - If SpecParser has no indent yet, we are starting a new
        #   top-level ParseElem. So we expect a first-of-line Token.
        #   If so, we remember that token's indent and line.
        #
        # - For subsequent tokens in the expression, we expect tokens
        #   from the same line or a continuation line indented farther
        #   than the first line of the expression.
        #
        if any(tok.isa(td) for td in self.menu):
            if self.indent is None:
                if tok.isfirst or self.allow_second:
                    self.lexer.debug(2, isfirst = True)
                    # HERE_INDENT
                    self.indent = tok.indent
                    self.line = tok.line
                    return True
                else:
                    self.lexer.debug(2, isfirst = False)
                    return False
            else:
                if self.line == tok.line:
                    self.lexer.debug(2, indent_ok = 'line', line = self.line)
                    return True
                elif self.indent < tok.indent:
                    self.lexer.debug(2, indent_ok = 'indent', self_indent = self.indent, tok_indent = tok.indent)
                    # HERE_INDENT
                    # self.line = tok.line
                    return True
                else:
                    self.lexer.debug(2, indent_ok = False, self_indent = self.indent, tok_indent = tok.indent)
                    return False
        else:
            return False

    ####
    # Top-level ParseElem handlers.
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
        return OptHelp(elems, text)

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
    # ParseElem obtained via the elems() helper.
    ####

    def elems(self):
        # TODO:
        # - name is cryptic
        # - what is the theme here?
        #
        # - Shouldn't takes_quantifier be set in each dataclass?
        # - The code using this function speaks of a ParseElem:
        #   - what is that?
        #   - should it be formalized: eg a base dataclass

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

    def choice_sep(self):
        tok = self.eat(TokDefs.choice_sep)
        if tok:
            return ChoiceSep()
        else:
            return None

    def quoted_literal(self):
        tok = self.eat(TokDefs.quoted_literal)
        if tok:
            return QuotedLiteral(text = tok.m.group(1))
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
            vals = tuple(vals)

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
        td_close = ParenPairs[td_open]
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
        lex = self.lexer
        kws.update(
            msg = msg,
            pos = lex.pos,
            line = lex.line,
            col = lex.col,
            current_token = lex.curr.kind if lex.curr else None,
        )
        raise OptopusError(**kws)

    def parse_first(self, *methods):
        elem = None
        for m in methods:
            elem = m()
            if elem:
                break
        return elem

    def parse_some(self, method):
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

