'''

TODO:

    - In sections, text is now assumed to be syntax unless it is block-quoted,
    which eliminates the need for extended peeks.

    - Sketch of parsing states, handlers, and state transitions:

        state = grammar-check:
        handlers : []

            peek for section-variant
            yes:
                state = grammar-opt-help 
                handlers : [section_title, opt_help]
                on section_title: state = section-opt-help
            else:
                state = grammar-variant
                handlers : [section_title, variant]
                on section_title: state = section-opt-help

        section-opt-help
            handlers : [block_quote, section_title, opt_help]
            on block_quote: state = section-other

        section-other
            handlers : [block_quote, other_line]
            on block_quote: state = section-opt-help

    - Convert RegexLexer and SpecParser back to simple peeks only:

        - Just use self.curr.
        - When reverting, do not return to eat_last_peek().

    - Set up the handlers, state management, and top-level SpecParser.parse().

    - Adjust other code accordingly.

        - It might not be necessary to complete the draft.

        - Perhaps sufficient to adjust a couple of the more complex methods and
        then just move on to real implementation.

        - There is now sufficient clarity to move to implementation.

Spec tokens:

    Spippet   | Pattern
    ------------------------------------------
    nm        | \w+
    name      | nm ([_-] nm)*
    prog-name | name ( \. nm )?
    hws       | [ \t]
    eol       | hws* \n
    num       | \d+
    q         | hws* , hws*
    quant     | num | q | q num | num q | num q num

    Tokens            | Pattern                 | Note
    ----------------------------------------------------------------
    quoted-block      | ```[\s\S]*?```          | .
    quoted-literal    | `[^`]*?`                | .
    newline           | \n                      | Ignore
    indent            | ^ hws*                  | Ignore, act
    whitespace        | hws*                    | Ignore
    quantifier-range  | \{ hws* (quant) hws* \} | .
    paren-open        | \(                      | .
    paren-close       | \)                      | .
    brack-open        | \[                      | .
    brack-close       | \]                      | .
    angle-open        | \<                      | .
    angle-close       | \>                      | .
    choice-sep        | BAR                     | .
    triple-dot        | \.\.\.                  | .
    question          | \?                      | .
    long-option       | -- name                 | .
    short-option      | - nm                    | .
    section-name      | prog-name? hws* :: eol  | Grammar
    section-title     | .*? :: eol              | Section, act
    section-variant   | .*? ::                  | .
    partial-defintion | name ! hws* :           | Grammar
    variant-defintion | name hws* :             | Grammar
    partial-usage     | name !                  | Grammar
    name-assign       | name hws* =             | .
    sym-dest          | name hws* \. hws* name  | .
    name-nl           | name eol                | .
    name              | name                    | .
    assign            | =                       | .
    sym-dot           | [!.]                    | .
    opt-help-text     | : .*                    | .

    Token         | Action
    ------------------------------------------
    indent        | set self.indent
    section-title | set self.state

    Lexer state:

        The state is just a name.

        TokType will have an attribute that can be used to declare the token
        relevant only for specific lexer states. None means all states.

'''

class RegexLexer(object):

    def __init__(self, text, token_types):
        self.text = text
        self.token_types = token_types
        self.loc = Loc(0, 0, 0)
        self.max_pos = len(self.text) - 1

    def get_next_token(self, ploc = None):
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
                tok = self.match_token(rgx, tt, ploc)
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

    def match_token(self, rgx, token_type, ploc = None):
        # This method is a non-standard in having two behaviors:
        #
        # - Returns Token or None.
        # - If Token: updates either ploc or self.loc.
        #
        # The dual behavior eliminates bookkeeping hassle for
        # peeking callers.

        # Search for the token.
        loc = ploc or self.loc
        m = rgx.match(self.text, pos = loc.pos)
        if not m:
            return None

        # Get matched text and locations of newlines inside of it.
        txt = m.group(0)
        indexes = [i for i, c in enumerate(text) if c == NL]

        # Update location information.
        width = len(txt)
        n_newlines = len(indexes)
        loc.pos += width
        loc.line += n_newlines
        loc.col = (
            width - indexes[-1] - 1 if indexes
            else loc.col + width
        )

        # Return token.
        tok = Token(token_type, txt, width, loc)
        return tok

    def error(self):
        fmt = 'RegexLexerError: loc={}'
        msg = fmt.format(self.loc)
        raise RegexLexerError(msg)

    # I do not think the new code need RegexLexer to be iterable --
    # or even that it makes sense for this use case.
    #
    # Dropping:
    #   __iter__()
    #   __next__()

class SpecParser:

    # General parsing methods (formerly in the mixin).

    def __init__(self, text):
        self.text = text
        self.curr = None
        self.lexer = RegexLexer(text, SPEC_TOKENS)
        self.handlers = (...)

    def parse(self):
        # Consume and yield as many ParseElem as we can.
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

    # ========================================
    # New eat() method.
    # ========================================

    def eat(self, toktype, ploc = None):
        # Normalize input to tuple(TokenType).
        tts = (toktype,) if isinstance(x, TokenType) else tuple(toktype)

        # Validate.
        if not tts:
            raise ...

        # Get the token.
        if ploc:
            tok = self.lexer.get_next_token(ploc)
        else:
            self.curr = self.curr or self.lexer.get_next_token()
            tok = self.curr
            if tok.isa(EOF):
                raise ...

        # Check token against destire type(s).
        for tt in tts:
            if tok.isa(tt):
                if not ploc:
                    self.curr = None
                return tok

        # Fail.
        return None

    # ========================================
    # OLD eat/peek methods.
    # ========================================

    # def peek(self, toktype):
    #     ok = self.do_eat(toktype, peek = True)
    #     self.prevpeek = toktype
    #     return ok

    # def eat(self, toktype):
    #     return self.do_eat(toktype)

    # def eat_last_peek(self):
    #     tok = self.do_eat(self.prevpeek)
    #     if tok:
    #         return tok
    #     else:
    #         raise ...

    # def do_eat(self, toktype, peek = False):
    #     # Normalize input to tuple(TokenType).
    #     tts = (toktype,) if isinstance(x, TokenType) else tuple(toktype)
    #
    #     # Validate.
    #     if not tts:
    #         raise ...
    #
    #     # Pull from lexer.
    #     if self.curr is None:
    #         self.curr = self.lexer.get_next_token()
    #         if self.curr.isa(EOF):
    #             raise ...
    #
    #     # Check.
    #     for tt in tts:
    #         if self.curr.isa(tt):
    #             if peek:
    #                 return True
    #             else:
    #                 tok = self.curr
    #                 self.curr = None
    #                 self.prevpeek = None
    #                 return tok
    #
    #     # Fail.
    #     return False if peek else None

    # ========================================

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

    def parse_first(self, methods, ploc = None):
        init = attr.evolve(ploc) if ploc else None
        for m in methods:
            x = m(ploc)
            if x:
                return True if ploc else x
            elif ploc:
                ploc.pos = init.pos
                ploc.line = init.line
                ploc.col = init.col
        return None

    def parse_some(self, method, ploc = None, require = 0):
        init = attr.evolve(ploc) if ploc else None
        xs = []
        while True:
            x = method(ploc)
            if x:
                xs.push(x)
            else:
                break
        if len(xs) >= require:
            return True if ploc else tuple(xs)
        else:
            raise ...

    # ========================================
    # Methods specific to the grammar syntax.

    def variant(self, ploc = None):

        # Scenarios:
        # - Called by a peeking handler | Forward ploc: return bool
        # - Need peek and ploc          | Create fresh ploc
        # - Need peek but not ploc      | Just eat
        # - Eat directly                | Eat
        # - Eat last peek               | Drop this

        # Setup.
        defs = (variant-defintion, partial-defintion)

        # Handle a forwarded peek.
        if ploc:
            return (
                self.eat(defs, ploc) and
                self.parse_some(self.expression, ploc)
            )

        # Variant.
        tok = self.eat(defs)
        if tok:
            var_name = ...
            is_partial = ...
            exprs = self.parse_some(self.expression)
            if exprs:
                return Variant(var_name, is_partial, exprs)
            else:
                raise ...
        else:
            return None

    def expresion(self, ploc = None):
        elems = self.parse_some(self.element, ploc)
        return bool(elems) if ploc else Expression(elems)

    def element(self, ploc = None):
        element_methods = (
            self.quoted_literal,
            self.partial_usage,
            self.paren_expression,
            self.brack_expression,
            self.positional,
            self.long_option,
            self.short_option,
        )
        e = self.parse_first(element_methods, ploc)
        if ploc:
            return bool(e)
        elif e:
            q = self.quantifier(ploc)
            if q:
                e.quantifier = q
        return e

    def paren_expression(self, ploc = None):
        return self.parenthesized(paren-open, 'expression', ploc)

    def brack_expression(self, ploc = None):
        return self.parenthesized(brack-open, 'expression', ploc)

    def quoted_literal(self, ploc = None):
        tok = self.eat(quoted-literal, ploc)
        if ploc:
            return bool(tok)
        elif tok:
            return Literal(...)
        else:
            return None

    def partial_usage(self, ploc = None):
        tok = self.eat(partial-usage, ploc)
        if ploc:
            return bool(tok)
        elif tok:
            return PartialUsage(...)
        else:
            return None

    def long_option(self, ploc = None):
        return self.option(long-option, ploc)

    def short_option(self, ploc = None):
        return self.option(short-option, ploc)

    def option(self, option_type, ploc = None):
        tok = self.eat(option_type, ploc)
        if ploc:
            return bool(tok)
        elif tok:
            name = ...
            params = self.parse_some(self.parameter, ploc)
            return Opt(name, params, ...)
        else:
            return None

    def positional(self, ploc = None):
        return self.parenthesized(angle-open, 'positional_definition', ploc)

    def parameter(self, ploc = None):
        return self.parenthesized(brace-open, 'parameter_definition', ploc)

    def positional_definition(self, ploc = None):
        # Get the choices. Positionals require a dest.
        choices = self.choices(ploc)
        if ploc:
            return bool(choices.dest)
        elif not choices.dest:
            raise ...

        # Return Positional or ParameterVariant.
        dest = choices.dest
        vals = choices.vals
        n = len(vals)
        return (
            Positional(dest) if n == 0 else
            PositionalVariant(dest, vals[0]) if n == 1 else
            Positional(dest, vals)
        )

    def parameter_definition(self, ploc = None):
        # Parse the choices expression.
        choices = self.parenthesized(angle-open, 'choices', ploc, empty_ok = True)

        # Return early on failure or if we are just peeking.
        if ploc:
            return bool(choices.dest)
        elif choices is None:
            return None

        # Handle nameless param <>.
        if not (choices.dest or choices.vals):
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

    def choices(self, ploc = None):
        # Used for parameters and positionals. Allows the following forms,
        # where x is a destination and V1/V2 are values.
        #   x
        #   x=V1
        #   x=V1|V2|...
        #   =V1
        #   =V1|V2|...

        # Need to parse this differently.
        # Just looking for a name at the front
        # will get confused about these two forms:
        #
        #   <sym>
        #   <val|val|val> 
        #
        # There are more tokens to take advantage of now.

        # Get destination, if any.
        tok = self.eat(name, ploc)
        if tok:
            dest = ...
        else:
            dest = None

        # Return if no assigned value/choices.
        tok = self.eat(assign, ploc)
        if not tok:
            return True if ploc else Choices(dest, tuple())

        # Get value/choices.
        choices = []
        while True:
            val = self.eat((quoted-literal, name), ploc)
            if val:
                choices.append(val)
                if not self.eat(choice-sep, ploc):
                    break
            else:
                break

        # Return.
        if choices:
            return True if ploc else Choices(dest, tuple(choices))
        else:
            # Return None here: equal without choices is invalid.
            pass

    def quantifier(self, ploc = None):
        quantifier_methods = (
            self.one_or_more_dots,
            self.quantifier_range,
        )
        q = self.parse_first(quantifier_methods, ploc)
        if ploc:
            return bool(q)
        elif q:
            greedy = not self.eat(question, ploc)
            return Quantifier(q, greedy)
        else:
            return None

    def one_or_more_dots(self, ploc = None):
        tok = self.eat(triple-dot, ploc)
        if ploc:
            return bool(tok)
        elif tok:
            return (1, None)
        else:
            return None

    def quantifier_range(self, ploc = None):
        tok = self.eat(quantifier-range, ploc)
        if ploc:
            return bool(tok)
        elif tok:
            ...
            return (..., ...)
        else:
            return None

    def parenthesized(self, open_tok, method_name, ploc = None, empty_ok = False):
        close_tok = ...
        tok = self.eat(open_tok, ploc)
        if tok:
            method = getattr(self, method_name)
            elem = method(ploc)
            if not (elem or empty_ok):
                raise ...
            elif self.eat(close_tok, ploc):
                return True if ploc else elem
            else:
                raise ...
        else:
            return None

