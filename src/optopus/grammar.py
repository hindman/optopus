
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
    p = pmodes
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
        # Name,               Emit, Modes, Regex pattern.
        ('quoted_block',      1,    's',   r.bq3 + r'[\s\S]*?' + r.bq3),
        ('quoted_literal',    1,    '_',   r.bq + r'[\s\S]*?' + r.bq),
        (tkinds.newline,      0.0,  '_',   r'\n'),
        (tkinds.indent,       1,    '_',   '(?m)^' + r.hws1 + r'(?=\S)'),
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
    f = lambda name, emit, m, patt: TokType(
        name,
        re.compile(patt),
        pms[m],
        bool(emit),
    )
    tts = tuple(f(*tup) for tup in tups)
    # Using that tuple, return a constants collection mapping
    # each ParserMode to its relevant TokTypes.
    d = {
        pm : tuple(tt for tt in tts if pm in tt.modes)
        for pm in p.values()
    }
    # Add a few special TokTypes.
    d[tkinds.eof] = TokType(tkinds.eof, None, tuple(), False)
    d[tkinds.err] = TokType(tkinds.err, None, tuple(), False)
    d[tkinds.rest] = TokType(tkinds.rest, '.+', tuple(), True)
    # Return them as a constants collection.
    return sc.constants('TokenTypes', d)

####
# Parsing and grammar constants.
####

pmodes = sc.constants('ParserModes', 'variant opt_help section')
tkinds = sc.cons(
    'TokenKinds',
    eof = 'eof',
    err = 'err',
    indent = 'indent',
    newline = 'newline',
    rest = 'rest',
)
toktypes = get_token_types()

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
        kind = (tkinds.err, tkinds.eof)[self.pos > self.maxpos]
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
        if tok.kind == tkinds.newline:
            self.indent = 0
            self.isfirst = True
        elif tok.kind == tkinds.indent:
            self.indent = tok.width
            self.isfirst = True

        # Return token.
        return tok

