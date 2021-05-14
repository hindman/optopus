
# TODO: parse_some() and parse_first(): make sure they are helpful.

'''

variant
    expression ...
        element...
            quoted_literal
            partial_usage
            paren_expression
                ( expression )
            brack_expression
                [ expression ]
            positional
                < positional_definition >
            long_option
                --opt
                parameter*
                    < parameter_definition >
            short_option
                -o
                parameter*
                    < parameter_definition >

# Details.
choices
quantifier
one_or_more_dots
quantifier_range

# helpers
parenthesized
option

'''

####
# Imports.
####

import attr
import re
import short_con as sc
from functools import cache
from collections import OrderedDict

def attrcls(*names):
    # Takes attribute names as list or space-delimited string.
    # Returns a class decorator that will add attributes
    # to the given class. Invoke this decorator so that it
    # executes before @attr.ib().
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
@attrcls('kind text m width pos line col nlines isfirst indent')
class Token:

    def isa(self, td):
        return self.kind == td.kind

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
@attrcls('elems')
class Parenthesized:
    pass

@attr.s(frozen = True)
@attrcls('elems')
class Bracketed:
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
    # Convenience vars.
    r = Snippets
    p = Pmodes
    hw = r.hws0
    pms = {
        '_': (p.variant, p.opt_help, p.section),
        'O': (p.opt_help, p.section),
        'v': (p.variant,),
        'o': (p.opt_help,),
        's': (p.section,),
        '': tuple(),
    }

    # Helper to wrap a regex elem in a capture.
    c = lambda p: '(' + p + ')'

    # Tuples to define TokDef instances.
    tups = (
        # Kind,            Emit, Modes, Pattern.
        ('quoted_block',   1,    's',   r.bq3 + c(r.quoted) + r.bq3),
        ('quoted_literal', 1,    '_',   r.bq + c(r.quoted) + r.bq),
        ('newline',        0.0,  '_',   r'\n'),
        ('indent',         1,    '_',   r.head + r.hws1 + r'(?=\S)'),
        ('whitespace',     0.0,  '_',   r.hws1),
        ('quant_range',    1,    '_',   r'\{' + c(r.quant) + r'\}'),
        ('paren_open',     1,    '_',   r'\('),
        ('paren_close',    1,    '_',   r'\)'),
        ('brack_open',     1,    '_',   r'\['),
        ('brack_close',    1,    '_',   r'\]'),
        ('angle_open',     1,    '_',   '<'),
        ('angle_close',    1,    '_',   '>'),
        ('choice_sep',     1,    '_',   r'\|'),
        ('triple_dot',     1,    '_',   r'\.\.\.'),
        ('question',       1,    '_',   r'\?'),
        ('long_option',    1,    '_',   r.pre + r.pre + c(r.name)),
        ('short_option',   1,    '_',   r.pre + c(r'\w')),
        ('section_name',   1,    'v',   r.head + c(r.prog) + '?' + hw + '::' + r.eol),
        ('section_title',  1,    '_',   r.head + c('.*') + '::' + r.eol),
        ('partial_def',    1,    'v',   c(r.name) + '!' + hw + ':'),
        ('variant_def',    1,    'v',   c(r.name) + hw + ':'),
        ('partial_usage',  1,    'v',   c(r.name) + '!'),
        ('name_assign',    1,    '_',   c(r.name) + hw + '='),
        ('sym_dest',       1,    '_',   c(r.name) + hw + '[!.]' + hw + c(r.name)),
        ('dest',           1,    '_',   '[!.]' + hw + c(r.name)),
        ('name',           1,    '_',   r.name),
        ('assign',         1,    '_',   '='),
        ('opt_help_sep',   1,    'O',   ':'),
        ('choice_val',     1,    '_',   '[^\s|>]+'),
        ('rest',           1,    '',    '.+'),
        ('eof',            0.0,  '',    ''),
        ('err',            0.0,  '',    ''),
    )

    # Create a dict mapping kind to each TokDef.
    tds = OrderedDict(
        (kind, TokDef(kind, re.compile(patt), pms[m], bool(emit)))
        for kind, emit, m, patt in tups
    )

    # Return them as a constants collection.
    return sc.constants('TokDefs', tds)

####
# Parsing and grammar constants.
####

Pmodes = sc.constants('ParserModes', 'variant opt_help section')
Snippets = define_regex_snippets()
TokDefs = define_tokdefs()
Chars = sc.cons(
    'Chars',
    space = ' ',
    newline = '\n',
)

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, tokdefs = None):
        self.text = text
        self.tokdefs = tokdefs

        # Location and token information.
        self.maxpos = len(self.text) - 1
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.isfirst = True

        # Will be set with Token(eof)/Token(err) when lexing finishes.
        self.end = None

    def get_next_token(self, lex_tokdef = None):
        # Starting at self.pos, emit the next Token.
        #
        # For non-emitted tokens, we break out of the for-loop,
        # but enter the while-loop again. This allows the lexer
        # to be able to ignore any number of non-emitted tokens
        # on each call of the function.
        #
        # The optional lex_tokdef allows the parser to request a
        # specific TokDef directly, bypassing the normal ordering
        # in self.tokdefs. Used for opt-help text continuation-lines.

        # Return if we are already done lexing.
        if self.end:
            return self.end

        # Normalize input to a tuple of TokDef.
        tds = (lex_tokdef,) if lex_tokdef else self.tokdefs

        # Return next Token that should be emitted.
        tok = True
        while tok:
            tok = None
            for td in tds:
                m = td.regex.match(self.text, pos = self.pos)
                if m:
                    tok = self.create_token(td, m)
                    if td.emit:
                        return tok
                    else:
                        break

        # We have lexed as far as we can.
        # Set self.end to Token(eof) or Token(err).
        td = (TokDefs.err, TokDefs.eof)[self.pos > self.maxpos]
        self.end = self.create_token(td, '')
        return self.end

    def create_token(self, tokdef, m):
        # Get text width and newline locations/count.
        text = m.group(0)
        width = len(text)
        indexes = [i for i, c in enumerate(text) if c == Chars.newline]
        n = len(indexes)

        # Create token.
        tok = Token(
            kind = tokdef.kind,
            text = text,
            m = m,
            width = width,
            pos = self.pos,
            line = self.line,
            col = self.col,
            nlines = n + 1,
            isfirst = self.isfirst,
            indent = self.indent,
        )

        # Update location info.
        self.isfirst = False
        self.pos += width
        self.line += n
        self.col = (
            width - indexes[-1] - 1 if indexes
            else self.col + width
        )

        # Update indent info.
        if tok.isa(TokDefs.newline):
            self.indent = 0
            self.isfirst = True
        elif tok.isa(TokDefs.indent):
            self.indent = tok.width
            self.isfirst = True

        # Return token.
        return tok

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
        self.lexer = RegexLexer(text)

        # Info about current token, line, and indent of that line.
        self.curr = None
        self.line = None
        self.indent = None

        # Parser mode and associated handlers.
        self.mode = None
        self.handlers = {
            None: tuple(),
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
        }

    ####
    # Setting the parser mode.
    ####

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if self.curr:
            # Changing mode while caching a prior token seems bad.
            raise ...
        else:
            self._mode = mode
            self.lexer.tokens = tuple(td for td in TokDefs if mode in td.modes)

    ####
    # Parse a spec.
    ####

    def parse(self):
        # Determine parsing mode:
        #
        #   [prog] :: opt_help...
        #   [prog] variant...
        #
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
        if self.lexer.end.isa(TokDefs.err):
            raise ...

        # Convert elems to a Grammar.
        # There will be some validation needed here too.
        return Grammar(elems)

    def do_parse(self):
        # Yields top-level ParseElem (those declared in self.handlers).
        elem = True
        while elem:
            for h in self.handlers[self.mode]:
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

    def eat(self, *tds, taste = False, lex_tokdef = None):
        # Get the next token, either from self.curr or the lexer.
        #
        # Note that unless the caller requested that the
        # lexer be asked for a specific TokDef, this method
        # will automatically skip any intervening indent tokens.

        # Get next token of interest.
        while True:
            if self.curr is None:
                self.curr = self.lexer.get_next_token(lex_tokdef)
            tok = self.curr

            # Lexer should deal with EOF, not parser.
            if tok.isa(EOF):
                raise ...

            # Skip indents, unless lex_tokdef.
            if tok.isa(TokDefs.indent) and not lex_tokdef:
                self.curr = None

            # Usually we break on the first iteration.
            break

        # Check whether the token follows indentation/start-of-line rules.
        #
        # - If SpecParser has no indent yet, we expect the first token
        #   for a variant/opt-help expression. If so, we remember that
        #   token's indent and line.
        #
        # - For subsequent tokens in the expression, we expect tokens
        #   from the same line or a continuation line indented farther
        #   than the first line of the expression.
        if self.indent is None:
            if tok.is_first:
                self.indent = tok.indent
                self.line = tok.line
                ok = True
            else:
                ok = False
        else:
            if self.line == tok.line:
                ok = True
            elif self.indent < tok.indent:
                self.line = tok.line
                ok = True
            else:
                ok = False

        # Return the token if indentation was OK
        # and it is among the requested kinds.
        if ok and any(self.curr.isa(td) for td in tds):
            if not taste:
                self.swallow()
            return tok
        else:
            return None

    def swallow(self):
        if self.curr is None:
            raise ...
        else:
            self.curr = None

    ####
    # Top-level ParseElem handlers.
    ####

    def variant(self):
        # Get variant/partial name, if any.
        tds = (TokDefs.variant_def, TokDefs.partial_def)
        tok = self.eat(tds, taste = True)
        if tok:
            self.swallow()
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
            raise ...

    def opt_help(self):
        # Try to get elements.
        elems = self.elems()
        if not elems:
            return None

        # Try to get the Opt help text and any continuation lines.
        texts = []
        if self.eat(TokDefs.opt_help_sep):
            while True:
                tok = self.eat(lex_tokdef = TokDefs.rest)
                if tok:
                    texts.append(tok.text.strip())
                if not self.eat(lex_tokdef = TokDefs.indent)
                    break

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
        methods = (
            self.quoted_literal,
            self.partial_usage,
            self.paren_expression,
            self.brack_expression,
            self.positional,
            self.long_option,
            self.short_option,
        )
        elems = []
        while True:
            e = self.parse_first(methods)
            if e:
                q = self.quantifier()
                if q:
                    e = attr.evolve(e, quantifier = q)
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

    def partial_usage(self):
        tok = self.eat(TokDefs.partial_usage)
        if tok:
            return PartialUsage(name = tok.m.group(1))
        else:
            return None

    def paren_expression(self):
        elems = self.parenthesized(TokDefs.paren_open, self.elems)
        if elems:
            return Parenthesized(elems)
        else:
            return None

    def brack_expression(self):
        elems = self.parenthesized(TokDefs.brack_open, self.elems)
        if elems:
            return Bracketed(elems)
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
            return Option(dest, params)
        else:
            return None

    # TODO: HERE

    def choices(self, require_dest = False):

        # ('sym_dest',       1,    '_',   c(r.name) + hw + '[!.]' + hw + c(r.name)),
        # ('dest',           1,    '_',   '[!.]' + hw + c(r.name)),
        # ('name',           1,    '_',   r.name),
        # ('assign',         1,    '_',   '='),
        # ('opt_help_sep',   1,    'O',   ':'),
        # ('choice_val',     1,    '_',   '[^\s|>]+'),

        # This version is better, but it doesn't handle 
        # just <dest> or <sym>.

        # Maybe it would help to have two choice_val tokens:
        # - choice_val followed by pipe
        # - choice_val by itself

        # Forms:
        #
        #   <    dest     >
        #   <    dest=vals>
        #   <sym.dest     >
        #   <sym.dest=vals>
        #
        #   <                >
        #   <           =vals>    # Equal sign is optional.
        #   <sym             >
        #   <sym        =vals>
        #   <   .subdest     >
        #   <   .subdest=vals>
        #   <sym.subdest     >
        #   <sym.subdest=vals>

        # Try to get sym.dest.
        tok = self.eat(TokDefs.sym_dest, TokDefs.dest)
        if tok:
            sym = ...
            dest = ...
        elif require_dest:
            raise ...
        else:
            sym = None
            dest = None

        # Try to get the dest assign equal-sign.
        assign = self.eat(TokDefs.assign)

        # Try to get any choice_val.
        vals = []
        while True:
            # Check for a choice_val.
            tok = self.eat(TokDefs.choice_val, taste = True)
            if not tok:
                break

            # Retroactively require the assign equal-sign if
            # we got the surrounding elements.
            if (sym or dest) and not assign:
                raise ...

            # Continue looping if choice_sep is next.
            self.swallow()
            vals.append(...)
            if not self.eat(TokDefs.choice_sep):
                break

        # Handle single choice_val.
        if len(vals) == 1:
            val = vals[0]
            vals = None
        else:
            val = None

        # Return.
        return SymDest(sym, dest, val, vals)

    def positional(self):
        # Try to get a Choices elem.
        ch = self.parenthesized(TokDefs.angle_open, self.choices)
        if not ch:
            return None

        # Positionals require a dest.
        if not ch.dest:
            raise ...

        # Return Positional or ParameterVariant.
        if len(ch.vals) == 1:
            return PositionalVariant(ch.dest, val = ch.vals[0])
        else:
            return Positional(ch.dest, choices = ch.vals)

    def parameter(self):
        ch = self.parenthesized(TokDefs.angle_open, self.choices, empty_ok = True)
        if not ch:
            return None

        # Handle nameless param <>.
        if not (choices.dest or choices.vals):
            return Parameter(None, None)

        # Return named Parameter or ParameterVariant.
        dest = choices.dest
        vals = choices.vals
        n = len(vals)
        return (
            Parameter(dest, None) if n == 0
            ParameterVariant(dest, val = val[0]) elif n == 1
            Parameter(dest, vals)
        )

    def quantifier(self):
        quantifier_methods = (
            self.one_or_more_dots,
            self.quantifier_range,
        )
        q = self.parse_first(quantifier_methods)
        if q:
            greedy = not self.eat(question)
            return Quantifier(q, greedy)
        else:
            return None

    def one_or_more_dots(self):
        tok = self.eat(triple-dot)
        if tok:
            return (1, None)
        else:
            return None

    def quantifier_range(self):
        tok = self.eat(quantifier-range)
        if tok:
            ...
            return (..., ...)
        else:
            return None

    def parenthesized(self, td_open, method, empty_ok = False):
        td_close = ParenPairs[td_open]
        tok = self.eat(td_open)
        if tok:
            elem = method()
            if not (elem or empty_ok):
                raise ...
            elif self.eat(td_close):
                return elem
            else:
                raise ...
        else:
            return None

    ####
    # Other stuff.
    ####

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

    def parse_first(self, methods):
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
                elems.push(e)
            else:
                break
        return elems

