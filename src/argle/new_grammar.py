
'''

----
Parsing the new spec-syntax
----

TODO:

    - staging plan:
        - Edit NEW files, while keeping OLD runnable.
        - When ready, swap back via git-mv (Git history resides in NEW).

----
Notes and questions
----

Entities that must start on a fresh line.
    - variant
    - any-section-title
    - section-content-elem

Parsing modes:
    - grammar: default
    - help_text: for opt-spec (rest of line plus continuations)

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
    0+ BlockQuote
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

    - Applies to Variant, Group.

    - Organize into groups, partitioning on ChoiceSep.
    - If multiple groups, we will end up with Group(mutext=True)

    ...



Sections:
    - An ordered list of section-elems.
    - Where each section-elem is: BlockQuote or Opt-reference.

ParseElem: top-level:
    Variant: name is_partial elems
    OptSpec: elems text
    SectionTitle: title
    BlockQuote: text

ParseElem: elems:
    ChoiceSep:
    QuotedLiteral: text
        - Becomes an Opt.
        - But has no dest.
        - Essentially requires the variant to include a positional constant.
        - Does that make it like a PositionalVariant with one choice and no dest or sym?
    PartialUsage: name
        - Insert the elems from the Variant(partial=True)
    Group: elems quantifier
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
from dataclasses import dataclass, field, replace as clone
from functools import wraps

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

    @property
    def brief(self):
        params = ', '.join(
            f'{attr} = {getattr(self, attr)!r}'
            for attr in 'kind text pos line col indent is_first'.split()
        )
        return f'Token({params})'

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
class Scope(ParseElem):
    query_path = str

@dataclass
class OptSpec(ParseElem):
    scope: Scope
    opt: ParseElem
    text: str
    token: Token

@dataclass
class SectionTitle(ParseElem):
    scope: Scope
    title: str
    token: Token

@dataclass
class Heading(ParseElem):
    title: str
    token: Token

@dataclass
class BlockQuote(ParseElem):
    text: str
    token: Token

@dataclass
class QuotedLiteral(ParseElem):
    text: str

@dataclass
class Choice(ParseElem):
    text: str

@dataclass
class SectionElems(ParseElem):
    elems: list[ParseElem]

@dataclass
class VariantElems(ParseElem):
    elems: list[ParseElem]

@dataclass
class VarInput(ParseElem):
    name: str
    elems: list[Choice]

@dataclass
class Quantifier(ParseElem):
    m: int
    n: int
    greedy: bool = True

@dataclass
class PartialUsage(ParseElem):
    text: str

@dataclass
class Group(ParseElem):
    name: str
    elems: list
    quantifier: Quantifier = None
    required: bool = True

@dataclass
class Positional(ParseElem):
    name: str
    elems: list    # choices
    quantifier: Quantifier = None

@dataclass
class Parameter(ParseElem):
    name: str
    elems: list    # choices
    quantifier: Quantifier = None

@dataclass
class RestOfLine(ParseElem):
    text: str

@dataclass
class OptHelpText(ParseElem):
    text: str

@dataclass
class BareOption(ParseElem):
    name: str

@dataclass
class Option(ParseElem):
    name: str
    params: list[Parameter]
    quantifier: Quantifier = None
    aliases: list[BareOption] = field(default_factory = list)

@dataclass
class ChoiceSep(ParseElem):
    pass

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
    def pp_gen(elem, level = 0, prefix = ''):
        # Setup.
        cls_name = elem.__class__.__name__
        indent1 = '    ' * level
        indent2 = '    ' * (level + 1)
        child_elems = ('elems', 'params', 'opt')

        # Start with the class of the current element.
        yield f'{indent1}{prefix}{cls_name}('

        # Then basic attributes.
        for attr, v in elem.__dict__.items():
            if attr not in child_elems:
                v = f'{v.brief}' if isinstance(v, Token) else f'{v!r}'
                yield f'{indent2}{attr} = {v}'

        # Then recurse to child elements.
        for attr in child_elems:
            children = getattr(elem, attr, [])
            if not isinstance(children, list):
                children = [children]

            for child in children:
                # yield f'{indent2}{attr} ='
                yield from Grammar.pp_gen(
                    child,
                    level + 1,
                )

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
    scope_marker = '<<'
    query_elem = fr'{glob_char}+'
    query_path = fr'{query_elem}(?:\.{query_elem})*'
    scope0 = scope_marker
    scope1 = captured(query_path) + wrapped_in(whitespace0, scope_marker)

    # Section title, heading.
    section_title = captured('.*') + section_marker
    heading = captured('.*') + heading_marker

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
    empty_set = '∅',
)

Pmodes = cons('grammar help_text')

TokDefs = define_tokdefs()
Rgxs = constants({kind : td.regex for kind, td in TokDefs})

# Bracket data keyed by the kind of bracketed expression.

BPairs = constants({
    TokDefs.paren_open.kind:       TokDefs.paren_close,
    TokDefs.paren_open_named.kind: TokDefs.paren_close,
    TokDefs.brack_open.kind:       TokDefs.brack_close,
    TokDefs.brack_open_named.kind: TokDefs.brack_close,
    TokDefs.angle_open.kind:       TokDefs.angle_close,
})

GBKinds = cons(
    # Groups.
    'group',
    'parameter_group',
    'opt_spec_group',
    # Var-inputs.
    'positional',
    'parameter',
)

OpeningTDs = cons(
    group = [
        TokDefs.paren_open,
        TokDefs.paren_open_named,
        TokDefs.brack_open,
        TokDefs.brack_open_named,
    ],
    var_input = [TokDefs.angle_open],
)

GBTDs = constants({
    GBKinds.group:           OpeningTDs.group,
    GBKinds.parameter_group: OpeningTDs.group,
    GBKinds.opt_spec_group:  OpeningTDs.group,
    GBKinds.positional:      OpeningTDs.var_input,
    GBKinds.parameter:       OpeningTDs.var_input,
})

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, validator, tokdefs = None, debug = False):
        # Text to be lexed.
        self.text = text

        # Debugging: file handle and indent-level.
        self.debug_fh = debug
        self.debug_indent = 0

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

    POSITION_ATTRS = cons('pos line col indent is_first')

    @tokdefs.setter
    def tokdefs(self, tokdefs):
        # If TokDefs are changed, clear any cached Token.
        self._tokdefs = tokdefs
        self.curr = None

    @property
    def position(self):
        return constants({
            a : getattr(self, a)
            for a in self.POSITION_ATTRS.keys()
        })

    @position.setter
    def position(self, p):
        self.curr = None
        for a in self.POSITION_ATTRS.keys():
            setattr(self, a, getattr(p, a))

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
            self.debug(lexed = tok.kind)
            if self.validator(tok):
                self.update_location(tok)
                self.curr = None
                self.debug(returned = tok.kind)
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
        text = m[0] if m else ''
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

    def debug(self,
              caller_name = None,
              caller_offset = 0,
              msg_prefix = '',
              RESULT = None,
              **kws):
        # Decided whether and where to emit debug output.
        if self.debug_fh is True:
            fh = sys.stdout
        elif self.debug_fh:
            fh = self.debug_fh
        else:
            return

        # Indentation.
        indent = Chars.space * (self.debug_indent * 2)

        # Name of the method calling debug().
        caller_name = caller_name or get_caller_name(caller_offset + 2)

        # The params-portion of the debug message.
        if RESULT is not None:
            params = f'RESULT = {RESULT}' if RESULT else Chars.empty_set
        elif kws:
            params = ', '.join(
                f'{k} = {v!r}'
                for k, v in kws.items()
            )
        else:
            params = ''

        # Print the message.
        msg = f'{msg_prefix}{indent}{caller_name}({params})'
        print(msg, file = fh)

####
# SpecParser.
####

class SpecParser:

    def __init__(self, text, debug = False):
        # The spec text.
        self.text = text

        # The lexer.
        self.lexer = RegexLexer(text, self.taste, debug = debug)

        # Set the initial mode, which triggers the setter
        # to tell the RegexLexer which TokDefs to use.
        self.mode = Pmodes.grammar

        # TokDefs the parser currently trying to eat: these are a subset of
        # those given to the RegexLexer whenever the parsing mode changes.
        self.menu = None

        # First Token of top-level ParseElem currently under construction.
        self.first_tok = None

        # Tokens the parser has eaten:
        # - For the entire spec.
        # - Since the last reset_meal() call.
        self.eaten = []
        self.meal = []

    ####
    # Debug decorator.
    ####

    def debug_indent(old_method):
        # Setup based on the name of the method being decorated.
        NAME = old_method.__name__
        MSG_PREFIX = '\n' if NAME == 'parse' else ''

        @wraps(old_method)
        def new_method(self, *xs, **kws):
            # Call debug() to emit the method name.
            lex = self.lexer
            lex.debug(caller_name = NAME, msg_prefix = MSG_PREFIX)

            # Within a higher indent level:
            # - Call the method.
            # - Call debug() to summarize the result.
            lex.debug_indent += 1
            elem = old_method(self, *xs, **kws)
            result = type(elem).__name__ if elem else False
            lex.debug(caller_name = NAME, RESULT = result)

            # Return to previous indent level and return.
            lex.debug_indent -= 1
            return elem

        return new_method

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

    @debug_indent
    def parse(self):
        # The method used by Parser.parse(SPEC).

        # Collect variants.
        elems = self.parse_some(self.variant)

        # Collect all other elements.
        se = self.collect_section_elems()
        if se:
            elems.extend(se.elems)

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

    @debug_indent
    def collect_section_elems(self):
        elems = []
        while True:
            self.require_is_first_token()
            e = (
                self.any_section_title() or
                self.section_content_elem()
            )
            if e:
                elems.append(e)
            else:
                break
        if elems:
            return SectionElems(elems = elems)
        else:
            return None

    def build_grammar(self, elems):
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
        self.lexer.debug(wanted = '|'.join(td.kind for td in tds))

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
                eaten = tok.kind,
                text = tok.text,
                pos = tok.pos,
                line = tok.line,
                col = tok.col,
            )
            self.eaten.append(tok)
            self.meal.append(tok)
            return tok

    def reset_meal(self):
        self.meal = []

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
                self.lexer.debug(ok = True, is_first = True)
                self.first_tok = tok
                return True
            else:
                self.lexer.debug(ok = True, is_first = False)
                return False

        def do_debug(reason):
            self.lexer.debug(
                ok = bool(reason),
                indent_reason = reason,
                self_indent = self.first_tok.indent,
                tok_indent = tok.indent,
                caller_offset = 1,
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
            do_debug(False)
            return False

    ####
    # Top-level parsing functions.
    ####

    @debug_indent
    def variant(self):
        lex = self.lexer
        self.require_is_first_token()
        orig_pos = lex.position

        # Get variant/partial name, if any.
        name = None
        is_partial = False
        tok = self.eat(TokDefs.variant_def)
        if tok:
            name = tok.m[1]
            if name.endswith(Chars.exclamation):
                name = name[0:-1]
                is_partial = True

        # Collect the ParseElem for the variant.
        ve = self.variant_elems()

        # Return, raise, or reset lexer position.
        if ve:
            if lex.curr and lex.curr.isa(TokDefs.opt_spec_sep):
                # If we got elems but halted on an opt-spec separator, return
                # empty after resetting the lexer position. We do this so we
                # can try to re-parse as an opt-spec rather than as a variant.
                lex.position = orig_pos
                return None
            else:
                # Otherwise, return the Variant.
                return Variant(
                    name = name,
                    is_partial = is_partial,
                    elems = ve.elems,
                )
        else:
            # If we got no elems, the situation is simple.
            if name:
                self.error('A Variant cannot be empty')
            else:
                return None

    @debug_indent
    def opt_spec_scope(self):
        tok = self.eat(TokDefs.opt_spec_scope, TokDefs.opt_spec_scope_empty)
        if tok:
            query_path = get(tok.m, 0)
            return Scope(query_path)
        else:
            return None

    @debug_indent
    def opt_spec_def(self):
        return (
            self.opt_spec_group() or
            self.opt_spec_elem()
        )

    @debug_indent
    def opt_spec_group(self):
        return self.with_quantifer(
            self.get_bracketed(GBKinds.opt_spec_group)
        )

    @debug_indent
    def opt_spec_elem(self):
        return (
            self.positional() or
            self.aliases_and_option()
        )

    @debug_indent
    def aliases_and_option(self):
        aliases = self.parse_some(self.bare_option)
        if aliases:
            b = aliases.pop()
            params = self.parse_some(self.any_parameter)
            e = Option(
                name = b.name,
                params = params,
                aliases = aliases,
            )
            if params:
                return e
            else:
                return self.with_quantifer(e)
        else:
            return None

    @debug_indent
    def rest_of_line(self):
        tok = self.eat(TokDefs.rest_of_line)
        if tok:
            text = tok.text.strip()
            if text:
                return RestOfLine(text = text)
        return None

    @debug_indent
    def opt_help_text(self):
        # Try to get the help text and any continuation lines.
        if self.eat(TokDefs.opt_spec_sep):
            # Change parsing mode while collected opt-spec help text.
            self.mode = Pmodes.help_text
            elems = self.parse_some(self.rest_of_line)
            self.mode = Pmodes.grammar

            # If we got any, assemble and return an OptHelpText.
            if elems:
                text = Chars.space.join(e.text for e in elems)
                return OptHelpText(text = text)

        return None

    @debug_indent
    def opt_spec(self):
        # If we do get an opt-spec, we will need access to its first Token.
        self.reset_meal()

        # Get the Scope, if any.
        scope = self.opt_spec_scope()

        # Get the Opt definition.
        e = self.opt_spec_def()
        if not e:
            return None

        # Get the OptHelpText, if any.
        t = self.opt_help_text()

        # Boom.
        return OptSpec(
            scope = scope,
            opt = e,
            text = t.text if t else None,
            token = self.meal[0],
        )

    @debug_indent
    def any_section_title(self):
        tok = self.eat(TokDefs.scoped_section_title, TokDefs.section_title)
        if tok:
            if tok.isa(TokDefs.scoped_section_title):
                scope = Scope(tok.m[1])
                title = tok.m[2]
            else:
                scope = None
                title = tok.m[1]
            return SectionTitle(
                title = title,
                scope = scope,
                token = tok,
            )
        else:
            return None

    ####
    # The elems() helper, which deals with parsing functions
    # shared by variants and opt-specs.
    ####

    @debug_indent
    def heading(self):
        tok = self.eat(TokDefs.heading)
        if tok:
            return Heading(
                title = tok.m[1].strip(),
                token = tok,
            )
        else:
            return None

    @debug_indent
    def block_quote(self):
        tok = self.eat(TokDefs.quoted_block)
        if tok:
            return BlockQuote(
                text = tok.m[1],
                token = tok,
            )
        else:
            return None

    @debug_indent
    def section_content_elem(self):
        return (
            self.heading() or
            self.block_quote() or
            self.opt_spec()
        )

    @debug_indent
    def variant_elems(self):
        elems = []
        while True:
            e = (
                self.quoted_literal() or
                self.choice_sep() or
                self.partial_usage() or
                self.any_group() or
                self.positional() or
                self.option()
            )
            if e:
                elems.append(e)
            else:
                break
        if elems:
            return VariantElems(elems = elems)
        else:
            return None

    @debug_indent
    def with_quantifer(self, e):
        if e:
            q = self.quantifier()
            if q:
                e.quantifier = q
        return e

    @debug_indent
    def quoted_literal(self):
        tok = self.eat(TokDefs.quoted_literal)
        if tok:
            return QuotedLiteral(text = tok.m[1])
        else:
            return None

    @debug_indent
    def next_choice(self, require_sep = True):
        if require_sep and not self.eat(TokDefs.choice_sep):
            return None

        e = self.quoted_literal()
        if e:
            return Choice(text = e.text)

        tok = self.eat(TokDefs.valid_name)
        if tok:
            return Choice(text = tok.text)
        else:
            return None

    @debug_indent
    def choice_sep(self):
        tok = self.eat(TokDefs.choice_sep)
        if tok:
            return ChoiceSep()
        else:
            return None

    @debug_indent
    def partial_usage(self):
        tok = self.eat(TokDefs.partial_usage)
        if tok:
            return PartialUsage(name = tok.m[1])
        else:
            return None

    @debug_indent
    def any_group(self):
        return self.with_quantifer(
            self.get_bracketed(GBKinds.group)
        )

    @debug_indent
    def parameter_group(self):
        return self.with_quantifer(
            self.get_bracketed(GBKinds.parameter_group)
        )

    @debug_indent
    def any_parameter(self):
        return (
            self.parameter() or
            self.parameter_group()
        )

    @debug_indent
    def positional(self):
        return self.with_quantifer(
            self.with_quantifer(
                self.get_bracketed(GBKinds.positional)
            )
        )

    @debug_indent
    def option(self):
        b = self.bare_option()
        if b:
            params = self.parse_some(self.any_parameter)
            e = Option(b.name, params, None)
            if params:
                return e
            else:
                return self.with_quantifer(e)
        else:
            return None

    @debug_indent
    def bare_option(self):
        tok = self.eat(TokDefs.long_option, TokDefs.short_option)
        if tok:
            return BareOption(name = tok.m[1])
        else:
            return None

    @debug_indent
    def parameter(self):
        return self.with_quantifer(
            self.get_bracketed(GBKinds.parameter)
        )

    @debug_indent
    def var_input_elems(self, require_name = False):
        # Returns a VarInput holding the guts of a positional or parameter.

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
            # Occurs when Parameter has choices, but no name: <a|b|c>
            choices = [Choice(text = name)] + choices
            name = None

        # Return the elems.
        return VarInput(name = name, elems = choices)

    @debug_indent
    def quantifier(self):
        q = self.triple_dot() or self.quant_range()
        if q:
            q.greedy = not self.eat(TokDefs.question)
            return q
        elif self.eat(TokDefs.question):
            return Quantifier(m = 0, n = 1)
        else:
            return None

    @debug_indent
    def triple_dot(self):
        tok = self.eat(TokDefs.triple_dot)
        if tok:
            return Quantifier(m = 1, n = None)
        else:
            return None

    @debug_indent
    def quant_range(self):
        tok = self.eat(TokDefs.quant_range)
        if tok:
            text = TokDefs.whitespace.regex.sub('', tok.m[1])
            xs = [
                None if x == '' else int(x)
                for x in text.split(Chars.comma)
            ]
            m = xs[0]
            n = get(xs, 1, default = m)
            return Quantifier(m = m, n = n)
        else:
            return None

    ####
    # Helper to parse a bracketed-expression: () [] <>.
    #
    # Plus its helper functions to manage the details for
    # each kind of expression.
    ####

    def get_bracketed(self, kind):
        # Takes a GBKinds value indicating the kind of bracketed expression
        # to parse. Does one of the follow:
        #
        # - Returns a ParseElem (success).
        # - Returns None (no opening bracket to get started)
        # - Raises an error (parses an expression partially, then must halt).
        #

        # Try to eat the opening bracket.
        tds = GBTDs[kind]
        tok = self.eat(*tds)
        if not tok:
            return None

        # Based on the Token we got, determine closing bracket TokDef.
        closing_td = BPairs[tok.kind]

        # Get group name attached to opening bracket, if any.
        group_name = get(tok.m, 1)

        # Parse the guts of the bracketed expression, using the helper
        # correspondng to the kind of expression.
        #
        # For groups, the helper has to be called with group-name, and the
        # returned Group has to be adjusted for square brackets.
        helper_method = getattr(self, f'gb_guts_{kind}')
        if tds == OpeningTDs.group:
            e = helper_method(group_name = group_name)
            if e and closing_td.isa(TokDefs.brack_close):
                e.required = False
        else:
            e = helper_method()

        # Raise if we cannot get the closing TokDef.
        if not self.eat(closing_td):
            self.error(
                msg = 'Failed to find closing bracket',
                kind = kind,
            )

        # Return the ParseElem.
        return e

    def gb_guts_positional(self):
        vi = self.var_input_elems(require_name = True)
        return Positional(name = vi.name, elems = vi.elems)

    def gb_guts_parameter(self):
        vi = self.var_input_elems()
        return Parameter(name = vi.name, elems = vi.elems)

    def gb_guts_group(self, group_name):
        ve = self.variant_elems()
        elems = ve.elems if ve else []
        g = Group(name = group_name, elems = elems)
        return self.require_elems(g)

    def gb_guts_parameter_group(self, group_name):
        elems = self.parse_some(self.any_parameter)
        g = Group(name = group_name, elems = elems)
        return self.require_elems(g)

    def gb_guts_opt_spec_group(self, group_name):
        ose = self.opt_spec_elem()
        elems = [ose] if ose else []
        g = Group(name = group_name, elems = elems)
        return self.require_elems(g)

    def require_elems(self, e):
        if e.elems:
            return e
        else:
            self.error(msg = 'Empty Group', e = e)

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

    def parse_some(self, method, **kws):
        # Takes a parsing function.
        # Collects as many elems as possible and returns them.
        elems = []
        while True:
            e = method(**kws)
            if e is None or e == []:
                break
            else:
                elems.append(e)
        return elems

def get_caller_name(caller_offset):
    # Get the name of a calling function.
    x = inspect.currentframe()
    for _ in range(caller_offset):
        x = x.f_back
    x = x.f_code.co_name
    return x

def fill_to_len(xs, n):
    # Takes a list and a desired length.
    # Returns a list at least that long.
    filler = [None] * (n - len(xs))
    return xs + filler

def get(xs, i, default = None):
    try:
        return xs[i]
    except (IndexError, KeyError) as e:
        return default

