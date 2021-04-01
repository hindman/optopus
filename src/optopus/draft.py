
class GenericParserMixin:

    def __init__(self):
        self.curr = None
        self.last_peek = []

    def parse(self):
        # Consume and yield as many tokens as we can.
        elem = True
        while elem:
            for func in self.parser_functions:
                elem = func()
                if elem:
                    yield elem
                    break
        # We expect EOF as the final token.
        if not self.current_token.isa(EOF):
            self.error()

    def peek(self, toktype):
        ok = self.do_eat(toktype, peek = True)
        self.last_peek = toktype
        return ok

    def eat(self, toktype):
        return self.do_eat(toktype)

    def eat_last_peek(self):
        tok = self.do_eat(self.last_peek)
        if tok:
            return tok
        else:
            raise ...

    def do_eat(self, toktype, peek = False):
        # Normalize input to tuple(TokenType).
        tts = (toktype,) if isinstance(x, TokenType) else tuple(toktype)

        # Validate.
        if not tts:
            raise ...

        # Pull from lexer.
        if self.curr is None:
            self.curr = self.lexer.get_next_token()
            if self.curr.isa(EOF):
                raise ...

        # Check.
        for tt in tts:
            if self.curr.isa(tt):
                if peek:
                    return True
                else:
                    tok = self.curr
                    self.curr = None
                    self.last_peek = None
                    return tok

        # Fail.
        return False if peek else None

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

    def parse_first(self, *methods):
        for m in methods:
            x = m()
            if x:
                return x
        return None

    def parse_some(self, method, require = 0):
        xs = []
        while True:
            x = method()
            if x:
                xs.push(x)
            else:
                break
        if len(xs) >= require:
            return xs
        else:
            raise ...

class GrammarParser:

    def variant(self):
        if self.peek((variant-defintion, partial-defintion)):
            tok = self.eat_last_peek()
            var_name = ...
            is_partial = ...
            exprs = self.parse_some(self.expression)
            if exprs:
                return Variant(var_name, is_partial, exprs)
            else:
                raise ...
        else:
            return None

    def expresion(self):
        elems = self.parse_some(self.element)
        return Expression(elems)

    def element(self):
        element_methods = [
            self.quoted_literal,
            self.partial_usage,
            self.paren_expression,
            self.brack_expression,
            self.positional,
            self.long_option,
            self.short_option,
        ]
        e = self.parse_first(*element_methods)
        if e:
            q = self.quantifier()
            if q:
                e.quantifier = q
        return e

    def paren_expression(self):
        return self.parenthesized(paren-open, paren-close, 'expression')

    def brack_expression(self):
        return self.parenthesized(brack-open, brack-close, 'expression')

    def quoted_literal(self):
        if self.peek(quoted-literal):
            tok = self.eat_last_peek()
            return Literal(...)
        else:
            return None

    def partial_usage(self):
        if self.peek(partial-usage):
            tok = self.eat_last_peek()
            return PartialUsage(...)
        else:
            return None

    def long_option(self):
        return self.option(long-option)

    def short_option(self):
        return self.option(long-option)

    def option(self, option_type):
        if self.peek(option_type):
            tok = self.eat_last_peek()
            name = ...
            params = self.parse_some(self.parameter)
            return Opt(name, params, ...)
        else:
            return None

    def positional(self):
        return self.parenthesized(angle-open, angle-close, 'positional_definition')

    def parameter(self):
        return self.parenthesized(brace-open, brace-close, 'parameter_definition')

    def positional_definition(self):
        # Destination assignment.
        if self.peek(destination):
            tok = self.eat_last_peek()
            dest = ...
            choices = self.choices()
            if not choices:
                raise ...
            elif len(choices) == 1:
                return PositionalVariant(dest, value = ...)
            else:
                return Positional(dest, choices = choices)
        # Simple positional.
        if self.peek(name):
            tok = self.eat_last_peek()
            dest = ...
            return Positional(dest)
        else:
            raise ...

    def parameter_definition(self):
        # TODO
        # -p {}        -p {x}        Parameter.
        # -p _         .             Parameter.
        # -p {=a|b}    -p {x=a|b}    Parameter choices.
        # -p {=foo}    -p {x=foo}    Parameter variant.

    def choices(self):
        # TODO
        # 'literal value'
        # name

    def quantifier(self):
        quantifier_methods = [
            self.one_or_more_dots,
            self.one_or_more,
            self.zero_or_more,
            self.zero_or_one,
            self.quantifier_range,
        ]
        q = self.parse_first(*quantifier_methods)
        if q:
            greedy = not self.eat(question)
            return Quantifier(q, greedy)
        else:
            return None

    def one_or_more_dots(self):
        tok = self.eat(one-or-more-dots)
        return (1, None) if tok else None

    def one_or_more(self):
        tok = self.eat(one-or-more)
        return (1, None) if tok else None

    def zero_or_more(self):
        tok = self.eat(zero-or-more)
        return (0, None) if tok else None

    def zero_or_one(self):
        tok = self.eat(question)
        return (0, 1) if tok else None

    def quantifier_range(self):
        if self.peek(quantifier-range):
            tup = self.eat_last_peek()
            return tup
        else:
            return None

    def parenthesized(self, open_tok, close_tok, method_name):
        if self.peek(open_tok):
            self.eat_last_peek()
            method = getattr(self, method_name)
            tok = method()
            if not tok:
                raise ...
            if self.eat(close_tok):
                return tok
            else:
                raise ...
        else:
            return None

