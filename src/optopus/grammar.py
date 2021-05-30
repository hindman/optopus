
'''

Status and remaining issues/questions:

    - We appear to be able to lex/parse the README examples.

    - Implement data-oriented exception strategy.

    - Convert grammar-syntax AST into a Grammar.

    - Need better debugging support.

Change specification: symdest vals must be quoted-literal or name. It's easy to
parse and easy to explain/document.

OptopusError:
    - Add method to make it easy to raise failed-parse errors.
    - Add kws to the calls.

Add SpecParser.debug attribute:
    - Parse as far as you can. Don't raise.
    - Collect eaten tokens and assembled elements.
    - Implement a method to print out the info.

'''

####
# Imports.
####

import attr
import re
import short_con as sc
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

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, validator, tokdefs = None):
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
            debug('LEX', tok.kind)
            if self.validator(tok):
                self.update_location(tok)
                self.curr = None
                debug('LEX', 'returning', tok.kind)
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
        debug('LEX', 'update_location', tok.kind)
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

        tok = self.eat(TokDefs.section_name)
        if tok:
            self.mode = Pmodes.opt_help
            prog = tok.m.group(1)
        else:
            self.mode = Pmodes.variant
            tok = self.eat(TokDefs.name)
            prog = tok.text if tok else None

        # Parse everything into a list of ParseElem.
        elems = [Prog(name = prog)]
        elems.extend(self.do_parse())

        # Raise if we did not parse the full text.
        lex = self.lexer
        if not (lex.end and lex.end.isa(TokDefs.eof)):
            msg = 'Failed to parse the full spec'
            raise OptopusError(
                msg = msg,
                pos = lex.pos,
                line = lex.line,
                col = lex.col,
                curr = lex.curr,
            )

        # Convert elems to a Grammar.
        # There will be some validation needed here too.
        return Grammar(elems)

    def do_parse(self):
        # Yields top-level ParseElem (those declared in self.handlers).
        debug('DO_PARSE', 'start')
        elem = True
        while elem:
            elem = False
            for h in self.handlers[self.mode]:
                debug('DO_PARSE', h)
                elem = h.method()
                if elem:
                    yield elem
                    # Every top-level ParseElem must start on a fresh line.
                    self.indent = None
                    self.line = None
                    # Advance parser mode, if needed.
                    if h.next_mode:
                        self.mode = h.next_mode
                    # Break from inner loop and enter again from beginning.
                    # We will exit outer loop if all handlers return None.
                    break

    ####
    # Eat tokens.
    ####

    def eat(self, *tds):
        self.menu = tds
        tok = self.lexer.get_next_token()
        if tok is None:
            return None
        elif tok.isa(TokDefs.eof, TokDefs.err):
            return None
        else:
            debug('EAT', tok)
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
        debug('TASTE', tok.kind)
        if any(tok.isa(td) for td in self.menu):
            if self.indent is None:
                if tok.isfirst:
                    debug('-', 1)
                    self.indent = tok.indent
                    self.line = tok.line
                    return True
                else:
                    debug('-', 2)
                    return False
            else:
                if self.line == tok.line:
                    debug('-', 21)
                    return True
                elif self.indent < tok.indent:
                    debug('-', 22)
                    self.line = tok.line
                    return True
                else:
                    debug('-', 23)
                    return False
        else:
            debug('-', 999)
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
            msg = 'A Variant cannot be empty'
            raise OptopusError(msg)

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
        debug('SECTION_TITLE', 'start')
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
            msg = 'Positionals require at least a dest'
            lex = self.lexer
            raise OptopusError(
                msg = msg,
                pos = lex.pos,
                line = lex.line,
                col = lex.col,
            )

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
                msg = 'Found choice values without required equal sign'
                raise OptopusError(msg)

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
                msg = 'Illegal empty parenthesized expression'
                raise OptopusError(msg)
            elif self.eat(td_close):
                return elem
            else:
                msg = 'Failed to find closing paren/bracket'
                lex = self.lexer
                raise OptopusError(
                    msg = msg,
                    pos = lex.pos,
                    line = lex.line,
                    col = lex.col,
                    close = td_close,
                    curr = lex.curr,
                )
        else:
            return None

    ####
    # Other stuff.
    ####

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise OptopusError(msg)

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

def debug(*xs):
    if False:
        print(*xs)

