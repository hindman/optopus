from .generic_parser import GenericParser
from .opt import Opt
from .regex_lexer import RegexLexer
from .token import (
    Token,
    WHITESPACE,
    LONG_OPT,
    SHORT_OPT,
    POS_OPT,
    OPT_ARG,
    EOF,
    SIMPLE_SPEC_TOKENS,
)


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

    def __init__(self, text):
        lexer = RegexLexer(text, SIMPLE_SPEC_TOKENS)
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
        if tok:
            return Opt(tok.value)
        else:
            return None

    def _opt(self, opt_type):
        # If the current Token is not the expected option type, bail out.
        # Otherwise, count the N of OPT_ARG that the Opt takes.
        tok = self.eat(opt_type)
        if not tok:
            return None
        opt = Opt(tok.value)
        while tok:
            tok = self.eat(OPT_ARG)
            if tok:
                opt.nargs += 1
        return opt

