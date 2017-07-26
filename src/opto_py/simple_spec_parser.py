import sys
import operator
import re

# Token types
WHITESPACE = 'WHITESPACE'
LONG_OPT   = 'LONG_OPT'
SHORT_OPT  = 'SHORT_OPT'
POS_OPT    = 'POS_OPT'
OPT_ARG    = 'OPT_ARG'
EOF        = 'EOF'

# Regex components.
PATT_END      = r'(?=\s|$)'
PATT_OPT_CHAR = r'[\w\-]+'

# Token types and their regexes.
SIMPLE_SPEC_TOKENS = (
    (WHITESPACE , re.compile(r'\s+')),
    (LONG_OPT   , re.compile(r'--' + PATT_OPT_CHAR + PATT_END)),
    (SHORT_OPT  , re.compile(r'-' + PATT_OPT_CHAR + PATT_END)),
    (POS_OPT    , re.compile(r'\<' + PATT_OPT_CHAR + r'\>' + PATT_END)),
    (OPT_ARG    , re.compile(r'[A-Z\d_\-]+' + PATT_END)),
)

class Token(object):

    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def isa(self, *types):
        return self.token_type in types

    def __str__(self):
        fmt = 'Token({}, {!r})'
        msg = fmt.format(self.token_type, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

class LexerError(Exception):
    pass

class RegexLexer(object):

    def __init__(self, text, token_types):
        self.text = text
        self.token_types = token_types
        self.pos = 0
        self.max_pos = len(self.text) - 1

    def get_next_token(self):
        for tt, rgx in self.token_types:
            tok = self.match_token(rgx, tt)
            if tok:
                if not tok.isa(WHITESPACE):
                    return tok
        if self.pos > self.max_pos:
            return Token(EOF, None)
        else:
            self.error()

    def match_token(self, rgx, token_type):
        m = rgx.match(self.text, pos = self.pos)
        if m:
            txt = m.group(0)
            self.pos += len(txt)
            return Token(token_type, txt)
        else:
            return None

    def error(self):
        fmt = 'LexerError: pos={}'
        msg = fmt.format(self.pos)
        raise LexerError(msg)

    def __iter__(self):
        self.is_eof = False
        return self

    def __next__(self):
        while not self.is_eof:
            tok = self.get_next_token()
            if tok.isa(EOF):
                self.is_eof = True
            return tok
        raise StopIteration

class Opt(Token):

    def __init__(self, token):
        self.token_type = token.token_type
        self.value = token.value
        self.nargs = 0

    def __str__(self):
        fmt = 'Opt({}, {!r}, {})'
        msg = fmt.format(self.token_type, self.value, self.nargs)
        return msg

    def __repr__(self):
        return self.__str__()

class Parser(object):

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def parse(self):
        opts = []
        while self.current_token.isa(LONG_OPT, SHORT_OPT, POS_OPT):
            tok = self.current_token
            opt = None
            if tok.isa(LONG_OPT):
                opt = self.long_opt()
            elif tok.isa(SHORT_OPT):
                opt = self.short_opt()
            elif tok.isa(POS_OPT):
                opt = self.pos_opt()
            if opt:
                opts.append(opt)
        return opts

    def long_opt(self):
        tok = self.current_token
        opt = Opt(tok)
        self.eat(LONG_OPT)
        while self.current_token.isa(OPT_ARG):
            opt.nargs += 1
            self.eat(OPT_ARG)
        return opt

    def short_opt(self):
        tok = self.current_token
        opt = Opt(tok)
        self.eat(SHORT_OPT)
        while self.current_token.isa(OPT_ARG):
            opt.nargs += 1
            self.eat(OPT_ARG)
        return opt

    def pos_opt(self):
        tok = self.current_token
        opt = Opt(tok)
        self.eat(POS_OPT)
        return opt

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

    def eat(self, token_type):
        if self.current_token.isa(token_type):
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

DEFAULT_TEXT = ' --foo FF GG  -x --blort -z Z1 Z2 <qq> <rr>  --debug  ' 

def main(args):

    text = args[0] if args else DEFAULT_TEXT
    lexer = RegexLexer(text, SIMPLE_SPEC_TOKENS)

    parser = Parser(lexer)
    opts = parser.parse()
    for opt in opts:
        print(opt)

if __name__ == '__main__':
    main(sys.argv[1:])

