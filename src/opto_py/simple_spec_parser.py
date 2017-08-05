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

# Token types:
# - The type.
# - Whether the RegexLexer should emit the tokens of this type.
# - The regex to match the token.
SIMPLE_SPEC_TOKENS = (
    (WHITESPACE, False, re.compile(r'\s+')),
    (LONG_OPT,   True,  re.compile(r'--' + PATT_OPT_CHAR + PATT_END)),
    (SHORT_OPT,  True,  re.compile(r'-' + PATT_OPT_CHAR + PATT_END)),
    (POS_OPT,    True,  re.compile(r'\<' + PATT_OPT_CHAR + r'\>' + PATT_END)),
    (OPT_ARG,    True,  re.compile(r'[A-Z\d_\-]+' + PATT_END)),
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

class RegexLexerError(Exception):
    pass

class RegexLexer(object):

    def __init__(self, text, token_types):
        self.text = text
        self.token_types = token_types
        self.pos = 0
        self.max_pos = len(self.text) - 1

    def get_next_token(self):
        # Starting at self.pos, try to emit the next Token.
        # If we find a valid token, there are two possibilities:
        #
        # - A Token that we should emit: just return it.
        #
        # - A Token that we should suppress: break out of the for-loop,
        #   but try the while-loop again. This will allow the Lexer
        #   to be able to ignore any number of suppressed tokens.
        #
        tok = True
        while tok:
            for tt, emit, rgx in self.token_types:
                tok = self.match_token(rgx, tt)
                if tok:
                    if emit:
                        return tok
                    else:
                        break
        # If we did not return a Token above, we should be
        # at the end of the input text.
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
        fmt = 'RegexLexerError: pos={}'
        msg = fmt.format(self.pos)
        raise RegexLexerError(msg)

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

class GenericParser(object):

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()
        self.parser_functions = tuple()

    def parse(self):
        elem = True
        while elem:
            for func in self.parser_functions:
                elem = func()
                if elem:
                    yield elem
                    break
        if not self.current_token.isa(EOF):
            self.error()

    def eat(self, token_type):
        # If the current Token is of the expected type, return it
        # after advancing the lexer. Otherwise, return None.
        tok = self.current_token
        if tok.isa(token_type):
            self.current_token = self.lexer.get_next_token()
            return tok
        else:
            return None

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

class SimpleSpecParser(GenericParser):

    ####
    #
    # To implement a parser:
    #
    # - Inherit from GenericParser.
    #
    # - Define one or more parser_functions.
    #
    # - Each of those functions should return some data element
    #   appropriate for the grammar (if the current Token matches)
    #   or None.
    #
    ####

    def __init__(self, lexer):
        super(SimpleSpecParser, self).__init__(lexer)
        self.parser_functions = (
            self.long_opt,
            self.short_opt,
            self.pos_opt,
        )

    def long_opt(self):
        return self._opt(LONG_OPT)

    def short_opt(self):
        return self._opt(SHORT_OPT)

    def pos_opt(self):
        tok = self.eat(POS_OPT)
        return Opt(tok) if tok else None

    def _opt(self, opt_type):
        # If the current Token is not the expected option type, bail out.
        # Otherwise, count the N of OPT_ARG that the Opt takes.
        tok = self.eat(opt_type)
        if not tok:
            return None
        opt = Opt(tok)
        while tok:
            tok = self.eat(OPT_ARG)
            if tok:
                opt.nargs += 1
        return opt

def main(args):

    DEFAULT_TEXT = ' --foo FF GG  -x --blort -z Z1 Z2 <qq> <rr>  --debug  '

    text = args[0] if args else DEFAULT_TEXT
    lexer = RegexLexer(text, SIMPLE_SPEC_TOKENS)

    parser = SimpleSpecParser(lexer)
    for opt in parser.parse():
        print(opt)

if __name__ == '__main__':
    main(sys.argv[1:])

