# TODO: Fix get_token_types()
# Move the algorithm to the code.
# Just create a simple constants collection, keyed by kind.

####
# Imports.
####

import attr
import re
import short_con as sc
from functools import cache
from collections import OrderedDict

####
# Data classes.
####

@attr.s(frozen = True)
class TokType:
    kind = attr.ib()
    regex = attr.ib()
    modes = attr.ib()
    emit = attr.ib()

@attr.s(frozen = True)
class Token:
    kind = attr.ib()
    text = attr.ib()
    width = attr.ib()
    pos = attr.ib()
    line = attr.ib()
    col = attr.ib()
    n_lines = attr.ib()
    isfirst = attr.ib()
    indent = attr.ib()

####
# Functions to return constants collections.
####

@cache
def get_regex_snippets():
    hws0 = r'[ \t]*'
    hws1 = r'[ \t]+'
    name = r'\w+(?:[_-]\w+)*'
    num = r'\d+'
    q = hws0 + ',' + hws0
    return sc.cons(
        'RegexSnippets',
        hws0  = hws0,
        hws1  = hws1,
        name  = name,
        num   = num,
        q     = q,
        prog  = name + r'(?:\.\w+)?',
        eol   = hws0 + r'(?=\n)',
        bq    = r'(?<!\\)`',
        bq3   = r'(?<!\\)```',
        pre   = '-',
        quant = hws0 + '|'.join((num + q + num, num + q, q + num, num, q)) + hws0,
    )

@cache
def get_token_types():
    # Convenience vars.
    r = get_regex_snippets()
    p = Pmodes
    pms = {
        '_': (p.variant, p.opt_help, p.section),
        'O': (p.opt_help, p.section),
        'v': (p.variant,),
        'o': (p.opt_help,),
        's': (p.section,),
        '': tuple(),
    }
    # Tuples to define TokTypes.
    tups = (
        # Kind,               Emit, Modes, Regex pattern.
        ('quoted_block',      1,    's',   r.bq3 + r'[\s\S]*?' + r.bq3),
        ('quoted_literal',    1,    '_',   r.bq + r'[\s\S]*?' + r.bq),
        (Tkinds.newline,      0.0,  '_',   r'\n'),
        (Tkinds.indent,       1,    '_',   '(?m)^' + r.hws1 + r'(?=\S)'),
        ('whitespace',        0.0,  '_',   r.hws1),
        ('quant_range',       1,    '_',   r'\{' + r.quant + r'\}'),
        ('paren_open',        1,    '_',   r'\('),
        ('paren_close',       1,    '_',   r'\)'),
        ('brack_open',        1,    '_',   r'\['),
        ('brack_close',       1,    '_',   r'\]'),
        ('angle_open',        1,    '_',   '<'),
        ('angle_close',       1,    '_',   '>'),
        ('choice_sep',        1,    '_',   r'\|'),
        ('triple_dot',        1,    '_',   r'\.\.\.'),
        ('question',          1,    '_',   r'\?'),
        ('long_option',       1,    '_',   r.pre + r.pre + r.name),
        ('short_option',      1,    '_',   r.pre + r'\w'),
        ('section_name',      1,    'v',   r.prog + '?' + r.hws0 + '::' + r.eol),
        ('section_title',     1,    '_',   '.*::' + r.eol),
        ('partial_defintion', 1,    'v',   r.name + '!' + r.hws0 + ':'),
        ('variant_defintion', 1,    'v',   r.name + r.hws0 + ':'),
        ('partial_usage',     1,    'v',   r.name + '!'),
        ('name_assign',       1,    '_',   r.name + r.hws0 + '='),
        ('sym_dest',          1,    '_',   r.name + r.hws0 + '[!.]' + r.hws0 + r.name),
        ('dest',              1,    '_',   '[!.]' + r.hws0 + r.name),
        ('name',              1,    '_',   r.name),
        ('assign',            1,    '_',   '='),
        ('opt_help_sep',      1,    'O',   ':.*'),  # TODO: adjust
    )
    # Create a tuple of all TokTypes.
    tts = tuple(
        TokType(kind, re.compile(patt), pms[m], bool(emit))
        for kind, emit, m, patt in tups
    )

    # Using that tuple, create dict mapping ParserMode to its TokTypes.
    ttmap = {
        pm : OrderedDict((tt.kind, tt) for tt in tts if pm in tt.modes)
        for pm in p.values()
    }

    # Also add some special TokTypes.
    ttmap[Tkinds.special] = OrderedDict(
        (tt.kind, tt)
        for tt in (
            TokType(Tkinds.eof, None, tuple(), False),
            TokType(Tkinds.err, None, tuple(), False),
            TokType(Tkinds.rest, '.+', tuple(), True),
        )
    )

    # Return them as a collection of constants collections.
    return sc.constants('TokenTypes', {
        k : sc.constants('TokenTypes', d)
        for k, d in ttmap.items()
    })

####
# Parsing and grammar constants.
####

Tkinds = sc.constants('TokenKinds', 'eof err indent newline rest special')
Pmodes = sc.constants('ParserModes', 'variant opt_help section')
TokenTypes = get_token_types()

####
# Imports.
####

import attr
import re
import short_con as sc
from functools import cache
from collections import OrderedDict

####
# Data classes.
####

@attr.s(frozen = True)
class TokType:
    kind = attr.ib()
    regex = attr.ib()
    modes = attr.ib()
    emit = attr.ib()

@attr.s(frozen = True)
class Token:
    kind = attr.ib()
    text = attr.ib()
    width = attr.ib()
    pos = attr.ib()
    line = attr.ib()
    col = attr.ib()
    n_lines = attr.ib()
    isfirst = attr.ib()
    indent = attr.ib()

####
# Functions to return constants collections.
####

@cache
def get_regex_snippets():
    hws0 = r'[ \t]*'
    hws1 = r'[ \t]+'
    name = r'\w+(?:[_-]\w+)*'
    num = r'\d+'
    q = hws0 + ',' + hws0
    return sc.cons(
        'RegexSnippets',
        hws0  = hws0,
        hws1  = hws1,
        name  = name,
        num   = num,
        q     = q,
        prog  = name + r'(?:\.\w+)?',
        eol   = hws0 + r'(?=\n)',
        bq    = r'(?<!\\)`',
        bq3   = r'(?<!\\)```',
        pre   = '-',
        quant = hws0 + '|'.join((num + q + num, num + q, q + num, num, q)) + hws0,
    )

@cache
def get_token_types():
    # Convenience vars.
    r = get_regex_snippets()
    p = Pmodes
    pms = {
        '_': (p.variant, p.opt_help, p.section),
        'O': (p.opt_help, p.section),
        'v': (p.variant,),
        'o': (p.opt_help,),
        's': (p.section,),
        '': tuple(),
    }
    # Tuples to define TokTypes.
    tups = (
        # Kind,               Emit, Modes, Regex pattern.
        ('quoted_block',      1,    's',   r.bq3 + r'[\s\S]*?' + r.bq3),
        ('quoted_literal',    1,    '_',   r.bq + r'[\s\S]*?' + r.bq),
        (Tkinds.newline,      0.0,  '_',   r'\n'),
        (Tkinds.indent,       1,    '_',   '(?m)^' + r.hws1 + r'(?=\S)'),
        ('whitespace',        0.0,  '_',   r.hws1),
        ('quant_range',       1,    '_',   r'\{' + r.quant + r'\}'),
        ('paren_open',        1,    '_',   r'\('),
        ('paren_close',       1,    '_',   r'\)'),
        ('brack_open',        1,    '_',   r'\['),
        ('brack_close',       1,    '_',   r'\]'),
        ('angle_open',        1,    '_',   '<'),
        ('angle_close',       1,    '_',   '>'),
        ('choice_sep',        1,    '_',   r'\|'),
        ('triple_dot',        1,    '_',   r'\.\.\.'),
        ('question',          1,    '_',   r'\?'),
        ('long_option',       1,    '_',   r.pre + r.pre + r.name),
        ('short_option',      1,    '_',   r.pre + r'\w'),
        ('section_name',      1,    'v',   r.prog + '?' + r.hws0 + '::' + r.eol),
        ('section_title',     1,    '_',   '.*::' + r.eol),
        ('partial_defintion', 1,    'v',   r.name + '!' + r.hws0 + ':'),
        ('variant_defintion', 1,    'v',   r.name + r.hws0 + ':'),
        ('partial_usage',     1,    'v',   r.name + '!'),
        ('name_assign',       1,    '_',   r.name + r.hws0 + '='),
        ('sym_dest',          1,    '_',   r.name + r.hws0 + '[!.]' + r.hws0 + r.name),
        ('dest',              1,    '_',   '[!.]' + r.hws0 + r.name),
        ('name',              1,    '_',   r.name),
        ('assign',            1,    '_',   '='),
        ('opt_help_sep',      1,    'O',   ':.*'),  # TODO: adjust
    )
    # Create a tuple of all TokTypes.
    tts = tuple(
        TokType(kind, re.compile(patt), pms[m], bool(emit))
        for kind, emit, m, patt in tups
    )

    # Using that tuple, create dict mapping ParserMode to its TokTypes.
    ttmap = {
        pm : OrderedDict((tt.kind, tt) for tt in tts if pm in tt.modes)
        for pm in p.values()
    }

    # Also add some special TokTypes.
    ttmap[Tkinds.special] = OrderedDict(
        (tt.kind, tt)
        for tt in (
            TokType(Tkinds.eof, None, tuple(), False),
            TokType(Tkinds.err, None, tuple(), False),
            TokType(Tkinds.rest, '.+', tuple(), True),
        )
    )

    # Return them as a collection of constants collections.
    return sc.constants('TokenTypes', {
        k : sc.constants('TokenTypes', d)
        for k, d in ttmap.items()
    })

####
# Parsing and grammar constants.
####

Tkinds = sc.constants('TokenKinds', 'eof err indent newline rest special')
Pmodes = sc.constants('ParserModes', 'variant opt_help section')
TokenTypes = get_token_types()

####
# Imports.
####

import attr
import re
import short_con as sc
from functools import cache
from collections import OrderedDict

####
# Data classes.
####

@attr.s(frozen = True)
class TokType:
    kind = attr.ib()
    regex = attr.ib()
    modes = attr.ib()
    emit = attr.ib()

@attr.s(frozen = True)
class Token:
    kind = attr.ib()
    text = attr.ib()
    width = attr.ib()
    pos = attr.ib()
    line = attr.ib()
    col = attr.ib()
    n_lines = attr.ib()
    isfirst = attr.ib()
    indent = attr.ib()

####
# Functions to return constants collections.
####

@cache
def get_regex_snippets():
    hws0 = r'[ \t]*'
    hws1 = r'[ \t]+'
    name = r'\w+(?:[_-]\w+)*'
    num = r'\d+'
    q = hws0 + ',' + hws0
    return sc.cons(
        'RegexSnippets',
        hws0  = hws0,
        hws1  = hws1,
        name  = name,
        num   = num,
        q     = q,
        prog  = name + r'(?:\.\w+)?',
        eol   = hws0 + r'(?=\n)',
        bq    = r'(?<!\\)`',
        bq3   = r'(?<!\\)```',
        pre   = '-',
        quant = hws0 + '|'.join((num + q + num, num + q, q + num, num, q)) + hws0,
    )

@cache
def get_token_types():
    # Convenience vars.
    r = get_regex_snippets()
    p = Pmodes
    pms = {
        '_': (p.variant, p.opt_help, p.section),
        'O': (p.opt_help, p.section),
        'v': (p.variant,),
        'o': (p.opt_help,),
        's': (p.section,),
        '': tuple(),
    }
    # Tuples to define TokTypes.
    tups = (
        # Kind,               Emit, Modes, Regex pattern.
        ('quoted_block',      1,    's',   r.bq3 + r'[\s\S]*?' + r.bq3),
        ('quoted_literal',    1,    '_',   r.bq + r'[\s\S]*?' + r.bq),
        (Tkinds.newline,      0.0,  '_',   r'\n'),
        (Tkinds.indent,       1,    '_',   '(?m)^' + r.hws1 + r'(?=\S)'),
        ('whitespace',        0.0,  '_',   r.hws1),
        ('quant_range',       1,    '_',   r'\{' + r.quant + r'\}'),
        ('paren_open',        1,    '_',   r'\('),
        ('paren_close',       1,    '_',   r'\)'),
        ('brack_open',        1,    '_',   r'\['),
        ('brack_close',       1,    '_',   r'\]'),
        ('angle_open',        1,    '_',   '<'),
        ('angle_close',       1,    '_',   '>'),
        ('choice_sep',        1,    '_',   r'\|'),
        ('triple_dot',        1,    '_',   r'\.\.\.'),
        ('question',          1,    '_',   r'\?'),
        ('long_option',       1,    '_',   r.pre + r.pre + r.name),
        ('short_option',      1,    '_',   r.pre + r'\w'),
        ('section_name',      1,    'v',   r.prog + '?' + r.hws0 + '::' + r.eol),
        ('section_title',     1,    '_',   '.*::' + r.eol),
        ('partial_defintion', 1,    'v',   r.name + '!' + r.hws0 + ':'),
        ('variant_defintion', 1,    'v',   r.name + r.hws0 + ':'),
        ('partial_usage',     1,    'v',   r.name + '!'),
        ('name_assign',       1,    '_',   r.name + r.hws0 + '='),
        ('sym_dest',          1,    '_',   r.name + r.hws0 + '[!.]' + r.hws0 + r.name),
        ('dest',              1,    '_',   '[!.]' + r.hws0 + r.name),
        ('name',              1,    '_',   r.name),
        ('assign',            1,    '_',   '='),
        ('opt_help_sep',      1,    'O',   ':.*'),  # TODO: adjust
    )
    # Create a tuple of all TokTypes.
    tts = tuple(
        TokType(kind, re.compile(patt), pms[m], bool(emit))
        for kind, emit, m, patt in tups
    )

    # Using that tuple, create dict mapping ParserMode to its TokTypes.
    ttmap = {
        pm : OrderedDict((tt.kind, tt) for tt in tts if pm in tt.modes)
        for pm in p.values()
    }

    # Also add some special TokTypes.
    ttmap[Tkinds.special] = OrderedDict(
        (tt.kind, tt)
        for tt in (
            TokType(Tkinds.eof, None, tuple(), False),
            TokType(Tkinds.err, None, tuple(), False),
            TokType(Tkinds.rest, '.+', tuple(), True),
        )
    )

    # Return them as a collection of constants collections.
    return sc.constants('TokenTypes', {
        k : sc.constants('TokenTypes', d)
        for k, d in ttmap.items()
    })

####
# Parsing and grammar constants.
####

Tkinds = sc.constants('TokenKinds', 'eof err indent newline rest special')
Pmodes = sc.constants('ParserModes', 'variant opt_help section')
TokenTypes = get_token_types()

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, token_types = None):
        self.text = text
        self.token_types = token_types
        # Location and token information.
        self.maxpos = len(self.text) - 1
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.isfirst = True
        # Attribute set with Token(eof | err) when lexing finishes.
        self.end = None

    def get_next_token(self, toktype = None):
        # Starting at self.pos, try to emit the next Token.
        #
        # For non-emitted tokens, we break out of the for-loop,
        # but enter the while-loop again. This allows the lexer
        # to be able to ignore any number of non-emitted tokens on each
        # call of the function.
        #
        # The optional toktype argument allows the parser to request a specific
        # TokType directly, bypassing the normal ordering in self.token_types.
        # This is used for opt-help text and its continuation-lines.

        # Return if we are already done lexing.
        if self.end:
            return self.end

        # Normalize input to a tuple of TokType.
        tts = (toktype,) if toktype else self.token_types

        # Return next Token that should be emitted.
        tok = True
        while tok:
            tok = None
            for tt in tts:
                m = tt.regex.match(self.text, pos = self.pos)
                if m:
                    tok = self.create_token(tt.kind, m.group(0))
                    if tt.emit:
                        return tok
                    else:
                        break

        # We have lexed as far as we can.
        # Set self.end to Token(eof) or Token(err).
        kind = (Tkinds.err, Tkinds.eof)[self.pos > self.maxpos]
        self.end = self.create_token(kind, '')
        return self.end

    def create_token(self, kind, text):
        # Get width and newline info.
        width = len(text)
        indexes = [i for i, c in enumerate(text) if c == '\n']
        n_newlines = len(indexes)

        # Create token.
        tok = Token(
            kind = kind,
            text = text,
            width = width,
            pos = self.pos,
            line = self.line,
            col = self.col,
            n_lines = n_newlines + 1,
            isfirst = self.isfirst,
            indent = self.indent,
        )

        # Update location info.
        self.isfirst = False
        self.pos += width
        self.line += n_newlines
        self.col = (
            width - indexes[-1] - 1 if indexes
            else self.col + width
        )

        # Update indent info.
        if tok.kind == Tkinds.newline:
            self.indent = 0
            self.isfirst = True
        elif tok.kind == Tkinds.indent:
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
    next_state = attr.ib()

class SpecParser:

    # General parsing methods (formerly in the mixin).

    def __init__(self, text):
        # The text and the lexer.
        self.text = text
        self.lexer = RegexLexer(text)

        # Info about current token, line, and indent of that line.
        self.curr = None
        self.line = None
        self.indent = None

        # Parser state and associated handlers.
        self.state = None
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
                Handler(self.block_quote, None),
                Handler(self.section_title, None),
                Handler(self.opt_help, None),
            ),
        }

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, s):
        if self.curr:
            # Changing state while caching a prior token seems bad.
            raise ...
        else:
            self._state = s
            self.lexer.tokens = getattr(TokenTypes, s)

    def parse(self):
        tok = self.eat(TokenTypes.opt_help
        if tok:
            return Literal(...)
        else:
            return None


        elems = list(self.do_parse())

        # TODO.
        # Check self.lexer.end

        # TODO.
        # Convert elems to a Grammar.
        # There will be some validation needed here too.
        ...

        # We expect EOF as the final token.
        if not self.curr.isa(EOF):
            self.error()

    def do_parse(self):
        # Consume and yield top-level ParseElem -- namely,
        # section titles, block-quotes, variants, opt-helps.
        elem = True
        while elem:
            for h in self.handlers[self.state]:
                elem = h.method()
                if elem:
                    yield elem
                    # Every top-level ParseElem must start on a fresh line.
                    self.indent = None
                    self.line = None
                    # Advance parser state, if needed.
                    if h.next_state:
                        self.set_state(h.next_state)
                    # Break from inner loop and enter again from beginning.
                    # We will exit outer loop if all handlers return None.
                    break

    def eat(self, *toktypes, taste = False, skip_indent = True, toktype = None):
        # Get the next token, either from self.curr or the lexer.
        # Typically, intervening indent tokens are skipped.
        while True:
            # Get token.
            if self.curr is None:
                self.curr = self.lexer.get_next_token(toktype = toktype)
            tok = self.curr
            # Lexer should deal with EOF, not parser.
            if tok.isa(EOF):
                raise ...
            # Skip indent or break.
            if tok.isa(INDENT) and skip_indent:
                self.curr = None
            else:
                break

        # Check whether token follows indentation/start-of-line rules.
        if self.indent is None:
            # SpecParser has no indent yet. We expect the first token
            # for a variant/opt-help expression. If OK, remember that
            # token's indent and line.
            if tok.is_first:
                self.indent = tok.indent
                self.line = tok.line
                ok = True
            else:
                ok = False
        else:
            # For subsequent tokens in the expression, we expect tokens
            # from the same line or a continuation line indented farther
            # than the first line of the expression.
            if self.line == tok.line:
                ok = True
            elif self.indent < tok.indent:
                self.line = tok.line
                ok = True
            else:
                ok = False

        # Check token type.
        if ok and any(self.curr.isa(tt) for tt in toktypes):
            if tok and not taste:
                self.swallow()
            return tok
        else:
            return None

    def swallow(self):
        if self.curr is None:
            raise ...
        else:
            self.curr = None

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
        return None

    def parse_some(self, method):
        elems = []
        while True:
            e = method()
            if e:
                elems.push(e)
            else:
                break
        return elems

    # ========================================
    # Methods specific to the grammar syntax.

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

    def variant(self):
        # Get variant/partial name, if any.
        defs = (variant-defintion, partial-defintion)
        tok = self.eat(defs, taste = True)
        if tok:
            self.swallow()
            var_name = ...
            is_partial = ...
        else:
            var_name = None
            is_partial = False

        # Collect the ParseElem for the variant.
        # Empty variant means a spec syntax error.
        elems = self.elems()
        if elems:
            return Variant(var_name, is_partial, elems)
        else:
            raise ...

    def opt_help(self):
        elems = self.elems()
        txt = ''
        if self.eat('opt-help-sep'):
            tt = TokType(REST_OF_LINE)
            while True:
                tok = self.eat(toktype = tt, skip_indent = False)
                if tok:
                    txt = txt + ' ' + tok.text.strip()
                if not self.eat('indent', skip_indent = False):
                    break
        return OptHelp(elems, txt.strip())

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
                    e.quantifier = q
                elems.append(e)
            else:
                break
        return elems

    def paren_expression(self):
        elems = self.parenthesized(paren-open, 'elems')
        if elems is None:
            return None
        else:
            return Parenthesized(elems)

    def brack_expression(self):
        elems = self.parenthesized(brack-open, 'elems')
        if elems is None:
            return None
        else:
            return Bracketed(elems)

    def quoted_literal(self):
        tok = self.eat(quoted-literal)
        if tok:
            return Literal(...)
        else:
            return None

    def partial_usage(self):
        tok = self.eat(partial-usage)
        if tok:
            return PartialUsage(...)
        else:
            return None

    def long_option(self):
        return self.option(long-option)

    def short_option(self):
        return self.option(short-option)

    def option(self, option_type):
        tok = self.eat(option_type)
        if tok:
            name = ...
            params = self.parse_some(self.parameter)
            return Opt(name, params, ...)
        else:
            return None

    def positional(self):
        return self.parenthesized(angle-open, 'positional_definition')

    def parameter(self):
        return self.parenthesized(angle-open, 'parameter_definition')

    def positional_definition(self):
        # Get the choices. Positionals require a dest.
        choices = self.choices()
        if not choices.dest:
            raise ...

        # Return Positional or ParameterVariant.
        dest = choices.dest
        vals = choices.vals
        n = len(vals)
        return (
            Positional(dest) if n == 0 else
            PositionalVariant(dest, vals[0]) if n == 1 else
            Positional(dest, vals)
        )

    def parameter_definition(self):
        # Parse the choices expression.
        choices = self.parenthesized(angle-open, 'choices', empty_ok = True)

        # Return early on failure or if we are just peeking.
        if choices is None:
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

    def choices(self):
        # Used for parameters and positionals. Allows the following forms,
        # where x is a destination and V1/V2 are values.
        #   x
        #   x=V1
        #   x=V1|V2|...
        #   =V1
        #   =V1|V2|...

        # Need to parse this differently.
        # Just looking for a name at the front
        # will get confused about these two forms:
        #
        #   <sym>
        #   <val|val|val>
        #
        # There are more tokens to take advantage of now.

        # Get destination, if any.
        tok = self.eat(name)
        if tok:
            dest = ...
        else:
            dest = None

        # Return if no assigned value/choices.
        tok = self.eat(assign)
        if not tok:
            return Choices(dest, tuple())

        # Get value/choices.
        choices = []
        while True:
            val = self.eat((quoted-literal, name))
            if val:
                choices.append(val)
                if not self.eat(choice-sep):
                    break
            else:
                break

        # Return.
        if choices:
            return Choices(dest, tuple(choices))
        else:
            # Return None here: equal without choices is invalid.
            pass

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

    def parenthesized(self, open_tok, method_name, empty_ok = False):
        close_tok = ...
        tok = self.eat(open_tok)
        if tok:
            method = getattr(self, method_name)
            elem = method()
            if not (elem or empty_ok):
                raise ...
            elif self.eat(close_tok):
                return elem
            else:
                raise ...
        else:
            return None

