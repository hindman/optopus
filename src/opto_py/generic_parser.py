from .token import EOF

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

