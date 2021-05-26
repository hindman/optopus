
# TODO: Better errors so I can debug failed parses: start with the failed-to-parse-full-spec.

# TODO: Get the test working.

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

@attr.s(frozen = True)
@attrcls('sym dest symlit val vals')
class SymDest:
    pass

@attr.s(frozen = True)
@attrcls('sym dest symlit choices')
class Positional:
    pass

@attr.s(frozen = True)
@attrcls('dest params')
class Option:
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
        ('sym_dest',       1,    '_',   c(r.name) + hw + c('[!.]') + hw + c(r.name)),
        ('dot_dest',       1,    '_',   r'\.' + hw + c(r.name)),
        ('solo_dest',      1,    '_',   c(r.name) + hw + r'(?=>)'),
        ('name',           1,    '_',   r.name),
        ('assign',         1,    '_',   '='),
        ('opt_help_sep',   1,    'O',   ':'),
        ('choice_val',     1,    '_',   r'[^\s|>]+'),
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
    exclamation = '!',
    comma = ',',
)
ParenPairs = {
    TokDefs.paren_open: TokDefs.paren_close,
    TokDefs.brack_open: TokDefs.brack_close,
    TokDefs.angle_open: TokDefs.angle_close,
}

####
# Lexer.
####

class RegexLexer(object):

    def __init__(self, text, tokdefs = None):
        self.text = text
        self.tokdefs = tokdefs
        self.maxpos = len(self.text) - 1

        # Location and token information.
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.isfirst = True
        self.prev_loc = None

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
        m = re.search('^$', '')
        self.end = self.create_token(td, m)
        return self.end

    def set_location(self, revert = False):
        if revert and not self.prev_loc:
            msg = 'Cannot set_location(revert) if self.prev_loc is unset'
            raise Exception(msg)
        elif revert:
            t = self.prev_loc
            self.pos = t[0]
            self.line = t[1]
            self.col = t[2]
            self.indent = t[3]
            self.isfirst = t[4]
            self.prev_loc = None
        else:
            self.prev_loc = (
                self.pos,
                self.line,
                self.col,
                self.indent,
                self.isfirst,
            )

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

        # Remember the current location info.
        self.set_location()

        # Update location info based on recently consumed Token.
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

        # Parsing modes. First defines the handlers for each
        # mode. Then set the initial mode.
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
        self.mode = Pmodes.variant

    ####
    # Setting the parser mode.
    ####

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        if self.curr:
            self.lexer.set_location(revert = True)
            self.curr = None
        else:
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
        e = self.lexer.end
        if not (e and e.isa(TokDefs.eof)):
            msg = 'Failed to parse the full spec'
            raise Exception(msg)

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

            # Skip indents, unless lex_tokdef.
            if tok.isa(TokDefs.indent) and not lex_tokdef:
                self.curr = None
                continue

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
            if tok.isfirst:
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
            msg = 'Cannot swallow() unless self.curr is defined'
            raise Exception(msg)
        else:
            self.curr = None

    ####
    # Top-level ParseElem handlers.
    ####

    def variant(self):
        # Get variant/partial name, if any.
        tds = (TokDefs.variant_def, TokDefs.partial_def)
        tok = self.eat(*tds, taste = True)
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
            msg = 'A Variant cannot be empty'
            raise Exception(msg)

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
                if not self.eat(lex_tokdef = TokDefs.indent):
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
        elems = []
        while True:
            e = self.parse_first(
                self.quoted_literal,
                self.partial_usage,
                self.paren_expression,
                self.brack_expression,
                self.positional,
                self.long_option,
                self.short_option,
            )
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

    def positional(self):
        # Try to get a SymDest elem.
        sd = self.parenthesized(TokDefs.angle_open, self.symdest, for_pos = True)
        if not sd:
            return None

        # Return Positional or PositionalVariant.
        xs = (sd.sym, sd.dest, sd.symlit)
        if sd.val is None:
            return Positional(*xs, choices = sd.vals)
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

    def symdest(self, for_pos = True):
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
                # Handle <.dest>, <dest>, or <sym>.
                txt = tok.m.group(1)
                if for_pos or tok.isa(TokDefs.dot_dest):
                    dest = txt
                else:
                    sym = txt
        elif for_pos:
            msg = 'Positionals require at least a dest'
            raise Exception(msg)

        # Try to get the dest assign equal-sign.
        # For now, treat this as optional.
        assign = self.eat(TokDefs.assign)

        # Try to get choice values.
        vals = []
        while True:
            tok = self.eat(TokDefs.quoted_literal, TokDefs.choice_val, taste = True)
            if not tok:
                break

            # If we got one, and if we already had a sym or dest,
            # the assign equal sign becomes required.
            if (sym or dest) and not assign:
                msg = 'Found choice values without required equal sign'
                raise Exception(msg)

            # Consume and store.
            self.swallow()
            i = 1 if tok.isa(TokDefs.quoted_literal) else 0
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
            greedy = not self.eat(question)
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
                raise Exception(msg)
            elif self.eat(td_close):
                return elem
            else:
                msg = 'Failed to find closing paren/bracket'
                raise Exception(msg)
        else:
            return None

    ####
    # Other stuff.
    ####

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

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
                elems.push(e)
            else:
                break
        return elems

