
'''

----
Parsing the new spec-syntax
----

CURRENT:

    NEXT:

        Brackets data:
            - I think I need an independent BKinds.

    . variant_elems():
        x quoted_literal()
        x choice_sep()
        x partial_usage()
        x any_group()
            x paren_expression()
            x brack_expression()
        - positional()
        - option()

TODO:

    parse(): reset lexer position if variant parsing ends on COLON

Implementation notes:

    - The variant() parsing function will need reset-lexer-position.

    - staging plan:
        - Edit NEW files, while keeping OLD runnable.
        - When ready, swap back (Git history currently in NEW).

----
Notes and questions
----

Entities that must start on a fresh line.
    - variant
    - any-section-title
    - section-content-elem

Parsing modes:
    - variant:
        - initial mode
    - section:
        - any-section-title
        - section-content-elem
            - if we get opt-spec, switch to opt-help-text mode
    - opt-help-text
        - grab rest of line, plus continuations
        - then switch back to section mode

    - Handlers seem unnecessary:
        - Set mode = variant.
        - Try to get variants.
        - Set mode = section.
        - Temporary switch modes as needed to collect opt-help-text.

Which parsing functions having early "overlap"?

    - Example of overlap:

        - Text with four tokens: T1 T2 T3 T4.
        - Two parsing functions: pf1() and pf2()
            - They both can consume T1 and T2.
            - But pf1() will fail upon T3.
            - While pf2() can consume all four.

    - Ways to address the problem:

        - Try the functions in the correct order.
            - In the example, try pf2() first.
            - This can work if there is an unambiguously correct order.

        - In cases where such overlap can occur:
            - Try pf1().
            - If failed, reset lexer position.
            - Try pf2().
            - Could work, but is more complex than relying on ordering.

    - Parsing functions with potential overlap:

        - Overlap 1: variant and opt-spec.

            - This is a known overlap with a lot of planning behind it.
            - Anything that parses as a variant is interpreted that way.

            - The overlap can consist of several tokens.

            - When parsing a variant fails:
                - If the failure occurs on Token(colon-marker).
                - Then the parser has at least two ways to respond:
                    - Reset lexer position and try to parse opt-spec instead.
                    - Forge ahead by somehow using the tokens/elems collected
                      so far to build an opt-spec rather than a variant.
                - The reset approach seems the simpler of the two.

        - Overlap 2: section-title and opt-spec.

            - The overlap is fairly narrow: both can start with a scope.
            - Possible resolution:
                - The scope can be expressed as a single Token.regex.
                - Add another Rgxs entry: Rgx.scope + Rgxs.section_title
            - If that approach works (seems likely), a section title (scoped or
              unscoped) can always be identified in a single token.
            - Hence no overlap issue.

Why not ask specifically for what is on SpecParser.menu?

    - Parser gives lexer a general list of TokDefs whenever the parsing is set.
    - But taste() approves only tokens on the menu.
    - Why bother with the general list in RegexLexer.tokdefs?

        - Allows lexer to handle non-emitted tokens.
        - Relieves parser of the need to pass them in every time, properly
          ordered.

        - But that would be easy to handle inside the parser.
            - Keep the full, ordered list in the parser.
            - Given tds passed to eat(), build an ordered sub-list
              to pass to get_next_token().

        - Provides a caching mechanism:
            - Most parsing modes use most of the tokens.
            - So the cached token is often used.
            - Performance gain probably irrelevant for this project.
            - But caching does seem correct in a textbook way.

----
TODOs, issues, questions
----

The elems() method:

    - A better name for the method?

        - It looks like the method deals with the parts of the grammar shared
          by opt-specs and variants.

        Function           | Top level | Uses elems() | elems()
        -------------------------------------------------------
        variant()          | yes       | yes          | .
        opt_spec()         | yes       | yes          | .
        section_title()    | yes       | .            | .
        quoted_block()     | yes       | .            | .
        -------------------------------------------------------
        quoted_literal()   | .         | .            | yes
        choice_sep()       | .         | .            | yes
        partial_usage()    | .         | .            | yes
        paren_expression() | .         | .            | yes
        brack_expression() | .         | .            | yes
        positional()       | .         | .            | yes
        long_option()      | .         | .            | yes
        short_option()     | .         | .            | yes

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

----
My old notes on converting the AST to a proper Grammar
----

Partition elems on the first SectionTitle:

    gelems : grammar section (all Variant or OptSpec)
    selems : other

Convert selems into groups, one per section:

    SectionTitle
    0+ QuotedBlock
    0+ OptSpec        # Can be full or mere references.

At this point, we will have:

    prog : name or None
    variants : 0+
    optspecs : 0+
    sections : 0+

If no variants:
    If no optspecs:
        - No-config parsing?
        - Or raise?
    Else:
        - Create one Variant from the optspecs.

Processing a sequence of elems:

    - Applies to Variant, Parenthesized, Bracketed.

    - Organize into groups, partitioning on ChoiceSep.
    - If multiple groups, we will end up with Group(mutext=True)

    ...



Sections:
    - An ordered list of section-elems.
    - Where each section-elem is: QuotedBlock or Opt-reference.

ParseElem: top-level:
    Variant: name is_partial elems
    OptSpec: elems text
    SectionTitle: title
    QuotedBlock: text

ParseElem: elems:
    ChoiceSep:
    QuotedLiteral: text
        - Becomes an Opt.
        - But has no dest.
        - Essentially requires the variant to include a positional constant.
        - Does that make it like a PositionalVariant with one choice and no dest or sym?
    PartialUsage: name
        - Insert the elems from the Variant(partial=True)
    Parenthesized: elems quantifier
        - Convert to Group or quantified Opt.
    Bracketed: elems quantifier
        - Convert to Group or quantified Opt.
    Option: dest params quantifier
    Positional: sym dest symlit choices quantifier
    PositionalVariant: sym dest symlit choice
    Parameter: sym dest symlit choices
    ParameterVariant: sym dest symlit choice

ParseElem: subcomponents:
    SymDest: sym dest symlit val vals
    Quantifier: m n greedy
    QuotedLiteral: text

'''

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
    is_first: bool

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
    name: str
    elems: list
    quantifier: Quantifier = None

@dataclass
class Bracketed(ParseElem):
    name: str
    elems: list
    quantifier: Quantifier = None

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
# Other intermediate objects.
####

@dataclass
class Enclosed():
    kind: str
    name: str
    elems: list

@dataclass
class VarInput():
    name: str
    choices: list[str]

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
    alphanum = r'[A-Za-z0-9]'
    alphanum0 = fr'{alphanum}*'
    alphanum1 = fr'{alphanum}+'
    number = r'\d+'

    # Names.
    python_name = fr'{alphanum1}(?:_{alphanum1})*'
    usage_name  = fr'{alphanum1}(?:-{alphanum1})*'
    valid_name = fr'{python_name}|{usage_name}'
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
    scope_marker = '<<'

    # Scope and section title.
    scope = captured(query_path) + wrapped_in(whitespace0, scope_marker)
    section_title = captured('.*') + section_marker

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
        ('quoted_block',          '  s ', wrapped_in(backquote3, captured_guts)),
        ('quoted_literal',        'vos ', wrapped_in(backquote1, captured_guts)),
        # - Whitespace.
        ('newline',               'vosh', r'\n'),
        ('indent',                'vosh', start_of_line + whitespace1 + not_whitespace),
        ('whitespace',            'vosh', whitespace1),
        # - Sections.
        ('scoped_section_title',  'vos ', scope + section_title),
        ('section_title',         'vos ', section_title),
        # - Parens.
        ('paren_open',            'vos ', r'\('),
        ('brack_open',            'vos ', r'\['),
        ('angle_open',            'vos ', '<'),
        ('paren_open_named',      'vos ', captured(valid_name) + r'=\('),
        ('brack_open_named',      'vos ', captured(valid_name) + r'=\['),
        ('paren_close',           'vos ', r'\)'),
        ('brack_close',           'vos ', r'\]'),
        ('angle_close',           'vos ', '>'),
        # - Quants.
        ('quant_range',           'vos ', r'\{' + captured(quant_range_guts) + r'\}'),
        ('triple_dot',            'vos ', dot * 3),
        ('question',              'vos ', r'\?'),
        # - Separators.
        ('choice_sep',            'vos ', r'\|'),
        ('assign',                'vos ', '='),
        ('opt_spec_sep',          ' os ', ':'),
        # - Options.
        ('long_option',           'vos ', option_prefix + option_prefix + captured_name),
        ('short_option',          'vos ', option_prefix + captured(r'\w')),
        # - Variants.
        ('variant_def',           'v   ', captured(valid_name + '!?') + whitespace0 + ':'),
        ('partial_usage',         'v   ', captured_name + '!'),
        # - Sym, dest.
        ('sym_dest',              'vos ', full_sym_dest),
        ('dot_dest',              'vos ', dot + whitespace0 + captured_name),
        ('solo_dest',             'vos ', captured_name + whitespace0 + r'(?=[>=])'),
        ('name',                  'vos ', valid_name),
        ('valid_name',            'vos ', valid_name),
        # - Special.
        ('rest_of_line',          '   h', '.+'),
        ('eof',                   '    ', ''),
        ('err',                   '    ', ''),
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
TDS = TokDefs
Rgxs = constants({kind : td.regex for kind, td in TokDefs})

# Bracket data keyed by the kind of bracketed expression.

def create_bracket_data():
    bs = [
        cons(
            kind = 'round',
            opening = TDS.paren_open,
            closing = TDS.paren_close,
            named = TDS.paren_open_named,
            cls = Parenthesized,
            method_name = 'variant_elems',
        ),
        cons(
            kind = 'square',
            opening = TDS.brack_open,
            closing = TDS.brack_close,
            named = TDS.brack_open_named,
            cls = Bracketed,
            method_name = 'variant_elems',
        ),
        cons(
            kind = 'positional',
            opening = TDS.angle_open,
            closing = TDS.angle_close,
            named = None,
            cls = Positional,
            method_name = 'var_input_elems',
        ),
        cons(
            kind = 'parameter',
            opening = TDS.angle_open,
            closing = TDS.angle_close,
            named = None,
            cls = Parameter,
            method_name = 'var_input_elems',
        ),
    ]
    return constants({b.kind : b for b in bs})

Brackets = create_bracket_data()

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
        # - is_first: True if next Token is first on line, after any indent.
        self.maxpos = len(self.text) - 1
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.is_first = True

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
            self.debug2(lexed = tok.kind)
            if self.validator(tok):
                self.update_location(tok)
                self.curr = None
                self.debug2(returned = tok.kind)
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
            is_first = self.is_first,
            indent = self.indent,
            newlines = newline_indexes,
        )

    def update_location(self, tok):
        # Updates the lexer's position-related info, given that
        # the parser has accepted the Token.

        # Character index, line number.
        self.pos += tok.width
        self.line += tok.nlines - 1

        # Column number.
        if tok.newlines:
            # Text straddles multiple lines. New column number
            # is based on the width of the text on the last line.
            #
            # Examples:
            #
            #     tok.text      | tok.width | tok.newlines | self.col
            #     ---------------------------------------------------
            #     \n            | 1         | (0,)         | 1
            #     fubb\n        | 5         | (4,)         | 1
            #     fubb\nbar     | 8         | (4,)         | 4
            #     fubb\nbar\n   | 9         | (4,8)        | 1
            #     fubb\nbar\nxy | 11        | (4,8)        | 3
            #
            self.col = tok.width - tok.newlines[-1]
        else:
            # Easy case: just add the token's width.
            self.col += tok.width

        # Update the parser's indent-related info.
        if tok.isa(TokDefs.newline):
            self.indent = 0
            self.is_first = True
        elif tok.isa(TokDefs.indent):
            self.indent = tok.width
            self.is_first = True
        else:
            self.is_first = False

    def debug(self, debug_level = 0, **kws):
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
        indent = Chars.space * (debug_level * 4)
        func_name = get_caller_name()
        params = ', '.join(
            f'{k} = {v!r}'
            for k, v in kws.items()
        )
        msg = f'{indent}{func_name}({params})'
        print(msg, file = fh)

    def debug1(self, **kws):
        self.debug(debug_level = 1, **kws)

    def debug2(self, **kws):
        self.debug(debug_level = 2, **kws)

####
# SpecParser.
####

# @dataclass
# class Handler:
#     # Data object used by SpecParser to manage transitions
#     # from one parsing mode to the next. Holds a top-level
#     # parsing function and the next mode to advance to if
#     # that function finds a match.
#     method: object
#     next_mode: str

class SpecParser:

    def __init__(self, text, debug = False):
        # The spec text.
        self.text = text

        # Whether/where to emit debug output.
        self.debug_fh = debug

        # The lexer.
        self.lexer = RegexLexer(text, self.taste, debug = debug)

        # Set the initial mode, which triggers the setter
        # to tell the RegexLexer which TokDefs to use.
        self.mode = Pmodes.variant

        # TokDefs the parser currently trying to eat: these are a subset of
        # those given to the RegexLexer whenever the parsing mode changes.
        self.menu = None

        # First Token of top-level ParseElem currently under construction.
        self.first_tok = None

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
        # The method used by Parser.parse(SPEC).

        # Setup.
        self.lexer.debug()
        self.lexer.debug(mode_check = 'started')

        # Collect variants.
        self.mode = Pmodes.variant
        elems = self.parse_some(self.variant)

        # TODO: reset lexer position if we failed on an opt-spec colon-marker.
        if True:
            pass

        # Collect all other elements.
        self.mode = Pmodes.section
        elems.extend(self.collect_section_elem)

        # Raise if we did not parse the full text.
        tok = self.lexer.end
        if not (tok and tok.isa(TokDefs.eof)):
            self.error('Failed to parse the full spec')

        # Convert the elements to a Grammar.
        return self.build_grammar(elems)

    def require_is_first_token(self):
        # Resets the parser's indent-related attributes, which will
        # cause self.taste() to reject the next token unless it is
        # the first on its line (aside from any indent).
        self.first_tok = None

    def collect_section_elem(self):
        elems = []
        while True:
            self.require_is_first_token()
            e = self.parse_first(
                self.any_section_title,
                self.section_content_elem,
            )
            if e:
                elems.append(e)
            else:
                break
        return elems

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
        self.lexer.debug1(wanted = ','.join(td.kind for td in tds))

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
            self.lexer.debug2(
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
        if self.first_tok is None:
            if tok.is_first:
                self.lexer.debug2(is_first = True)
                self.first_tok = tok
                return True
            else:
                self.lexer.debug2(is_first = False)
                return False

        def do_debug(ok):
            self.lexer.debug2(
                indent_ok = ok,
                self_indent = self.first_tok.indent,
                tok_indent = tok.indent,
            )

        # For subsequent tokens in the expression, we expect tokens either from
        # the same line or from a continuation line indented farther than the
        # first line of the expression.
        if self.first_tok.line == tok.line:
            do_debug('line')
            return True
        elif self.first_tok.indent < tok.indent:
            do_debug('indent')
            return True
        else:
            do_debug('NO')
            return False

    ####
    # Top-level parsing functions.
    ####

    def variant(self):
        self.require_is_first_token()

        # Get variant/partial name, if any.
        name = None
        is_partial = False
        tok = self.eat(TokDefs.variant_def)
        if tok:
            name = tok.m.group(1)
            if name.endswith(Chars.exclamation):
                name = name[0:-1]
                is_partial = True

        # Collect the ParseElem for the variant.
        elems = self.variant_elems()
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

    def any_section_title(self):
        tok = self.eat(TokDefs.scoped_section_title, TokDefs.section_title)
        if tok:
            return SectionTitle(title = tok.m.group(1).strip())
        else:
            return None

    # def section_title(self):
    #     tok = self.eat(TokDefs.section_title, TokDefs.section_name)
    #     if tok:
    #         return SectionTitle(title = tok.m.group(1).strip())
    #     else:
    #         return None

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

    def variant_elems(self):
        elems = []
        TAKES_QUANTIFIER = (Parenthesized, Bracketed, Positional, Option)
        while True:
            e = self.parse_first(
                self.quoted_literal,
                self.choice_sep,
                self.partial_usage,
                self.any_group,
                self.positional,
                self.option,
            )
            if e:
                e = self.with_quantifer(e, TAKES_QUANTIFIER)
                elems.append(e)
            else:
                break
        return elems

    def with_quantifer(self, e, types):
        if isinstance(e, types):
            q = self.quantifier()
            if q:
                e.quantifier = q
        return e

    def quoted_literal(self):
        tok = self.eat(TokDefs.quoted_literal)
        if tok:
            return QuotedLiteral(text = tok.m.group(1))
        else:
            return None

    def next_choice(self, require_sep = True):
        if require_sep and not self.eat(TokDefs.choice_sep)
            return None

        e = self.quoted_literal()
        if e:
            return e

        tok = self.eat(TokDefs.valid_name)
        return tok.text if tok else None

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

    def any_group(self):
        return paren_expression() or brack_expression()

    def paren_expression(self):
        return self.get_bracketed(Brackets.round, named_ok = True)

    def brack_expression(self):
        return self.get_bracketed(Brackets.square, named_ok = True)

    def positional(self):
        return self.get_bracketed(Brackets.positional, require_name = True)

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
        return self.get_bracketed(Brackets.parameter, empty_ok = True)

    def var_input_elems(self, require_name = False):
        # Returns a VarInput holding the guts of a positional or parameter.
        #
        # Forms:
        #
        #   < valid-name >
        #   < valid-name = choices >
        #   < choices >
        #   < >
        #
        # Logic for parameters:
        #
        #   - For positionals, noc is required.
        #
        #   noc         = name-or-choice
        #   assign      = bool
        #   require_sep = not assign
        #   roc         = rest-of-choices
        #
        #   noc | = | roc | Form | Example and error
        #   -------------------------------------------------------------------------------------
        #   Y   | Y | Y   | #2   | <foo=x|y>
        #   Y   | Y | .   | .    | <foo=>        Assign w/o choice(s)
        #   Y   | . | Y   | #3   | <foo|x|y>    
        #   Y   | . | .   | #1   | <foo>        
        #   .   | Y | Y   | .    | <=x|y>        Assign w/o name
        #   .   | Y | .   | .    | <=>           Ditto
        #   .   | . | Y   | #3   | <`hi!`|x|y>
        #   .   | . | .   | #4   | <>

        # Try to get a valid name, which could be a name or a choice.
        tok = self.eat(TokDefs.valid_name)
        name_or_choice = tok.text if tok else None

        # Check for an equal sign.
        assign = bool(self.eat(TokDefs.assign))
        require_sep = not assign

        # Collect the rest of the choices.
        rest = []
        while True:
            c = self.next_choice(require_sep = require_sep)
            require_sep = True
            if c:
                rest.append(c)
            else:
                break

        # Setup default parameters for VarInput we will return.
        name = name_or_choice or None
        choices = rest

        # Check for errors and make adjustments where needed.
        if require_name and not name:
            self.error('Var-input: positional requires a name: <>')
        elif assign and not choices:
            self.error('Var-input: assign without choices: <foo=>')
        elif assign and not name:
            self.error('Var-input: assign without a name: <=x|y')
        elif name and (not assign) and choices:
            choices = [name] + choices
            name = None

    def quantifier(self):
        q = self.parse_first(self.triple_dot, self.quant_range)
        if q:
            m, n = q
            greedy = not self.eat(TokDefs.question)
            return Quantifier(m, n, greedy)
        elif self.eat(TokDefs.question):
            # TODO: a bare ? means {0,1} => Quantifier(0, 1, False)
            return Quantifier(None, None, False)
        else:
            return None

    def triple_dot(self):
        tok = self.eat(TokDefs.triple_dot)
        return (1, None) if tok else None

    def quant_range(self):
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

    def get_bracketed(self, bracket, named_ok = False, empty_ok = False, **kws):
        # A general helper to consume an expression (optionally
        # with a name) enclosed in brackets: (), [], or <>.

        # Prepare the opening TokDefs we want to consume.
        td_open, td_close, td_named = BracketTriples[kind]
        tds = [td_open]
        if named_ok and td_named:
            tds.append(td_named)

        # Try to eat the opening bracket.
        tok = self.eat(*tds)
        if not tok:
            return None

        # Get the name, if any.
        gs = tok.m.groups()
        name = gs[0] if gs else None

        # Get the elem(s) inside the brackets.
        # Raise if we get nothing, unless empty is allowed.
        method = getattr(self, brackets.method_name)
        elems = method(**kws)
        if not (elems or empty_ok):
            self.error(
                msg = 'Empty bracketed expression',
                kind = kind,
            )

        # If we can eat the closing TokDef, return an Enclosed instance.
        # Otherwise raise an error.
        if self.eat(td_close):

            if b.kind == b

            if cls:
                return cls(kind = kind, elems = elems)
            else:
                return Enclosed(kind = kind, name = name, elems = elems)
        else:
            self.error(
                msg = 'Failed to find closing bracket',
                kind = kind,
            )

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

def fill_to_length(xs, wanted):
    # Takes a list and a desired length.
    # Returns a list of that length (or longer).
    need = wanted - len(xs)
    return xs + [None] * need

