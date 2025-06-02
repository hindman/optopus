
import sys

from dataclasses import dataclass

from short_con import cons

from .constants import Chars
from .tokens import Token, TokDefs
from .utils import get_caller_name, get

####
# RegexLexer.
####

class RegexLexer(object):

    ####
    # Setup.
    ####

    def __init__(self, text, validator, tokdefs = None, debug = False):
        # Text to be lexed.
        self.text = text
        self.lines = text.split(Chars.newline)

        # Debugging: file handle and indent-level.
        self.debug_fh = debug
        self.debug_indent = 0

        # TokDefs currently of interest. Modal parsers can change
        # them when the parsing mode changes.
        self.tokdefs = tokdefs

        # A validation function. Called in get_next_token() to ask the parser
        # whether the matched Token is a kind of immediate of interest.
        self.validator = validator

        # Current token and final token, that latter to be set
        # with Token(eof)/Token(err) when lexing finishes.
        self.curr = None
        self.end = None

        # Location and token information:
        # - pos: character index
        # - line: line number
        # - col: column number
        # - indent: width of most recently read Token(indent).
        # - is_first: True if next Token is first on line, after any indent.
        self.maxpos = len(self.text) - 1
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent = 0
        self.is_first = True

    ####
    # Properties allowing the SpecParser to change the tokdefs
    # of interest or to reset the lexer position.
    ####

    @property
    def tokdefs(self):
        return self._tokdefs

    @tokdefs.setter
    def tokdefs(self, tokdefs):
        # If TokDefs are changed, clear any cached Token.
        self._tokdefs = tokdefs
        self.curr = None

    @property
    def position(self):
        return cons(
            pos = self.pos,
            line = self.line,
            col = self.col,
            indent = self.indent,
            is_first = self.is_first,
            curr = None,
        )

    @position.setter
    def position(self, pos):
        for a, v in pos:
            setattr(self, a, v)

    ####
    # Getting the next token.
    #
    # - get_next_token(): used by SpecParser during its parsing process.
    #
    # - match_token(): used by RegexLexer to try the tokdefs in order
    #   until it matches a TokDef with a token that should be emitted.
    #
    ####

    def get_next_token(self):
        # Return if we are already done lexing.
        if self.end:
            return self.end

        # Get the next token, either from self.curr or the matcher.
        if self.curr:
            tok = self.curr
            self.curr = None
        else:
            tok = self.match_token()

        # If we got a Token, ask the parser's validation function
        # whether to return it or cache it in self.curr.
        # If returned, we update location information.
        if tok:
            self.debug(lexed = tok.kind)
            if self.validator(tok):
                self.update_location(tok)
                self.curr = None
                self.debug(returned = tok.kind)
                return tok
            else:
                self.curr = tok
                return None

        # If we did not get a token, we have lexed as far as
        # we can. Set the end token and return it.
        done = self.pos > self.maxpos
        td = TokDefs.eof if done else TokDefs.err
        tok = self.create_token(td)
        self.curr = None
        self.end = tok
        self.update_location(tok)
        return tok

    def match_token(self):
        # Starting at self.pos, return the next Token.
        #
        # For non-emitted tokens, we break out of the for-loop, but enter the
        # while-loop again. This allows the lexer to be able to ignore 0+
        # non-emitted tokens on each call of the function.
        #
        tok = True
        while tok:
            tok = None
            for td in self.tokdefs:
                m = td.regex.match(self.text, pos = self.pos)
                if m:
                    tok = self.create_token(td, m)
                    if td.emit:
                        return tok
                    else:
                        self.update_location(tok)
                        break
        return None

    ####
    # Helpers used when getting the next token.
    ####

    def create_token(self, tokdef, m = None):
        # Helper to create Token from a TokDef and a regex Match.
        text = m[0] if m else ''
        newline_indexes = [
            i for i, c in enumerate(text)
            if c == Chars.newline
        ]
        return Token(
            kind = tokdef.kind,
            text = text,
            m = m,
            width = len(text),
            pos = self.pos,
            line = self.line,
            col = self.col,
            nlines = len(newline_indexes) + 1,
            is_first = self.is_first,
            indent = self.indent,
            newlines = newline_indexes,
        )

    def update_location(self, tok):
        # Updates the lexer's position-related info, given that
        # the parser has accepted the Token.

        # Character index, line number.
        self.pos += tok.width
        self.line += tok.nlines - 1

        # Column number.
        if tok.newlines:
            # Text straddles multiple lines. New column number
            # is based on the width of the text on the last line.
            #
            # Examples:
            #
            #     tok.text      | tok.width | tok.newlines | self.col
            #     ---------------------------------------------------
            #     \n            | 1         | [0]          | 1
            #     fubb\n        | 5         | [4]          | 1
            #     fubb\nbar     | 8         | [4]          | 4
            #     fubb\nbar\n   | 9         | [4, 8]       | 1
            #     fubb\nbar\nxy | 11        | [4, 8]       | 3
            #
            self.col = tok.width - tok.newlines[-1]
        else:
            # Easy case: just add the token's width.
            self.col += tok.width

        # Update the parser's indent-related info.
        if tok.isa(TokDefs.newline):
            self.indent = 0
            self.is_first = True
        elif tok.isa(TokDefs.indent):
            self.indent = tok.width
            self.is_first = True
        else:
            self.is_first = False

    ####
    # Getting contextual text surround the current position.
    ####

    def get_context(self):
        return ParseContext(
            line = get(self.lines, self.line - 1),
            col = self.col,
        )


    ####
    # Helpers to print debugging information.
    ####

    def debug(self,
              caller_name = None,
              caller_offset = 0,
              msg_prefix = '',
              RESULT = None,
              **kws):

        # Decided whether and where to emit debug output.
        if self.debug_fh is True:
            fh = sys.stdout
        elif self.debug_fh:
            fh = self.debug_fh
        else:
            return

        # Indentation.
        indent = Chars.space * (self.debug_indent * 2)

        # Name of the method calling debug().
        caller_name = caller_name or get_caller_name(caller_offset + 2)

        # The params-portion of the debug message.
        if RESULT is False:
            # A parsing-function completed without success.
            params = Chars.empty_set
        elif RESULT:
            # A parsing-function suceeded: RESULT holds ParseElem class name.
            params = f'RESULT = {RESULT}'
        elif kws:
            # An informational debug() call.
            params = ', '.join(
                f'{k} = {v!r}'
                for k, v in kws.items()
            )
        else:
            # The same, but no kws, so the caller just wanted
            # the caller_name printed.
            params = ''

        # Print the message.
        msg = f'{msg_prefix}{indent}{caller_name}({params})'
        print(msg, file = fh)

####
# ParseContext.
####

@dataclass
class ParseContext():
    line: str
    col: int

    @property
    def for_error(self):
        if self.line:
            heading = '# Parse context.'
            indent = Chars.space * (self.col - 1)
            caret_line = indent + Chars.caret
            return f'\n\n{heading}\n{self.line}\n{caret_line}'
        else:
            return None

