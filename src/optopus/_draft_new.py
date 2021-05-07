
class SpecParser:

    # General parsing methods (formerly in the mixin).

    def __init__(self, text):
        # The text and the lexer.
        self.text = text
        self.lexer = RegexLexer(text, SPEC_TOKENS)
        # State and handlers for that state.
        self.state = None
        selr.handlers = tuple()
        # Info about current token, line, and indent of that line.
        self.curr = None
        self.line = None
        self.indent = None
        # Tokens and handlers for the parser states.
        self.state_configs = {
            'grammar_variant': (
                __,
                Handler(self.section_title, 'section_opt_help'),
                Handler(self.variant, None),
            ),
            'grammar_opt_help': (
                __,
                Handler(self.section_title, 'section_opt_help'),
                Handler(self.opt_help, None),
            ),
            'section_opt_help': (
                __,
                Handler(self.block_quote, None),
                Handler(self.section_title, None),
                Handler(self.opt_help, None),
            ),
        }

    def set_state(self, next_state):
        if self.curr:
            # Changing state while caching a prior token seems bad.
            raise ...
        else:
            tup = self.state_configs[next_state]
            self.state = next_state
            self.lexer.tokens = tup[0]
            self.handlers = tup[1:]

    def parse(self):
        elems = list(self.do_parse())

        # Convert elems to a Grammar.
        # There will be some validation needed here too.
        ...

        # We expect EOF as the final token.
        if not self.curr.isa(EOF):
            self.error()

    def do_parse(self):
        # Consume and yield top-level ParseElem -- namely,
        # section titles, block-quotes, variants, opt-helps.
        elem = True
        while elem:
            for h in self.handlers:
                elem = h.method()
                if elem:
                    yield elem
                    # Every top-level ParseElem must start on a fresh line.
                    self.indent = None
                    self.line = None
                    # Advance parser state, if needed.
                    if h.next_state:
                        self.set_state(h.next_state)
                    # Break from inner loop and enter it again.
                    # We will exit outer loop if all handlers return None.
                    break

    def eat(self, toktypes*, taste = False, skip_indent = True, toktype = None):
        # Get the next token, either from self.curr or the lexer.
        # Typically, intervening indent tokens are skipped.
        while True:
            # Get token.
            if self.curr is None:
                self.curr = self.lexer.get_next_token(toktype = toktype)
            tok = self.curr
            # Lexer should deal with EOF, not parser.
            if tok.isa(EOF):
                raise ...
            # Skip indent or break.
            if tok.isa(INDENT) and skip_indent:
                self.curr = None
            else:
                break

        # Check whether token follows indentation/start-of-line rules.
        if self.indent is None:
            # SpecParser has no indent yet. We expect the first token
            # for a variant/opt-help expression. If OK, remember that
            # token's indent and line.
            if tok.is_first:
                self.indent = tok.indent
                self.line = tok.line
                ok = True
            else:
                ok = False
        else:
            # For subsequent tokens in the expression, we expect tokens
            # from the same line or a continuation line indented farther
            # than the first line of the expression.
            if self.line == tok.line:
                ok = True
            elif self.indent < tok.indent:
                self.line = tok.line
                ok = True
            else:
                ok = False

        # Check token type.
        if ok and any(self.curr.isa(tt) for tt in toktypes):
            if tok and not taste:
                self.swallow()
            return tok
        else:
            return None

    def swallow(self):
        if self.curr is None:
            raise ...
        else:
            self.curr = None

    def error(self):
        fmt = 'Invalid syntax: pos={}'
        msg = fmt.format(self.lexer.pos)
        raise Exception(msg)

    def parse_first(self, methods):
        elem = None
        for m in methods:
            elem = m()
            if elem:
                break
        return None

    def parse_some(self, method):
        elems = []
        while True:
            e = method()
            if e:
                elems.push(e)
            else:
                break
        return elems

    # ========================================
    # Methods specific to the grammar syntax.

    '''

    variant
        expression ...
            element...
                quoted_literal
                partial_usage
                paren_expression
                    ( expression )
                brack_expression
                    [ expression ]
                positional
                    < positional_definition >
                long_option
                    --opt
                    parameter*
                        < parameter_definition >
                short_option
                    -o
                    parameter*
                        < parameter_definition >

    # Details.
    choices
    quantifier
    one_or_more_dots
    quantifier_range

    # helpers
    parenthesized
    option

    '''

    def variant(self):
        # Get variant/partial name, if any.
        defs = (variant-defintion, partial-defintion)
        tok = self.eat(defs, taste = True)
        if tok:
            self.swallow()
            var_name = ...
            is_partial = ...
        else:
            var_name = None
            is_partial = False

        # Collect the ParseElem for the variant.
        # Empty variant means a spec syntax error.
        elems = self.elems()
        if elems:
            return Variant(var_name, is_partial, elems)
        else:
            raise ...

    def opt_help(self):
        elems = self.elems()
        txt = ''
        if self.eat('opt-help-sep'):
            tt = TokType(REST_OF_LINE)
            while True:
                tok = self.eat(toktype = tt, skip_indent = False)
                if tok:
                    txt = txt + ' ' + tok.text.strip()
                if not self.eat('indent', skip_indent = False):
                    break
        return OptHelp(elems, txt.strip())

    def elems(self):
        methods = (
            self.quoted_literal,
            self.partial_usage,
            self.paren_expression,
            self.brack_expression,
            self.positional,
            self.long_option,
            self.short_option,
        )
        elems = []
        while True:
            e = self.parse_first(methods)
            if e:
                q = self.quantifier()
                if q:
                    e.quantifier = q
                elems.append(e)
            else:
                break
        return elems

    def paren_expression(self):
        elems = self.parenthesized(paren-open, 'elems')
        if elems is None:
            return None
        else:
            return Parenthesized(elems)

    def brack_expression(self):
        elems = self.parenthesized(brack-open, 'elems')
        if elems is None:
            return None
        else:
            return Bracketed(elems)

    def quoted_literal(self):
        tok = self.eat(quoted-literal)
        if tok:
            return Literal(...)
        else:
            return None

    def partial_usage(self):
        tok = self.eat(partial-usage)
        if tok:
            return PartialUsage(...)
        else:
            return None

    def long_option(self):
        return self.option(long-option)

    def short_option(self):
        return self.option(short-option)

    def option(self, option_type):
        tok = self.eat(option_type)
        if tok:
            name = ...
            params = self.parse_some(self.parameter)
            return Opt(name, params, ...)
        else:
            return None

    def positional(self):
        return self.parenthesized(angle-open, 'positional_definition')

    def parameter(self):
        return self.parenthesized(angle-open, 'parameter_definition')

    def positional_definition(self):
        # Get the choices. Positionals require a dest.
        choices = self.choices()
        if not choices.dest:
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

    def parameter_definition(self):
        # Parse the choices expression.
        choices = self.parenthesized(angle-open, 'choices', empty_ok = True)

        # Return early on failure or if we are just peeking.
        if choices is None:
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

    def choices(self):
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
        tok = self.eat(name)
        if tok:
            dest = ...
        else:
            dest = None

        # Return if no assigned value/choices.
        tok = self.eat(assign)
        if not tok:
            return Choices(dest, tuple())

        # Get value/choices.
        choices = []
        while True:
            val = self.eat((quoted-literal, name))
            if val:
                choices.append(val)
                if not self.eat(choice-sep):
                    break
            else:
                break

        # Return.
        if choices:
            return Choices(dest, tuple(choices))
        else:
            # Return None here: equal without choices is invalid.
            pass

    def quantifier(self):
        quantifier_methods = (
            self.one_or_more_dots,
            self.quantifier_range,
        )
        q = self.parse_first(quantifier_methods)
        if q:
            greedy = not self.eat(question)
            return Quantifier(q, greedy)
        else:
            return None

    def one_or_more_dots(self):
        tok = self.eat(triple-dot)
        if tok:
            return (1, None)
        else:
            return None

    def quantifier_range(self):
        tok = self.eat(quantifier-range)
        if tok:
            ...
            return (..., ...)
        else:
            return None

    def parenthesized(self, open_tok, method_name, empty_ok = False):
        close_tok = ...
        tok = self.eat(open_tok)
        if tok:
            method = getattr(self, method_name)
            elem = method()
            if not (elem or empty_ok):
                raise ...
            elif self.eat(close_tok):
                return elem
            else:
                raise ...
        else:
            return None

