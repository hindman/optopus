'''

Spec tokens:

    Spippet   | Pattern
    ------------------------------------------
    nm        | \w+
    name      | nm ([_-] nm)*
    prog-name | name \. nm
    sp-tab    | [ \t]
    sp-nl     | \s* \n
    num       | \d+
    q         | \s* , \s*
    quant     | num | num q | q num | num q num

    Tokens            | Pattern                     | Note
    ----------------------------------------------------------------
    quoted-block      | ```[\s\S]*?```              | .
    quoted-literal    | `[^`]+?`                    | .
    newline           | \n                          | Ignore
    indent            | ^ sp-tab*                   | Ignore, act
    whitespace        | \s+                         | Ignore
    quantifier-range  | \{ \s* (quant) \s* \}       | .
    paren-open        | \(                          | .
    paren-close       | \)                          | .
    brack-open        | \[                          | .
    brack-close       | \]                          | .
    angle-open        | \<                          | .
    angle-close       | \>                          | .
    choice-sep        | BAR                         | .
    triple-dot        | \.\.\.                      | .
    question          | \?                          | .
    long-option       | -- name                     | .
    short-option      | - nm                        | .
    section-name      | prog-name? sp-tab* :: sp-nl | Grammar
    section-title     | .*? :: sp-nl                | Section, act
    section-variant   | .*? ::                      | .
    partial-defintion | name ! sp-tab* :            | Grammar
    variant-defintion | name sp-tab* :              | Grammar
    partial-usage     | name !                      | Grammar
    name-assign       | name =                      | .
    name-nl           | name sp-nl                  | .
    name              | name                        | .
    assign            | =                           | .
    sym-dot           | [!.]                        | .
    opt-help-text     | : .*                        | .

    Token         | Action
    ------------------------------------------
    indent        | set self.indent
    section-title | set self.state

    Lexer state:

        The state is just a name.

        TokType will have an attribute that can be used to declare the token
        relevent only for specific lexer states. None means all states.

'''

class RegexLexer(object):

    # Modifications to track (LINE, COL)

    def __init__(self, text, token_types):
        self.text = text
        self.token_types = token_types
        self.pos = 0
        self.line = 0
        self.col = 0
        self.state = 1
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
            # Get matched text and locations of newlines inside of it.
            txt = m.group(0)
            indexes = [i for i, c in enumerate(text) if c == NL]
            # Adjust lexer location information.
            n_chars = len(txt)
            n_newlines = len(indexes)
            self.pos += n_chars
            self.line += n_newlines
            if indexes:
                self.col = n_chars - indexes[-1] - 1
            else:
                self.col += n_chars
            # Return Token, including location information.
            return Token(token_type, txt, Loc(self.pos, self.line, self.col))
        else:
            return None

    def error(self):
        fmt = 'RegexLexerError: pos={}'
        msg = fmt.format(self.pos)
        raise RegexLexerError(msg)

    # Is the new code going to need RegexLexer to be iterable?
    # I don't think so. Commenting this out. Iteration does
    # not make sense.

    # def __iter__(self):
    #     self.is_eof = False
    #     return self

    # def __next__(self):
    #     if self.is_eof:
    #         raise StopIteration
    #     else:
    #         tok = self.get_next_token()
    #         if tok.isa(EOF):
    #             self.is_eof = True
    #         return tok

class SpecParser:

    # General parsing methods (formerly in the mixin).

    def __init__(self, text):
        self.text = text
        self.curr = None
        self.prevpeek = None
        self.lexer = RegexLexer(text, SPEC_TOKENS)
        self.handlers = (...)

    def parse(self):
        # Consume and yield as many tokens as we can.
        elem = True
        while elem:
            for func in self.handlers:
                elem = func()
                if elem:
                    yield elem
                    break
        # We expect EOF as the final token.
        if not self.curr.isa(EOF):
            self.error()

    def peek(self, toktype):
        ok = self.do_eat(toktype, peek = True)
        self.prevpeek = toktype
        return ok

    def eat(self, toktype):
        return self.do_eat(toktype)

    def eat_last_peek(self):
        tok = self.do_eat(self.prevpeek)
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
                    self.prevpeek = None
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

    # Methods specific to the grammar syntax.

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
        # Get the choices or raise.
        choices = self.choices()
        if choices:
            dest = choices.dest
            vals = choices.vals
            n = len(vals)
        else:
            raise ...

        # Return Positional or ParameterVariant.
        # Raise if no destination.
        if dest:
            return (
                Positional(dest) if n == 0 else
                PositionalVariant(dest, vals[0]) if n == 1 else
                Positional(dest, vals)
            )
        else:
            raise ...

    def parameter_definition(self):
        # Handle nameless param via underscore.
        # TODO: dropped the nameless-param idea.
        if self.peek(nameless-param):
            return Parameter(None, None)

        # Parse the expression in braces or raise.
        choices = self.parenthesized(brace-open, brace-close, 'choices', empty_ok = True)
        if not choices:
            raise ...

        # Hanlde nameless param via {}.
        if choices.isa(EmptyToken):
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

        # Get destination, if any.
        if self.peek(name):
            tok = self.eat_last_peek()
            dest = ...
        else:
            dest = None

        # Return if no assigned value/choices.
        tok = self.eat(assign)
        if not tok:
            return Choices(dest, tuple())

        # Get value/choices.
        choices = []
        while self.peak((quoted-literal, name)):
            val = self.eat_last_peek()
            choices.append(val)
            if not self.eat(choice-sep):
                break

        # Return.
        return Choices(dest, tuple(choices))

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
        tok = self.eat(triple-dot
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

    def parenthesized(self, open_tok, close_tok, method_name, empty_ok = False):
        if self.peek(open_tok):
            self.eat_last_peek()
            method = getattr(self, method_name)
            tok = method()
            if not (tok or empty_ok):
                raise ...
            elif self.eat(close_tok):
                return tok or EmptyToken
            else:
                raise ...
        else:
            return None

