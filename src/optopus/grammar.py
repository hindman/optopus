import attr
import re
import short_con as sc

pmodes = constants('ParserModes', 'variant opt_help section')

@attr.s
class TokType:
    name = attr.ib()
    regex = attr.ib()
    modes = attr.ib()
    emit = attr.ib()

def con_regex_snippets():
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

def con_token_types():
    rs = con_regex_snippets()
    p = pmodes
    pms = dict(
        _ = (p.variant, p.opt_help, p.section),
        v = (p.variant,),
        o = (p.opt_help,),
        s = (p.section,),
        O = (p.opt_help, p.section),
    )
    tups = (
        # Name,               Emit, Modes, Regex pattern.
        ('quoted_block',      1,    's',   rs.bq3 + r'[\s\S]*?' + rs.bq3),
        ('quoted_literal',    1,    '_',   rs.bq + r'[\s\S]*?' + rs.bq),
        ('newline',           0.0,  '_',   r'\n'),
        ('blank_line',        0.0,  '_',   '(?m)^' + rs.hws + rs.eol),
        ('indent',            1,    '_',   '(?m)^' + rs.hws + '(?=\S)'),
        ('whitespace',        0.0,  '_',   rs.hws),
        ('quant_range',       1,    '_',   r'\{' + rs.quant + r'\}'),
        ('paren_open',        1,    '_',   r'\('),
        ('paren_close',       1,    '_',   r'\)'),
        ('brack_open',        1,    '_',   r'\['),
        ('brack_close',       1,    '_',   r'\]'),
        ('angle_open',        1,    '_',   '<'),
        ('angle_close',       1,    '_',   '>'),
        ('choice_sep',        1,    '_',   r'\|'),
        ('triple_dot',        1,    '_',   r'\.\.\.'),
        ('question',          1,    '_',   r'\?'),
        ('long_option',       1,    '_',   rs.pre + rs.pre + rs.name),
        ('short_option',      1,    '_',   rs.pre + r'\w'),
        ('section_name',      1,    'v',   rs.prog + '?' + rs.hws + '::' + rs.eol),
        ('section_title',     1,    '_',   '.*::' + rs.eol),
        ('partial_defintion', 1,    'v',   rs.name + '!' + rs.hws + ':'),
        ('variant_defintion', 1,    'v',   rs.name + rs.hws + ':'),
        ('partial_usage',     1,    'v',   rs.name + '!'),
        ('name_assign',       1,    '_',   rs.name + rs.hws + '='),
        ('sym_dest',          1,    '_',   rs.name + rs.hws + '[!.]' + rs.hws + rs.name),
        ('dest',              1,    '_',   '[!.]' + rs.hws + rs.name),
        ('name',              1,    '_',   rs.name),
        ('assign',            1,    '_',   '='),
        ('opt_help_sep',      1,    'O',   ':'),
        ('rest_of_line',      1,    ' ',   '.*'),
    )
    return tuple(
        TokType(name, re.compile(patt), pms[m], bool(emit))
        for name, emit, m, patt in tups
    )

class RegexLexer(object):

    def __init__(self, text, token_types = None):
        self.text = text
        self.token_types = token_types
        self.max_pos = len(self.text) - 1
        # Location and other info given to tokens.
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.is_first = True

    def get_next_token(self, toktype = None):
        # Starting at self.pos, try to emit the next Token.
        # If we find a valid token, there are two possibilities:
        #
        # - A Token that we should emit: just return it.
        #
        # - A Token that we should suppress: break out of the for-loop,
        #   but try the while-loop again. This will allow the Lexer
        #   to be able to ignore any number of suppressed tokens.
        #
        # The optional toktype argument allows the parser to request a specific
        # TokType directly, bypassing the normal ordering in self.token_types.
        # This is used for opt-help text (and its continuation-lines).
        #
        tts = (toktype,) if toktype else self.token_types
        tok = True
        while tok:
            for tt in tts:
                tok = self.match_token(tt)
                if tok:
                    if tok.name == 'indent':
                        self.indent = tok.width
                        self.is_first = True
                    if tt.emit:
                        return tok
                    else:
                        break
        # If we did not return a Token above, we should be
        # at the end of the input text.
        if self.pos > self.max_pos:
            return Token(EOF, ...)
        else:
            self.error()

    def match_token(self, rgx, token_type):
        # Search for the token.
        m = rgx.match(self.text, pos = self.pos)
        if not m:
            return None

        # Get matched text, width, and newline info.
        txt = m.group(0)
        width = len(txt)
        indexes = [i for i, c in enumerate(text) if c == NL]
        n_newlines = len(indexes)

        # Create token.
        tok = Token(
            token_type,
            txt,
            width = width,
            pos = self.pos,
            line = self.line,
            col = self.col,
            n_lines = n_newlines + 1,
            is_first = self.is_first,
            indent = self.indent,
        )

        # Update location info.
        self.pos += width
        self.line += n_newlines
        self.col = (
            width - indexes[-1] - 1 if indexes
            else self.col + width
        )
        self.is_first = False

        # Return token.
        return tok

    def error(self):
        fmt = 'RegexLexerError: pos={}'
        msg = fmt.format(self.pos)
        raise RegexLexerError(msg)

