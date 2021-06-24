
'''

Status:

    - Able to lex/parse the README examples to an AST (with some bugs/issues
      noted below), but not yet a Grammar. Correctness not fully checked.

TODO:

    - debug() output from eat() looks like col might be off by 1 : investigate

    - Sorted out most of the continuation-line problems, but the situation is
      awkward and at least one bug remains:

        - Awkward:
            - We have special logic for Pmodes.variant vs Pmodes.opt_help.
            - It's not clear we need to modify SpecParser.line for continuation lines.
            - allow_second isn't the clearest name

        - Known bug. The following two examples should be equivalent, but the
          parser does the second example incorrectly because all lines are
          interpreted as continuations, because the special-logic noted above
          sets self.indent=0 when eating `pgrep` and that never changes.

            FIXED NOW, I think: see allow_second.

            # Would correctly create 2 Variant.
            pgrep [-i] [-v] <rgx> <path>
            [--foo] <blort>

            # Would incorrectly create only 1 Variant.
            pgrep
               [-i] [-v]
                    <rgx> <path>
               [--foo] <blort>

            - The problem: sometimes we want the first eat() for Pmodes.variant to
              establish self.indent and sometimes we don't (the latter is wanted
              only with the first variant starts on the same line as the prog).

            - There are two issues:

                - Does next token have to be first on the line?
                    - Yes for first token of top-level ParseElem.
                    - With one exception: the first Variant: it can be first or second token.

                - Should the token be used to establish a new value for SpecParser.indent?
                    - Always yes, at least for top-level ParseElem.

                - Currently, self.indent is handling both things. Hence the problem.

    - Convert grammar-syntax AST into a Grammar.

'''

####
# Imports.
####

import attr
import re
import short_con as sc
import inspect
from functools import cache
from collections import OrderedDict

from .errors import OptopusError

def attrcls(*names):
    # Takes attribute names as list or space-delimited string.
    # Returns a class decorator that will add attributes
    # to the given class. Invoke this decorator so that it
    # executes before @attr.s().
    names = tuple(nm for name in names for nm in name.split())

    def decorator(cls):
        for nm in names:
            setattr(cls, nm, attr.ib())
        return cls

    return decorator

####
# Data classes.
####

@attr.s(frozen = True)
@attrcls('kind regex modes emit')
class TokDef:
    pass

@attr.s(frozen = True)
@attrcls('kind text m width pos line col nlines isfirst indent newlines')
class Token:

    def isa(self, *tds):
        return any(self.kind == td.kind for td in tds)

@attr.s(frozen = True)
@attrcls('name')
class Prog:
    pass

@attr.s(frozen = True)
@attrcls('name is_partial elems')
class Variant:
    pass

@attr.s(frozen = True)
@attrcls('elems text')
class OptHelp:
    pass

@attr.s(frozen = True)
@attrcls('title')
class SectionTitle:
    pass

@attr.s(frozen = True)
@attrcls('text')
class QuotedBlock:
    pass

@attr.s(frozen = True)
@attrcls('text')
class QuotedLiteral:
    pass

@attr.s(frozen = True)
@attrcls('name')
class PartialUsage:
    pass

@attr.s(frozen = True)
@attrcls('elems quantifier')
class Parenthesized:
    pass

@attr.s(frozen = True)
@attrcls('elems quantifier')
class Bracketed:
    pass

@attr.s(frozen = True)
@attrcls('sym dest symlit val vals')
class SymDest:
    pass

@attr.s(frozen = True)
@attrcls('sym dest symlit choices quantifier')
class Positional:
    pass

@attr.s(frozen = True)
@attrcls('dest params quantifier')
class Option:
    pass

@attr.s(frozen = True)
@attrcls('')
class ChoiceSep:
    pass

@attr.s(frozen = True)
@attrcls('m n greedy')
class Quantifier:
    pass

@attr.s(frozen = True)
@attrcls('sym dest symlit choice')
class PositionalVariant:
    pass

@attr.s(frozen = True)
@attrcls('sym dest symlit choices')
class Parameter:
    pass

@attr.s(frozen = True)
@attrcls('sym dest symlit choice')
class ParameterVariant:
    pass

@attr.s(frozen = True)
@attrcls('elems')
class Grammar:
    pass

####
# Functions to return constants collections.
####

@cache
def define_regex_snippets():
    hws0 = r'[ \t]*'
    hws1 = r'[ \t]+'
    name = r'\w+(?:[_-]\w+)*'
    num = r'\d+'
    q = hws0 + ',' + hws0
    return sc.cons(
        'RegexSnippets',
        hws0   = hws0,
        hws1   = hws1,
        name   = name,
        num    = num,
        q      = q,
        prog   = name + r'(?:\.\w+)?',
        eol    = hws0 + r'(?=\n)',
        bq     = r'(?<!\\)`',
        bq3    = r'(?<!\\)```',
        pre    = '-',
        quant  = hws0 + '|'.join((num + q + num, num + q, q + num, num, q)) + hws0,
        quoted = r'[\s\S]*?',
        head   = '(?m)^',
    )

@cache
def define_tokdefs():
    # Helper to wrap a regex elem in a capture.
    c = lambda s: '(' + s + ')'

    # Convenience vars.
    r = Snippets
    hw = r.hws0
    cnm = c(r.name)

    # Tuples to define TokDef instances.
    tups = (
        # Kind             Emit  Modes    Pattern
        # - Quoted.
        ('quoted_block',   1,    '  s ',  r.bq3 + c(r.quoted) + r.bq3),
        ('quoted_literal', 1,    'vos ',  r.bq + c(r.quoted) + r.bq),
        # - Whitespace.
        ('newline',        0.0,  'vosh',  r'\n'),
        ('indent',         0.0,  'vosh',  r.head + r.hws1 + r'(?=\S)'),
        ('whitespace',     0.0,  'vosh',  r.hws1),
        # - Sections.
        ('section_name',   1,    'v   ',  c(r.prog) + hw + '::' + r.eol),
        ('section_title',  1,    'vos ',  c('.*') + '::' + r.eol),
        # - Parens.
        ('paren_open',     1,    'vos ',  r'\('),
        ('paren_close',    1,    'vos ',  r'\)'),
        ('brack_open',     1,    'vos ',  r'\['),
        ('brack_close',    1,    'vos ',  r'\]'),
        ('angle_open',     1,    'vos ',  '<'),
        ('angle_close',    1,    'vos ',  '>'),
        # - Quants.
        ('quant_range',    1,    'vos ',  r'\{' + c(r.quant) + r'\}'),
        ('triple_dot',     1,    'vos ',  r'\.\.\.'),
        ('question',       1,    'vos ',  r'\?'),
        # - Separators.
        ('choice_sep',     1,    'vos ',  r'\|'),
        ('assign',         1,    'vos ',  '='),
        ('opt_help_sep',   1,    ' os ',  ':'),
        # - Options.
        ('long_option',    1,    'vos ',  r.pre + r.pre + cnm),
        ('short_option',   1,    'vos ',  r.pre + c(r'\w')),
        # - Variants.
        ('partial_def',    1,    'v   ',  cnm + '!' + hw + ':'),
        ('variant_def',    1,    'v   ',  cnm + hw + ':'),
        ('partial_usage',  1,    'v   ',  cnm + '!'),
        # - Sym, dest.
        ('sym_dest',       1,    'vos ',  cnm + hw + c('[!.]') + hw + cnm),
        ('dot_dest',       1,    'vos ',  r'\.' + hw + cnm),
        ('solo_dest',      1,    'vos ',  cnm + hw + r'(?=[>=])'),
        ('name',           1,    'vos ',  r.name),
        # - Special.
        ('rest_of_line',   1,    '   h',  '.+'),
        ('eof',            0.0,  '    ',  ''),
        ('err',            0.0,  '    ',  ''),
    )

    # Parser modes.
    pms = dict(
        v = Pmodes.variant,
        o = Pmodes.opt_help,
        s = Pmodes.section,
        h = Pmodes.help_text,
    )

    # Create a dict mapping kind to each TokDef.
    tds = OrderedDict()
    for kind, emit, ms, patt in tups:
        tds[kind] = TokDef(
            kind = kind,
            regex = re.compile(patt),
            modes = tuple(pms[m] for m in ms if m != Chars.space),
            emit = bool(emit),
        )

    # Return them as a constants collection.
    return sc.constants('TokDefs', tds)

####
# Parsing and grammar constants.
####

Chars = sc.cons(
    'Chars',
    space = ' ',
    newline = '\n',
    exclamation = '!',
    comma = ',',
)

Pmodes = sc.constants('ParserModes', 'variant opt_help section help_text')
Snippets = define_regex_snippets()
TokDefs = define_tokdefs()

ParenPairs = {
    TokDefs.paren_open: TokDefs.paren_close,
    TokDefs.brack_open: TokDefs.brack_close,
    TokDefs.angle_open: TokDefs.angle_close,
}

Debug = sc.cons(
    'Debug',
    emit = True,
)

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, validator, tokdefs = None):
        # Inputs:
        # - Text to be lexxed.
        # - Validator function from parser to validate tokens.
        # - TokDefs currently of interest.
        self.text = text
        self.validator = validator
        self.tokdefs = tokdefs

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
            debug(2, lexed = tok.kind)
            if self.validator(tok):
                self.update_location(tok)
                self.curr = None
                debug(2, returned = tok.kind)
                return tok
            else:
                self.curr = tok
                return None

        # And if we didn't get a token, we have lexed as far as
        # we can. Set the end token and return it.
        td = (TokDefs.err, TokDefs.eof)[self.pos > self.maxpos]
        m = re.search('^$', '')
        tok = self.create_token(td, m)
        self.curr = None
        self.end = tok
        self.update_location(tok)
        return tok

    def match_token(self):
        # Starting at self.pos, reutn the next Token.
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
        # Update position-related info.
        self.pos += tok.width
        self.line += tok.nlines - 1
        self.col = (
            tok.width - tok.newlines[-1] - 1 if tok.newlines
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

####
# SpecParser.
####

@attr.s(frozen = True)
class Handler:
    method = attr.ib()
    next_mode = attr.ib()

class SpecParser:

    def __init__(self, text):
        # The text and the lexer.
        self.text = text
        self.lexer = RegexLexer(text, self.taste)

        # Line and indent from the first Token of the top-level
        # ParseElem currently under construction by the parser.
        self.line = None
        self.indent = None
        self.allow_second = False

        # Parsing modes. First defines the handlers for each
        # mode. Then set the initial mode.
        self.handlers = {
            Pmodes.variant: (
                Handler(self.section_title, Pmodes.section),
                Handler(self.variant, None),
            ),
            Pmodes.opt_help: (
                Handler(self.section_title, Pmodes.section),
                Handler(self.opt_help, None),
            ),
            Pmodes.section: (
                Handler(self.quoted_block, None),
                Handler(self.section_title, None),
                Handler(self.opt_help, None),
            ),
            Pmodes.help_text: tuple(),
        }
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
        self._mode = mode
        self.lexer.tokdefs = tuple(
            td
            for td in TokDefs.values()
            if mode in td.modes
        )

    ####
    # Parse a spec.
    ####

    def parse(self):
        # Determine parsing mode:
        #
        #   [prog] :: opt_help...
        #   [prog] variant...
        #

        # return Grammar([len(self.lexer.tokens)])

        debug(0)
        debug(0, mode_check = 'started')

        allow_second = False
        prog = None
        tok = self.eat(TokDefs.section_name)
        if tok:
            self.mode = Pmodes.opt_help
            prog = tok.m.group(1)
        else:
            self.mode = Pmodes.variant
            tok = self.eat(TokDefs.name)
            if tok:
                prog = tok.text
                allow_second = True

        # Parse everything into a list of ParseElem.
        elems = list(self.do_parse(allow_second))

        # Raise if we did not parse the full text.
        tok = self.lexer.end
        if not (tok and tok.isa(TokDefs.eof)):
            self.error('Failed to parse the full spec')

        # Convert elems to a Grammar.
        # There will be some validation needed here too.

        return self.build_grammar(prog, elems)

    def build_grammar(self, prog, elems):
        return Grammar(elems)

        print()
        print('zzzzzzzzzzzzzzz')
        for e in elems:
            print(e)
        print('---------------')
        print()

        '''

        ----------------------------------------------------

        LOOKS OK

        pgrep [-i] [-v] <rgx> <path>

        Variant(
            name=None,
            is_partial=False,
            elems=[
                Bracketed(
                    elems=[Option(dest='i', params=[], quantifier=None)],
                    quantifier=None),
                Bracketed(
                    elems=[Option(dest='v', params=[], quantifier=None)],
                    quantifier=None),
                Positional(sym=None, dest='rgx', symlit=False, choices=(), quantifier=None),
                Positional(sym=None, dest='path', symlit=False, choices=(), quantifier=None),
            ],
        )

        ----------------------------------------------------

        TODO: incorrect parse:
            - continuation-line logic must have a problem
            - The first OptHelp consume all of the subequent material as continuation.

        pgrep ::
            <rgx> : Python regular expression
            [<path>...] : Path(s) to input
            [-i --ignore-case] : Ignore case
            [-v --invert-match] : Select non-matching lines

        OptHelp(
            elems=[Positional(sym=None, dest='rgx', symlit=False, choices=(), quantifier=None)],
            text='Python regular expression [<path>...] : Path(s) to input [-i --ignore-case] : Ignore case [-v --invert-match] : Select non-matching lines'
        )

        ----------------------------------------------------

        TODO: incorrect parse:
            - similar continuation-line problem
            - in this case, the whole grammer is interpreted as one variant; should be 3

        wrangle
            <task=grep>   [-i] [-v] [-m] [-C]
                          [--color <red|green|blue>]
                          <rgx> [<path>...]
            <task=sub>    [-i] [-n] <rgx> <rep> [<path>...]
            <task=search> [-i] [-g] [-d | -p] <rgx> [<path>...]

            ::

            <task>             : Task to perform
            <task=grep>        : Emit lines matching pattern
            <task=sub>         : Search for pattern and replace
            <task=search>      : Emit text matching pattern
            <rgx>              : Python regular expression
            <path>             : Path(s) to input
            <rep>              : Replacement text
            -i --ignore-case   : Ignore case
            -v --invert-match  : Select non-matching lines
            -m --max-count <n> : Stop searching after N matches
            -C --context <n>   : Print N lines of before/after context
            --color <>         : Highlight matching text
            -n --nsubs <n>     : N of substitutions
            -g --group <n>     : Emit just capture group N [0 for all]
            -d --delim <s>     : Delimeter for capture groups [tab]
            -p --para          : Emit capture groups one-per-line, paragraph-style

        Variant(
            name=None,
            is_partial=False,
            elems=[
                PositionalVariant(sym=None, dest='task', symlit=False, choice='grep'),
                Bracketed(elems=[Option(dest='i', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='v', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='m', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='C', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='color', params=[Parameter(sym=None, dest=None, symlit=False, choices=('red', 'green', 'blue'))], quantifier=None)], quantifier=None),
                Positional(sym=None, dest='rgx', symlit=False, choices=(), quantifier=None),
                Bracketed(elems=[Positional(sym=None, dest='path', symlit=False, choices=(), quantifier=Quantifier(m=1, n=None, greedy=True))], quantifier=None),

                PositionalVariant(sym=None, dest='task', symlit=False, choice='sub'),
                Bracketed(elems=[Option(dest='i', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='n', params=[], quantifier=None)], quantifier=None),
                Positional(sym=None, dest='rgx', symlit=False, choices=(), quantifier=None),
                Positional(sym=None, dest='rep', symlit=False, choices=(), quantifier=None),
                Bracketed(elems=[Positional(sym=None, dest='path', symlit=False, choices=(), quantifier=Quantifier(m=1, n=None, greedy=True))], quantifier=None),

                PositionalVariant(sym=None, dest='task', symlit=False, choice='search'),
                Bracketed(elems=[Option(dest='i', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='g', params=[], quantifier=None)], quantifier=None),
                Bracketed(elems=[Option(dest='d', params=[], quantifier=None), ChoiceSep(), Option(dest='p', params=[], quantifier=None)], quantifier=None),
                Positional(sym=None, dest='rgx', symlit=False, choices=(), quantifier=None),
                Bracketed(elems=[Positional(sym=None, dest='path', symlit=False, choices=(), quantifier=Quantifier(m=1, n=None, greedy=True))], quantifier=None)
            ]
        )
        SectionTitle(title='::')
        OptHelp(
            elems = [
                Positional(sym=None, dest='task', symlit=False, choices=(), quantifier=None),
            ],
            text='Task to perform'
        )
        OptHelp(
            elems = [
                PositionalVariant(sym=None, dest='task', symlit=False, choice='grep'),
            ],
            text='Emit lines matching pattern'
        )
        OptHelp(
            elems = [
                PositionalVariant(sym=None, dest='task', symlit=False, choice='sub'),
            ],
            text='Search for pattern and replace'
        )
        OptHelp(
            elems = [
                PositionalVariant(sym=None, dest='task', symlit=False, choice='search'),
            ],
            text='Emit text matching pattern'
        )
        OptHelp(
            elems = [
                Positional(sym=None, dest='rgx', symlit=False, choices=(), quantifier=None),
            ],
            text='Python regular expression'
        )
        OptHelp(
            elems = [
                Positional(sym=None, dest='path', symlit=False, choices=(), quantifier=None),
            ],
            text='Path(s) to input'
        )
        OptHelp(
            elems = [
                Positional(sym=None, dest='rep', symlit=False, choices=(), quantifier=None),
            ],
            text='Replacement text'
        )
        OptHelp(
            elems = [
                Option(dest='i', params=[], quantifier=None),
                Option(dest='ignore-case', params=[], quantifier=None),
            ],
            text='Ignore case'
        )
        OptHelp(
            elems = [
                Option(dest='v', params=[], quantifier=None),
                Option(dest='invert-match', params=[], quantifier=None),
            ],
            text='Select non-matching lines'
        )
        OptHelp(
            elems = [
                Option(dest='m', params=[], quantifier=None),
                Option(
                    dest='max-count',
                    params=[Parameter(sym='n', dest=None, symlit=False, choices=())],
                    quantifier=None),
            ],
            text='Stop searching after N matches'
        )
        OptHelp(
            elems = [
                Option(dest='C', params=[], quantifier=None),
                Option(
                    dest='context',
                    params=[Parameter(sym='n', dest=None, symlit=False, choices=())],
                    quantifier=None),
            ],
            text='Print N lines of before/after context'
        )
        OptHelp(
            elems = [
                Option(
                    dest='color',
                    params=[Parameter(sym=None, dest=None, symlit=False, choices=())],
                    quantifier=None),
            ],
            text='Highlight matching text'
        )
        OptHelp(
            elems = [
                Option(dest='n', params=[], quantifier=None),
                Option(
                    dest='nsubs',
                    params=[Parameter(sym='n', dest=None, symlit=False, choices=())],
                    quantifier=None),
            ],
            text='N of substitutions'
        )
        OptHelp(
            elems = [
                Option(dest='g', params=[], quantifier=None),
                Option(
                    dest='group',
                    params=[Parameter(sym='n', dest=None, symlit=False, choices=())],
                    quantifier=None),
            ],
            text='Emit just capture group N [0 for all]'
        )
        OptHelp(
            elems = [
                Option(dest='d', params=[], quantifier=None),
                Option(
                    dest='delim',
                    params=[Parameter(sym='s', dest=None, symlit=False, choices=())],
                    quantifier=None),
            ],
            text='Delimeter for capture groups [tab]'
        )
        OptHelp(
            elems = [
                Option(dest='p', params=[], quantifier=None),
                Option(dest='para', params=[], quantifier=None),
            ],
            text='Emit capture groups one-per-line, paragraph-style'
        )


        ----------------------------------------------------

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

            - First check for ChoiceSep.
                - If present, create an Group(mutex=True) container.

            ...

        Sections:
            - An ordered list of section-elems.
            - Where each section-elem is: QuotedBlock or Opt-reference.

        '''

        # Top-level parsing:
        #     variant:
        #         section_title
        #         variant
        #     opt_help:
        #         section_title
        #         opt_help
        #     section:
        #         quoted_block
        #         section_title
        #         opt_help
        #
        # ParseElem: top-level:
        #     Prog: name
        #     Variant: name is_partial elems
        #     OptHelp: elems text
        #     SectionTitle: title
        #     QuotedBlock: text
        #
        # ParseElem: groups:
        #     Parenthesized: elems quantifier
        #     Bracketed: elems quantifier
        #     ChoiceSep:
        #
        # ParseElem: elems:
        #     PartialUsage: name
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
                debug(0, handler = h.method.__name__)
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

    ####
    # Eat tokens.
    ####

    def eat(self, *tds):
        self.menu = tds
        debug(1, wanted = ','.join(td.kind for td in tds))
        tok = self.lexer.get_next_token()
        if tok is None:
            return None
        elif tok.isa(TokDefs.eof, TokDefs.err):
            return None
        else:
            debug(
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
                    debug(2, isfirst = True)
                    # HERE_INDENT
                    self.indent = tok.indent
                    self.line = tok.line
                    return True
                else:
                    debug(2, isfirst = False)
                    return False
            else:
                if self.line == tok.line:
                    debug(2, indent_ok = 'line', line = self.line)
                    return True
                elif self.indent < tok.indent:
                    debug(2, indent_ok = 'indent', self_indent = self.indent, tok_indent = tok.indent)
                    # HERE_INDENT
                    # self.line = tok.line
                    return True
                else:
                    debug(2, indent_ok = False, self_indent = self.indent, tok_indent = tok.indent)
                    return False
        else:
            # debug(2, kind = False)
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

    def opt_help(self):
        # Try to get elements.
        elems = self.elems()
        if not elems:
            return None

        # Try to get the Opt help text and any continuation lines.
        texts = []
        if self.eat(TokDefs.opt_help_sep):
            self.mode = Pmodes.help_text
            while True:
                tok = self.eat(TokDefs.rest_of_line)
                if tok:
                    texts.append(tok.text.strip())
                else:
                    break
            self.mode = Pmodes.opt_help

        # Join text parts and return.
        text = Chars.space.join(t for t in texts if t)
        return OptHelp(elems, text)

    def section_title(self):
        tok = self.eat(TokDefs.section_title)
        if tok:
            return SectionTitle(title = tok.text.strip())
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
                    e = attr.evolve(e, quantifier = q)
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
        else:
            return None

    def triple_dot(self):
        tok = self.eat(TokDefs.triple_dot)
        return (1, None) if tok else None

    def quantifier_range(self):
        tok = self.eat(TokDefs.quant_range)
        if tok:
            text = TokDefs.whitespace.regex.sub('', tok.text)
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

def debug(indent, **kws):
    if Debug.emit:
        msg = ''
        if kws:
            func = get_caller_name()
            gen = ('{} = {!r}'.format(k, v) for k, v in kws.items())
            msg = '{}{}({})'.format(
                Chars.space * (indent * 4),
                func,
                ', '.join(gen)
            )
        print(msg)

