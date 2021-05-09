# TODO:
# - Setup constants better
# - Proof
# - Test.

import attr
import re
import short_con as sc
from functools import cache
from collections import OrderedDict

pmodes = constants('ParserModes', 'variant opt_help section')

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

@cache
def get_regex_snippets():
    hws = r'[ \t]*'
    name = r'\w+(?:[_-]\w+)*'
    num = r'\d+'
    q = hws + ',' + hws
    return sc.cons(
        'Snippets',
        hws   = hws,
        name  = name,
        num   = num,
        q     = q,
        prog  = name + r'(?:\.\w+)?',
        eol   = hws + r'(?=\n)',
        bq    = r'(?<!\\)`',
        bq3   = r'(?<!\\)```',
        pre   = '-',
        quant = hws + '|'.join(num + q + num, num + q, q + num, num, q) + hws,
    )

@cache
def get_token_types():
    r = get_regex_snippets()
    p = pmodes
    pms = {
        '_': (p.variant, p.opt_help, p.section),
        'O': (p.opt_help, p.section),
        'v': (p.variant,),
        'o': (p.opt_help,),
        's': (p.section,),
        '': tuple(),
    }
    tups = (
        # Name,               Emit, Modes, Regex pattern.
        ('quoted_block',      1,    's',   r.bq3 + r'[\s\S]*?' + r.bq3),
        ('quoted_literal',    1,    '_',   r.bq + r'[\s\S]*?' + r.bq),
        ('newline',           0.0,  '_',   r'\n'),
        ('blank_line',        0.0,  '_',   '(?m)^' + r.hws + r.eol),
        ('indent',            1,    '_',   '(?m)^' + r.hws + '(?=\S)'),
        ('whitespace',        0.0,  '_',   r.hws),
        ('quant_range',       1,    '_',   r'\{' + r.quant + r'\}'),
        ('paren_open',        1,    '_',   r'\('),
        ('paren_close',       1,    '_',   r'\)'),
        ('brack_open',        1,    '_',   r'\['),
        ('brack_close',       1,    '_',   r'\]'),
        ('angle_open',        1,    '_',   '<'),
        ('angle_close',       1,    '_',   '>'),
        ('choice_sep',        1,    '_',   r'\ | '),
        ('triple_dot',        1,    '_',   r'\.\.\.'),
        ('question',          1,    '_',   r'\?'),
        ('long_option',       1,    '_',   r.pre + r.pre + r.name),
        ('short_option',      1,    '_',   r.pre + r'\w'),
        ('section_name',      1,    'v',   r.prog + '?' + r.hws + '::' + r.eol),
        ('section_title',     1,    '_',   '.*::' + r.eol),
        ('partial_defintion', 1,    'v',   r.name + '!' + r.hws + ':'),
        ('variant_defintion', 1,    'v',   r.name + r.hws + ':'),
        ('partial_usage',     1,    'v',   r.name + '!'),
        ('name_assign',       1,    '_',   r.name + r.hws + '='),
        ('sym_dest',          1,    '_',   r.name + r.hws + '[!.]' + r.hws + r.name),
        ('dest',              1,    '_',   '[!.]' + r.hws + r.name),
        ('name',              1,    '_',   r.name),
        ('assign',            1,    '_',   '='),
        ('opt_help_sep',      1,    'O',   ':'),
        ('rest_of_line',      1,    '',    '.*'),
        ('EOF',               0.0,  '',    '\Z'),
        ('ERR',               0.0,  '',    '\Z'),
    )
    d = OrderedDict(
        (name, TokType(name, re.compile(patt), pms[m], bool(emit)))
        for name, emit, m, patt in tups
    )
    return sc.constants('TokenTypes', d)

class RegexLexer(object):

    def __init__(self, text, toktypes = None):
        self.text = text
        self.toktypes = toktypes
        self.maxpos = len(self.text) - 1
        # Location and token information.
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.isfirst = True
        # Attribute set with Token(eof|err) when lexing finishes.
        self.end = None

    def get_next_token(self, toktype = None):
        # Starting at self.pos, try to emit the next Token.
        # If we find a valid token, there are two possibilities:
        #
        # - A Token that we should emit: just return it.
        #
        # - A Token that we should suppress: break out of the for-loop,
        #   but try the while-loop again. This will allow the Lexer
        #   to be able to ignore any number of suppressed tokens on each
        #   call of the function.
        #
        # The optional toktype argument allows the parser to request a specific
        # TokType directly, bypassing the normal ordering in self.toktypes.
        # This is used for opt-help text (and its continuation-lines).

        # Return if we are already done lexing.
        if self.end:
            return self.end

        # Normalize input to a tuple of TokType.
        tts = (toktype,) if toktype else self.toktypes

        # Return next Token that should be emitted.
        tok = True
        while tok:
            for tt in tts:
                m = tt.regex.match(self.text, pos = self.pos)
                if m:
                    tok = self.create_token(tt.name, m.group(0))
                    if tt.emit:
                        return tok
                    else:
                        break

        # We have lexed as far as we can.
        # Set self.end to Token(eof) or Token(err).
        tt = getattr(
            get_token_types(),
            'eof' if self.pos > self.maxpos else 'err'
        )
        self.end = self.create_token(tt, '')
        return self.end

    def create_token(self, kind, text):
        # Get width and newline info.
        width = len(text)
        indexes = [i for i, c in enumerate(text) if c == NL]
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
        if tok.name == 'indent':
            self.indent = tok.width
            self.isfirst = True

        # Return token.
        return tok

