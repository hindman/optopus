'''

TODO:

    - Continuation lines:

        - Lexer sets Token attributes about indentation.

        - Let eat() enforce indentation rules using that info:

            - SpecParser will have self.indent = N | None

            - If None: enforce is-first requirement:

                - Swallow if:

                    tok.is_first or
                    self.is_first_variant

                - Represents start variant/opt-help.
                - Set self.indent = tok.ident
                - Set self.is_first_variant = False on second variant.

            - If set: enforce indentation rules:

                - Swallow token only if:

                    self.line == tok.line or
                    self.indent < tok.indent

    - Create a Handler data-class.

    - Create a Token data-class.

    - SpecParser.parse(): determine initial state:

        peek for section-name
        yes: state => grammar_opt_help
        no:  state = grammar_variant

    - SpecParser.variant(): variants no longer require a name.

    - SpecParser.element(): not helpful.

        - Move logic to expression().

    - Adjust parsing methods

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
    bq        | (?<!\\)`
    bq3       | (?<!\\)```

    Tokens            | Pattern                  | Note
    -------------------------------------------------------------------------------
    quoted-block      | bq3 [\s\S]*? bq3         | .
    quoted-literal    | bq [\s\S]*? bq           | .
    newline           | \n                       | Ignore
    indent            | ^ hws*                   | Ignore; track; MULTILINE
    whitespace        | hws*                     | Ignore
    quantifier-range  | \{ hws* quant hws* \}    | .
    paren-open        | \(                       | .
    paren-close       | \)                       | .
    brack-open        | \[                       | .
    brack-close       | \]                       | .
    angle-open        | \<                       | .
    angle-close       | \>                       | .
    choice-sep        | BAR                      | .
    triple-dot        | \.\.\.                   | .
    question          | \?                       | .
    long-option       | -- name                  | .
    short-option      | - \w                     | .
    section-name      | prog-name? hws* :: eol   | Grammar
    section-title     | .* :: eol                | Section
    partial-defintion | name ! hws* :            | Grammar
    variant-defintion | name hws* :              | Grammar
    partial-usage     | name !                   | Grammar
    name-assign       | name hws* =              | .
    sym-dest          | name hws* [!.] hws* name | .
    dest              | [!.] hws* name           | .
    name              | name                     | .
    assign            | =                        | .
    opt-help-text     | : .*                     | .

'''

class RegexLexer(object):

    def __init__(self, text, token_types):
        self.text = text
        self.token_types = token_types
        self.max_pos = len(self.text) - 1
        # Location and other info given to tokens.
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.is_first = True

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
                    if tok.name == 'indent':
                        self.indent = tok.width
                    elif tok.name == 'newline':
                        self.indent = 0
                        self.is_first = True
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

class SpecParser:

    # General parsing methods (formerly in the mixin).

    def __init__(self, text):
        self.text = text
        self.curr = None
        self.state = None
        self.handlers = None
        self.lexer = RegexLexer(text, SPEC_TOKENS)

        self.states = dict(
            grammar_opt_help = dict(
                tokens = __,
                handlers = [
                    (self.section_title, 'section_opt_help'),
                    (self.opt_help, None),
                ],
            ),
            grammar_variant = dict(
                tokens = __,
                handlers = [
                    (self.section_title, 'section_opt_help'),
                    (self.variant, None),
                ],
            ),
            section_opt_help = dict(
                tokens = __,
                handlers = [
                    (self.block_quote, 'section_other'),
                    (self.section_title, None),
                    (self.opt_help, None),
                ],
            ),
            section_other = dict(
                tokens = __,
                handlers = [
                    (self.block_quote, 'section_opt_help'),
                    (self.other_line, None),
                ],
            ),
        )

    def parse(self):

        # Consume and yield as many ParseElem as we can.
        elem = True

        while elem:
            for h in self.handlers:
                elem = h.method()
                if elem:
                    yield elem
                    if h.next_state:
                        self.state = h.next_state
                    break
        # We expect EOF as the final token.
        if not self.curr.isa(EOF):
            self.error()

    def eat(self, toktypes*, taste = False):
        # Pull from lexer if we lack a current token.
        if self.curr is None:
            self.curr = self.lexer.get_next_token()
            if self.curr.isa(EOF):
                # Because the lexer should deal with EOF, not parser.
                raise ...
        # Check for desired token type(s).
        tok = None
        for tt in toktypes:
            if self.curr.isa(tt):
                tok = self.curr
                if not taste:
                    self.swallow()
                break
        return tok

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

        # Setup.
        defs = (variant-defintion, partial-defintion)

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

    def expression(self):
        elems = self.parse_some(self.element)
        return Expression(elems)

    def element(self):
        element_methods = (
            self.quoted_literal,
            self.partial_usage,
            self.paren_expression,
            self.brack_expression,
            self.positional,
            self.long_option,
            self.short_option,
        )
        e = self.parse_first(element_methods)
        if e:
            q = self.quantifier()
            if q:
                e.quantifier = q
        return e

    def paren_expression(self):
        return self.parenthesized(paren-open, 'expression')

    def brack_expression(self):
        return self.parenthesized(brack-open, 'expression')

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

