import re

'''

Spec tokens:

    Spippet   | Pattern
    -----------------------------------------------------
    nm        | \w+
    name      | nm ([_-] nm)*
    prog-name | name ( \. nm )?
    hws       | [ \t]
    eol       | hws* (?=\n)
    num       | \d+
    q         | hws* , hws*
    quant     | num | q | q num | num q | num q num
    bq        | (?<!\\)`
    bq3       | (?<!\\)```

    Tokens            | Pattern                  | Modes | Note
    ---------------------------------------------------------------------------------
    quoted-block      | bq3 [\s\S]*? bq3         | s     | .
    quoted-literal    | bq [\s\S]*? bq           | all   | .
    newline           | \n                       | all   | Ignore
    blank-line        | ^ hws* eol               | all   | Ignore; MULTILINE
    indent            | ^ hws* (?=\S)            | all   | MULTILINE
    whitespace        | hws*                     | all   | Ignore
    quantifier-range  | \{ hws* quant hws* \}    | all   | .
    paren-open        | \(                       | all   | .
    paren-close       | \)                       | all   | .
    brack-open        | \[                       | all   | .
    brack-close       | \]                       | all   | .
    angle-open        | \<                       | all   | .
    angle-close       | \>                       | all   | .
    choice-sep        | BAR                      | all   | .
    triple-dot        | \.\.\.                   | all   | .
    question          | \?                       | all   | .
    long-option       | -- name                  | all   | .
    short-option      | - \w                     | all   | .
    section-name      | prog-name? hws* :: eol   | v     | .
    section-title     | .* :: eol                | all   | .
    partial-defintion | name ! hws* :            | v     | .
    variant-defintion | name hws* :              | v     | .
    partial-usage     | name !                   | v     | .
    name-assign       | name hws* =              | all   | .
    sym-dest          | name hws* [!.] hws* name | all   | .
    dest              | [!.] hws* name           | all   | .
    name              | name                     | all   | .
    assign            | =                        | all   | .
    opt-help-sep      | :                        | o s   | .
    rest-of-line      | .*                       |       | .

'''

pmodes = constants('ParserModes', 'variant opt_help section all')

@attr.s
class TokType:
    name = attr.ib()

    # Attribute | Note
    # --------------------------------------------------------------------------------
    # name      | Name of token.
    # regex     | Regex to match the token.
    # emit      | Whether to emit back to parser [default: True].
    # flags     | re.compile() flags
    # modes     | .
    # --------------------------------------------------------------------------------

from short_con import constants, cons

'''

'''

snips = cons('Snippets',
    'name' = r'\w+(?:[_-]\w+)*',
    'num'  = r'\d+',
    'hws'  = r'[ \t]',
    'q'    = r'[ \t]*,[ \t]*',
)

snips = cons('Snippets',
    'name'      = r'\w+(?:[_-]\w+)*',
    'num'       = r'\d+',
    'hws'       = r'[ \t]',
    'q'         = r'[ \t]*,[ \t]*',
    'prog_name' = cons.name + r'(?:\.\w+)?',
    'eol'       = cons.hws + r'*(?=\n)',
    'quant'     = r'num | q | q num | num q | num q num',
    'bq'        = r'(?<!\\)`',
    'bq3'       = r'(?<!\\)```',
)

snips = cons('Snippets',
    'name'      = snips.name,
    'num'       = snips.num,
    'hws'       = snips.hws,
    'q'         = snips.q,
    'prog-name' = snips.name + r'(?:\.\w+)?',
    'eol'       = snips.hws + r'*(?=\n)',
    'quant'     = r'num | q | q num | num q | num q num',
    'bq'        = r'(?<!\\)`',
    'bq3'       = r'(?<!\\)```',
)

token_types = cons('TokTypes',
    TokType('quoted_block'
    # quoted-block      | bq3 [\s\S]*? bq3         | s     | .
    # quoted-literal    | bq [\s\S]*? bq           | all   | .
)


class regexlexer:

    def __init__(self, text, token_types = none):
        self.text = text
        self.token_types = token_types
        self.max_pos = len(self.text) - 1
        # location and other info given to tokens.
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.is_first = true

    def get_next_token(self, toktype = none):
        # starting at self.pos, try to emit the next token.
        # if we find a valid token, there are two possibilities:
        #
        # - a token that we should emit: just return it.
        #
        # - a token that we should suppress: break out of the for-loop,
        #   but try the while-loop again. this will allow the lexer
        #   to be able to ignore any number of suppressed tokens.
        #
        # the optional toktype argument allows the parser to request a specific
        # toktype directly, bypassing the normal ordering in self.token_types.
        # this is used for opt-help text (and its continuation-lines).
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

