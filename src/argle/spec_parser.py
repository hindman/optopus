
r'''

TODO:

    - Quoted strings: refactor to use a parse mode:
        - Support no-wrap: ```!
        - Support comment: ```#
        - Support backslashed literals: ```   `   !   #   \

        - Details:

            - Parsing modes: quote1 and quote3.

            - Logic:
                - quote3 mode starts if we get: ```! or ```# or ```
                - quote1 mode starts if we get: `
                - collect quoted_char() until we get the terminal TokDef
                  appropriate for the mode.

            - TokDefs:

                Kind              | Modes  | Rgx      | Action
                -------------------------------------------------------------
                literal_backslash | both   | \\\\     | emit \
                literal_backquote | both   | \\`      | emit `
                quoted_char3      | quote3 | [^`]     | emit CHAR
                quoted_char1      | quote1 | [^`\t\n] | emit CHAR
                -------------------------------------------------------------
                backquote3        | quote3 | ```      | halt quote3 mode
                backquote1        | quote1 | `        | halt quote1 mode

    - build_grammar()

        - PartialUsage => replace with actual elems
        - Group => split elems on ChoiceSep

    - error(): includes expected-elements:
        - Probably framed in terms of parsing-functions.

----
Spec-parsing overview
----

TokDefs and Tokens:

    - Tokens are the atomic entitites of the parsing process. Examples:

        long_option  | --foo
        short_option | -x
        newline      | \n
        paren_open   | (
        brack_close  | ]

    - TokDef:
        - Has a kind attribute and a regex.
        - Used by RegexLexer to hunt for tokens of interest.

    - Token:
        - Emitted by RegexLexer when it finds a match.
        - Has a kind attribute paralleling the TokDef.
        - Contains the matched text, plus information about the position of
          that match within the larger corpus (line, col, etc).

SpecParser and RegexLexer: overview:

    - The RegexLexer:
        - Works with atomic units: Tokens.
        - Its primary function is get_next_token().

    - The SpecParser:
        - Works with more meaningful grammatical units.
        - Those units are expressed in various parsing functions.
        - Examples:
            - variant()
            - opt_spec()
            - section_title()
            - quoted_block()

        - Parsing functions are hierarchical:
            - Some match large things: eg variants or opt-specs.
            - Others match small things within those larger grammatical
              units: eg, long options, positional, parameters, etc.

        - The spec-syntax requires contextual parsing:
            - The SpecParser uses a mode attribute to manage context.
            - When the mode changes, the parser tells the lexer which TokDefs
              to search for.

            - The initial implementation of this code had 4 modes, but after
              the spec-syntax was simplified, we now only have two modes:
                - grammar:
                    - The default.
                    - Regular spec-syntax grammar.
                - help-text:
                    - Collects opt-spec help text, plus continuation lines.
                    - Get triggered after we hit the opt-spec separator (:).
                    - The mode uses very few TokDefs: if a continutation line
                      satisfies the line/indent requirements, the entire
                      rest_of_line is slurped up as help text.
                    - After an opt-spec help text is parsed, we toggle back to
                      the default parsing mode.

Spec-parsing: the process:

    - Intialization:
        - SpecParser sets itself up.
        - It creates self.lexer holding a RegexLexer.
        - The RegexLexer is given two things:
            - The text to be processed.
            - A validator function: Lexer.taste() [details below].

    - SpecParser.parse() is invoked:

        - That invocation occurs in two context:
            - Unit tests for SpecParser.
            - By a user: opts = Parser(SPEC).parse()

        - The parse() function:
            - Works with top-level parsing functions.
            - Those functions then rely on lower level functions.
            - When no more elements can be parsed, the parse() function:
                - Raises if we failed to consume the entire spec.
                - Assembles the parsed elements into a Grammar.
                - The Grammar becomes the basis for a Parser to parse
                  command-line arguments, generate help text, etc.

    - When a parsing function is called:
        - It calls eat(), passing in 1+ TokDefs.
        - Those TokDefs are a subset of the broader list of TokDefs that the
          RegexLexer was given when the parsing mode was set.
        - The eat() method assigns those TokDefs to self.menu.
        - Then it calls RegexLexer.get_next_token().

    - When get_next_token() is called:

        - The lexer uses its match_token() method to try to match each TokDef
          in self.tokdefs.
            - It tries them in order until it gets a match.
            - If the matched TokDef has emit=False:
                - The lexer updates its position information.
                - Then it goes through the self.tokdefs again, from the start.
            - Otherwise, it creates a Token and returns it.

        - When get_next_token() receives such a Token:
            - It calls self.validator() with that Token.
            - In effect, it says to the SpecParser:
                - I found a Token relevant for the current parsing mode.
                - But is it the right kind, given the current context?

        - The validator function is SpecParser.taste():
            - It first checks whether the matched Token is on self.menu.
            - Then it checks other contextual details related to line
              indentation and start-of-line status.
            - It returns True is all criteria are met.

        - Then get_next_token() reacts to that bool:
            - If True:
                - It updates its own location information (line, col, etc).
                - Returns the Token.
            - If False:
                - It just stores the Token in self.curr.
                - And it returns None.
                - Storing the Token is self.curr is just an optimization:
                    - The next call to get_next_token() will immediately use
                      self.curr rather than checking the self.tokdefs.

    - The parsing function keeps going:
        - A parsing function might need to uses self.eat() multiple times to
          assemble the grammatical entity it is trying to match.
        - It those eat() calls lead down a successful path, it eventually
          returns the relevant ParseElem.
        - Otherwise it returns None.

Why not ask specifically for what is on SpecParser.menu?

    - The SpecParser gives RegexLexer a general list of TokDefs whenever the
      parsing mode is set.
    - But taste() approves only tokens on the menu.
    - Why bother with the general list in RegexLexer.tokdefs?

        - It allows lexer to handle non-emitted tokens.
        - Relieves parser of the need to pass them in every time, properly
          ordered.

        - But that would be easy to handle inside the parser.
            - Keep the full, ordered list in the parser.
            - Given tds passed to eat(), build an ordered sub-list
              to pass to get_next_token().

        - Provides a caching mechanism:
            - Most parsing modes use most of the tokens.
            - So the cached token is often used.
            - Performance gain probably irrelevant for this project.
            - But caching does seem correct in a textbook way.

----
VarInput forms
----

A VarInput for a positional or parameter can take various forms:

    < valid-name >              #1
    < valid-name = choices >    #2
    < choices >                 #3
    < >                         #4

Parsing complexity comes from two issues:
    - Positional require a name; parameters do not.
    - A valid-name and a choice look the same, so the parser does not know how
      to interpret the first valid-name until it parses farther.

Parsing components/flags:

    - Notation used in the table:

        noc  | True if the first valid-name or choice is present.
        =    | True if an equal sign is present.
        oc   | True if any other choices are present.
        form | The var-input form (as listed above).

    - Table listing all possible situations:

        noc | = | oc | form | Example and error
        --------------------------------------------------------
        Y   | Y | Y  | #2   | <foo=x|y>
        Y   | Y | .  | .    | <foo=>        Assign w/o choice(s)
        Y   | . | Y  | #3   | <foo|x|y>
        Y   | . | .  | #1   | <foo>
        .   | Y | Y  | .    | <=x|y>        Assign w/o name
        .   | Y | .  | .    | <=>           Ditto
        .   | . | Y  | #3   | <`hi!`|x|y>
        .   | . | .  | #4   | <>


----
Why parameter_group() needs position-rest and error-catching logic
----

Because options can have groups as parameters, grammatical overlap occurs:

    - Example A:

        --env --user [--indent]
                      ^

        - Parses Option(--env).
        - Starts Option(--user).
        - Starts parameter_group().
        - Halts after opening bracket: options cannot be in parameter-groups.

    - Two possible responses here:

        - Strict policy:
            - Options bind greedily to parameters and parameter-groups.
            - If the parsing halts, so be.
            - Let user add the necessary groups to disambiguate.

        - More flexible parsing:
            - Catch the halt error.
            - Reset position.
            - Interpret the option as finished.
            - Try parsing the non-parameter-group as a regular group.

    - Why strict policy is a step too far:

        - Few users will ever need to know about parameter-groups.
        - But the strict policy approach would force them to write common
          scenarios in awkward ways.

        - Example A would have to be rewritten in one of these ways:

            (--env) (--user) [--indent]    # Disambiguate via groups.
            [--indent] --env --user        # Clever reordering.
            --env --user ; [--indent]      # New syntax: semicolon as separator.

        - People doing regular things (a sequence of options) would need to
          reason about a subtle and fairly exotic feature (parameter-groups).

    - The halt can occur at any depth in the attempted parameter-group parse:

        --user [<x> --HERE]
        --user <name> [<x> --HERE]
        --env [<x> [<y> [<z> --HERE]]]

    - So the policy is:
        - Greedy parameter binding, as usual.
        - But failed parameter-group parses will be retried as regular groups.

'''

####
# Imports.
####

from dataclasses import dataclass, field
from functools import wraps

from short_con import cons, constants

from .constants import Chars, Pmodes
from .errors import SpecParseError, ErrKinds, ErrMsgs
from .regex_lexer import RegexLexer
from .tokens import Token, TokDefs
from .utils import get, distilled

####
# Data classes: ParseElems.
#
# These are intermediate objects used during spec-parsing.
# They are not user-facing and they do not end up as elements
# within the ultimate Grammar returned by SpecParser.parser().
####

@dataclass
class ParseElem:
    # A base class, mostly as a device for terminology.
    #
    # Also a home for some utilities to represent ParseElem
    # as pretty-printable text.
    #

    # ParseElem attributes that should be expanded hierarchically
    # by pp_gen(), rather than being shown simply via repr().
    PP_CHILDREN = ('elems', 'params', 'opt')

    @property
    def pp(self):
        # Return the ParseElem as pretty-printable text.
        return '\n'.join(self.pp_gen(0))

    def pp_gen(self, level = 0):
        # Recursive helper used by pp().
        # Yields lines for the pretty-printable text.

        # Setup.
        cls_name = self.__class__.__name__
        indent = ' ' * 4
        indent1 = indent * level
        indent2 = indent * (level + 1)

        # Start with the class of the current element.
        yield f'{indent1}{cls_name}('

        # Then basic attributes.
        for attr, v in self.__dict__.items():
            if attr not in self.PP_CHILDREN:
                v = f'{v.brief}' if isinstance(v, Token) else f'{v!r}'
                yield f'{indent2}{attr} = {v}'

        # Then recurse to child elements.
        for attr in self.PP_CHILDREN:
            # Get the element, putting it inside a list if needed.
            children = getattr(self, attr, [])
            if not isinstance(children, list):
                children = [children]

            # Process each element.
            for child in children:
                yield from child.pp_gen(level + 1)

@dataclass
class SpecAST(ParseElem):
    # The top-level container for a parsed spec.
    # It is an AST-style container of entire spec.
    # Used to build the ultimate Grammar.
    elems: list[ParseElem]

@dataclass
class VariantElems(ParseElem):
    # A top-level container for elements parsed when we are looking for stuff
    # (1) inside a variant or (b) stuff inside a () or [] group.
    elems: list[ParseElem]

@dataclass
class SectionElems(ParseElem):
    # A top-level container for elements parsed after we are no longer
    # looking for variants.
    elems: list[ParseElem]

@dataclass
class Scope(ParseElem):
    # A scope attached to either a SectionTitle or OptSpec.
    query_path: str

@dataclass
class Quantifier(ParseElem):
    # A quantifier attached to various ParseElem.
    m: int
    n: int
    greedy: bool = True

@dataclass
class Choice(ParseElem):
    # A choice attached to a VarInput (positional or parameter).
    text: str

@dataclass
class Variant(ParseElem):
    name: str
    is_partial: bool
    elems: list

@dataclass
class PartialUsage(ParseElem):
    # When a partial-variant is used inside another variant.
    name: str

@dataclass
class Group(ParseElem):
    # A group: () or [].
    # If the latter, required=False.
    name: str
    elems: list
    quantifier: Quantifier = None
    required: bool = True

@dataclass
class ChoiceSep(ParseElem):
    # Used to represent the choice separator inside a Group.
    pass

@dataclass
class VarInput(ParseElem):
    # An intermediate object used when parsing Positional or Parameter.
    name: str
    elems: list[Choice]

@dataclass
class Positional(ParseElem):
    name: str
    elems: list[Choice]
    quantifier: Quantifier = None

@dataclass
class Parameter(ParseElem):
    name: str
    elems: list[Choice]
    quantifier: Quantifier = None

@dataclass
class BareOption(ParseElem):
    # An intermediate object used when parsing (a) an option,
    # or (b) aliases in an opt-spec.
    name: str

@dataclass
class Option(ParseElem):
    name: str
    params: list[Parameter]
    quantifier: Quantifier = None
    aliases: list[BareOption] = field(default_factory = list)

@dataclass
class OptHelpText(ParseElem):
    # An intermediate object used to parse help-text for an OptSpec.
    text: str

@dataclass
class RestOfLine(ParseElem):
    # An intermediate object used to parse help-text for an OptSpec.
    text: str

@dataclass
class OptSpec(ParseElem):
    scope: Scope
    opt: ParseElem
    text: str
    token: Token

@dataclass
class SectionTitle(ParseElem):
    scope: Scope
    title: str
    token: Token

@dataclass
class Heading(ParseElem):
    title: str
    token: Token

@dataclass
class BlockQuote(ParseElem):
    text: str
    token: Token

@dataclass
class QuotedLiteral(ParseElem):
    # Used (a) to represent a literal in a command-line grammar, or (b)
    # as an intermediate object when parsing choices in a var-input.
    text: str

####
# Constants used when parsing bracketed expressions: () [] <>.
#
# Such parsing occurs within the get_bracketed() method
# and its helper methods.
####

# Kinds of bracketed expressions.
# Callers of get_bracketed() pass in one of these values.
GBKinds = cons(
    # Groups: () or []
    'group',
    'parameter_group',
    'opt_spec_group',
    # Var-inputs: <>
    'positional',
    'parameter',
)

# Sets of opening-TokDefs to use when looking for such expressions.
OpeningTDs = cons(
    group = [
        TokDefs.paren_open,
        TokDefs.paren_open_named,
        TokDefs.brack_open,
        TokDefs.brack_open_named,
    ],
    var_input = [
        TokDefs.angle_open,
    ],
)

# A map connecting the two: bracketed-expression-kind => opening-TokDefs
GBTDs = constants({
    GBKinds.group:           OpeningTDs.group,
    GBKinds.parameter_group: OpeningTDs.group,
    GBKinds.opt_spec_group:  OpeningTDs.group,
    GBKinds.positional:      OpeningTDs.var_input,
    GBKinds.parameter:       OpeningTDs.var_input,
})

# Bracket pairs: opening-TokDef-kind => closing-TokDef.
BPairs = constants({
    TokDefs.paren_open.kind:       TokDefs.paren_close,
    TokDefs.paren_open_named.kind: TokDefs.paren_close,
    TokDefs.brack_open.kind:       TokDefs.brack_close,
    TokDefs.brack_open_named.kind: TokDefs.brack_close,
    TokDefs.angle_open.kind:       TokDefs.angle_close,
})

####
# SpecParser.
####

class SpecParser:

    def __init__(self, text, debug = False):
        # The spec text.
        self.text = text

        # The lexer.
        self.debug = debug
        self.lexer = RegexLexer(text, self.taste, debug = self.debug)

        # Set the initial mode, which triggers the setter
        # to tell the RegexLexer which TokDefs to use.
        self.mode = Pmodes.grammar

        # TokDefs the parser currently trying to eat: these are a subset of
        # those given to the RegexLexer whenever the parsing mode changes.
        self.menu = None

        # First Token of top-level ParseElem currently under construction.
        self.first_tok = None

        # Tokens the parser has eaten.
        self.eaten = []

        # Current stack of parsing-function names.
        # Used for error-reporting and debugging.
        self.parse_stack = []

    @property
    def position(self):
        return cons(
            lexer_position = self.lexer.position,
            mode = self.mode,
            first_tok = self.first_tok,
            next_token_index = self.next_token_index,
        )

    @position.setter
    def position(self, pos):
        self.lexer.position = pos.lexer_position
        self.mode = pos.mode
        self.first_tok = pos.first_tok
        self.reset_eaten(pos.next_token_index)

    @property
    def next_token_index(self):
        return len(self.eaten)

    def reset_eaten(self, next_token_index):
        self.eaten = self.eaten[0 : next_token_index]

    ####
    # Parse-tracking decorator.
    #
    # Manages the indentation levels needed for debugging output
    # as we traverse the hierarchy of parsing-function calls.
    #
    # Also TODO ...
    ####

    def track_parse(old_method):
        # Setup based on the name of the method being decorated.
        NAME = old_method.__name__
        MSG_PREFIX = '\n' if NAME == 'parse' else ''

        @wraps(old_method)
        def parsing_func(self, *xs, **kws):
            # Call debug() to emit the method name.
            lex = self.lexer
            lex.debug(caller_name = NAME, msg_prefix = MSG_PREFIX)

            # Within a higher indent level:
            # - Call the method.
            # - Call debug() to summarize the result.
            lex.debug_indent += 1
            self.parse_stack.append(f'{NAME}()')
            elem = old_method(self, *xs, **kws)
            self.parse_stack.pop()
            result = type(elem).__name__ if elem else False
            lex.debug(caller_name = NAME, RESULT = result)

            # Return to previous indent level and return.
            lex.debug_indent -= 1
            return elem

        return parsing_func

    ####
    # Setting the parser mode.
    ####

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        # When the mode changes, we tell RegexLexer
        # which tokens it should be looking for.
        self._mode = mode
        self.lexer.tokdefs = [
            td
            for td in TokDefs.values()
            if mode in td.modes
        ]

    ####
    # Parse a spec.
    #
    # This is the method used by Parser to convert the spec
    # it is given into a Grammar that it will ultimately
    # use to parse arguments and generate help text.
    ####

    @track_parse
    def parse(self):

        # Collect variants.
        elems = self.parse_some(self.variant)

        # Collect all other elements.
        se = self.collect_section_elems()
        if se:
            elems.extend(se.elems)

        # Raise if we did not parse the full text.
        tok = self.lexer.end
        if not (tok and tok.isa(TokDefs.eof)):
            self.error(ErrKinds.incomplete_spec_parse)

        # Convert the elements to a Grammar.
        sa = SpecAST(elems)
        g = self.build_grammar(sa)
        return g

    ####
    # Parsing functions:
    #
    # - Top-level elements.
    # - Or helpers that collect them.
    ####

    @track_parse
    def variant(self):
        # Setup.
        # - Variants must begin on a fresh line.
        # - Get starting position (because we might need to reset).
        lex = self.lexer
        self.require_is_first_token()
        orig_pos = self.position

        # Get variant/partial name, if any.
        name = None
        is_partial = False
        tok = self.eat(TokDefs.variant_def)
        if tok:
            name = tok.m[1]
            if name.endswith(Chars.exclamation):
                name = name[0:-1]
                is_partial = True

        # Collect the ParseElem for the variant.
        ve = self.variant_elems()

        # Return, raise, or reset position.
        if ve:
            # If we got elems but halted on an opt-spec separator, return empty
            # after resetting the lexer position. Otherwise, return a Variant.
            #
            # We do the position-reset so we can try to re-parse the material
            # as an opt-spec rather than as a variant.
            #
            # This is a known complexity: a bare-bones opt-spec (ie, with no
            # help-text) is also a syntactially valid variant.
            if lex.curr and lex.curr.isa(TokDefs.opt_spec_sep):
                self.position = orig_pos
                return None
            else:
                return Variant(
                    name = name,
                    is_partial = is_partial,
                    elems = ve.elems,
                )
        else:
            # If we got no elems, the situation is simple.
            if name:
                self.error(ErrKinds.empty_variant)
            else:
                return None

    @track_parse
    def collect_section_elems(self):
        # A helper used to collect top-level elements.
        # Like variants, these must also start on their own line.
        elems = []
        while True:
            self.require_is_first_token()
            e = (
                self.any_section_title() or
                self.section_content_elem()
            )
            if e:
                elems.append(e)
            else:
                break
        if elems:
            return SectionElems(elems = elems)
        else:
            return None

    @track_parse
    def any_section_title(self):
        # A section title: scoped or not.
        tok = self.eat(TokDefs.scoped_section_title, TokDefs.section_title)
        if tok:
            if tok.isa(TokDefs.scoped_section_title):
                scope = Scope(tok.m[1])
                title = tok.m[2]
            else:
                scope = None
                title = tok.m[1]
            return SectionTitle(
                title = title,
                scope = scope,
                token = tok,
            )
        else:
            return None

    @track_parse
    def section_content_elem(self):
        # A helper used to collect top-level elements.
        return (
            self.heading() or
            self.block_quote() or
            self.opt_spec()
        )

    @track_parse
    def heading(self):
        tok = self.eat(TokDefs.heading)
        if tok:
            return Heading(
                title = tok.m[1].strip(),
                token = tok,
            )
        else:
            return None

    @track_parse
    def block_quote(self):
        tok = self.eat(TokDefs.quoted_block)
        if tok:
            return BlockQuote(
                text = tok.m[1],
                token = tok,
            )
        else:
            return None

    @track_parse
    def opt_spec(self):
        # If we do get an opt-spec, we will need access to its first Token.
        first_tok_index = self.next_token_index

        # Get the Scope, if any.
        scope = self.opt_spec_scope()

        # Get the Opt definition.
        e = self.opt_spec_def()
        if not e:
            return None

        # Get the OptHelpText, if any.
        t = self.opt_help_text()

        # Boom.
        return OptSpec(
            scope = scope,
            opt = e,
            text = t.text if t else None,
            token = self.eaten[first_tok_index],
        )

    ####
    # Parsing functions:
    #
    # - Mid-level elements that can appear in a Variant or Group.
    ####

    @track_parse
    def variant_elems(self):
        # A helper to collect elements inside a Variant or a Group.
        elems = []
        while True:
            e = (
                self.quoted_literal() or
                self.choice_sep() or
                self.partial_usage() or
                self.any_group() or
                self.positional() or
                self.option()
            )
            if e:
                elems.append(e)
            else:
                break
        if elems:
            return VariantElems(elems = elems)
        else:
            return None

    @track_parse
    def quoted_literal(self):
        tok = self.eat(TokDefs.quoted_literal)
        if tok:
            return QuotedLiteral(text = tok.m[1])
        else:
            return None

    @track_parse
    def choice_sep(self):
        tok = self.eat(TokDefs.choice_sep)
        if tok:
            return ChoiceSep()
        else:
            return None

    @track_parse
    def partial_usage(self):
        tok = self.eat(TokDefs.partial_usage)
        if tok:
            return PartialUsage(name = tok.m[1])
        else:
            return None

    @track_parse
    def any_group(self):
        return self.with_quantifer(
            self.get_bracketed(GBKinds.group)
        )

    @track_parse
    def positional(self):
        return self.with_quantifer(
            self.with_quantifer(
                self.get_bracketed(GBKinds.positional)
            )
        )

    @track_parse
    def option(self):
        b = self.bare_option()
        if b:
            params = self.parse_some(self.any_parameter, top_level = True)
            e = Option(b.name, params, None)
            if params:
                return e
            else:
                return self.with_quantifer(e)
        else:
            return None

    ####
    # Parsing functions:
    #
    # Elements that can appear in an OptSpec.
    ####

    @track_parse
    def opt_spec_scope(self):
        # An opt-spec scope declaration.
        tok = self.eat(TokDefs.opt_spec_scope, TokDefs.opt_spec_scope_empty)
        if tok:
            query_path = get(tok.m, 1)
            return Scope(query_path)
        else:
            return None

    @track_parse
    def opt_spec_def(self):
        # An opt-spec definition (ie, the stuff between
        # the scope and the help-text).
        return (
            self.opt_spec_group() or
            self.opt_spec_elem()
        )

    @track_parse
    def opt_spec_group(self):
        # The enclosing-group around an opt-spec definition.
        return self.with_quantifer(
            self.get_bracketed(GBKinds.opt_spec_group)
        )

    @track_parse
    def opt_spec_elem(self):
        return (
            self.positional() or
            self.aliases_and_option()
        )

    @track_parse
    def aliases_and_option(self):
        # One or more aliases and then the option itself.
        aliases = self.parse_some(self.bare_option)
        if aliases:
            b = aliases.pop()
            params = self.parse_some(self.any_parameter, top_level = True)
            e = Option(
                name = b.name,
                params = params,
                aliases = aliases,
            )
            if params:
                return e
            else:
                return self.with_quantifer(e)
        else:
            return None

    @track_parse
    def bare_option(self):
        # Parses just the option, eg --foo.
        # Used when parsing an option in a variant or the
        # aliases in an opt-spec.
        tok = self.eat(TokDefs.long_option, TokDefs.short_option)
        if tok:
            return BareOption(name = tok.m[1])
        else:
            return None

    @track_parse
    def opt_help_text(self):
        # Try to get the opt-spec help text and any continuation lines.
        if self.eat(TokDefs.opt_spec_sep):
            # Change parsing mode while collected opt-spec help text.
            self.mode = Pmodes.help_text
            elems = self.parse_some(self.rest_of_line)
            self.mode = Pmodes.grammar

            # If we got any, assemble and return an OptHelpText.
            if elems:
                text = Chars.space.join(e.text for e in elems)
                return OptHelpText(text = text)

        return None

    @track_parse
    def rest_of_line(self):
        tok = self.eat(TokDefs.rest_of_line)
        if tok:
            text = tok.text.strip()
            if text:
                return RestOfLine(text = text)
        return None

    ####
    # Parsing functions:
    #
    # Parameters.
    ####

    @track_parse
    def any_parameter(self, top_level = True):
        return (
            self.parameter() or
            self.parameter_group(top_level = top_level)
        )

    @track_parse
    def parameter(self):
        return self.with_quantifer(
            self.get_bracketed(GBKinds.parameter)
        )

    @track_parse
    def parameter_group(self, top_level = True):
        # True: parameter as a direct child of the option.
        # False: parameter nested inside a parameter-group.

        # Store the current position-info, in case we need
        # to reset it. Details below.
        orig_pos = self.position if top_level else None

        try:
            # Here we either (a) parse a parameter-group or (b) never
            # even get started (no opening bracket) and get None.
            e = self.get_bracketed(GBKinds.parameter_group)
            return self.with_quantifer(e)
        except SpecParseError as err:
            # Here we started parsing a parameter-group, but then halted midway
            # with an error.
            #
            # If this parameter_group() call is for a top-level element (direct
            # child of an Option, not a nested parameter-group) and if the
            # error is the right kind, we need to reset-position and return
            # None, rather than letting the error be raised.
            #
            # That will tell the currently-pending Option that no more
            # parameters are forthcoming. The Option will wrap up and the group
            # that raised the error here will be re-parsed, as a regular group.
            eks = (
                ErrKinds.empty_group,
                ErrKinds.unclosed_bracketed_expression,
            )
            if top_level and err.isa(*eks):
                self.position = orig_pos
                return None
            else:
                raise

    ####
    # Quantifiers.
    ####

    @track_parse
    def with_quantifer(self, e):
        # A helper to attached a quantifier to a ParseElem.
        if e:
            q = self.quantifier()
            if q:
                e.quantifier = q
        return e

    @track_parse
    def quantifier(self):
        # Parses quantifiers: ... or {m,n} or ?
        q = self.triple_dot() or self.quant_range()
        if q:
            q.greedy = not self.eat(TokDefs.question)
            return q
        elif self.eat(TokDefs.question):
            return Quantifier(m = 0, n = 1)
        else:
            return None

    @track_parse
    def triple_dot(self):
        tok = self.eat(TokDefs.triple_dot)
        if tok:
            return Quantifier(m = 1, n = None)
        else:
            return None

    @track_parse
    def quant_range(self):
        tok = self.eat(TokDefs.quant_range)
        if tok:
            text = TokDefs.whitespace.regex.sub('', tok.m[1])
            xs = [
                None if x == '' else int(x)
                for x in text.split(Chars.comma)
            ]
            m = xs[0]
            n = get(xs, 1, default = m)
            return Quantifier(m = m, n = n)
        else:
            return None

    ####
    # Parsing functions.
    #
    # Helpers to parse the elements inside a var-input.
    ####

    @track_parse
    def var_input_elems(self, require_name = False):
        # Returns a VarInput holding the guts of a positional or parameter.
        # See 'VarInput forms' for details and examples.

        # Try to get a valid name, which could be a name or a choice.
        tok = self.eat(TokDefs.valid_name)
        name_or_choice = tok.text if tok else None

        # Check for an equal sign.
        assign = bool(self.eat(TokDefs.assign))

        # Collect the rest of the choices.
        rest = []
        require_sep = not assign
        while True:
            c = self.next_choice(require_sep = require_sep)
            require_sep = True
            if c:
                rest.append(c)
            else:
                break

        # Setup default parameters for the VarInput we will return.
        name = name_or_choice or None
        choices = rest

        # Check for errors and make adjustments where needed.
        if require_name and not name:
            self.error(ErrKinds.unnamed_positional)
        elif assign and not choices:
            self.error(ErrKinds.assign_without_choices)
        elif assign and not name:
            self.error(ErrKinds.assign_without_name)
        elif name and (not assign) and choices:
            # Occurs when Parameter has choices, but no name: <a|b|c>
            choices = [Choice(text = name)] + choices
            name = None

        # Boom.
        return VarInput(name = name, elems = choices)

    @track_parse
    def next_choice(self, require_sep = True):
        # If needed, make sure there is a choice separator (|).
        if require_sep and not self.eat(TokDefs.choice_sep):
            return None

        # First try for a quoted-literal.
        e = self.quoted_literal()
        if e:
            return Choice(text = e.text)

        # Otherwise, the choice must be a valid-name.
        tok = self.eat(TokDefs.valid_name)
        if tok:
            return Choice(text = tok.text)
        else:
            return None

    ####
    # Parsing bracketed expressions: () [] <>.
    #
    # - The primary helper: get_bracketed().
    # - Its helper functions to manage details for each kind of expression.
    # - A helper used to enforce against empty Groups.
    ####

    def get_bracketed(self, kind):
        # Takes a GBKinds value indicating the kind of bracketed expression
        # to parse. Does one of the follow:
        #
        # - Returns a ParseElem (success).
        # - Returns None (no opening bracket to get started)
        # - Raises an error (parses an expression partially, then must halt).
        #

        # Try to eat the opening bracket.
        tds = GBTDs[kind]
        tok = self.eat(*tds)
        if not tok:
            return None

        # Based on the Token we got, determine closing bracket TokDef.
        closing_td = BPairs[tok.kind]

        # Get group name attached to opening bracket, if any.
        group_name = get(tok.m, 1)

        # Parse the guts of the bracketed expression, using the helper
        # correspondng to the kind of expression.
        #
        # For groups, the helper has to be called with group-name, and the
        # returned Group has to be adjusted for square brackets.
        helper_method = getattr(self, f'gb_guts_{kind}')
        if tds == OpeningTDs.group:
            e = helper_method(group_name = group_name)
            if e and closing_td.isa(TokDefs.brack_close):
                e.required = False
        else:
            e = helper_method()

        # Raise if we cannot get the closing TokDef.
        if not self.eat(closing_td):
            td = closing_td
            self.error(
                ErrKinds.unclosed_bracketed_expression,
                closing_td = distilled(closing_td, 'kind', 'regex'),
            )

        # Return the ParseElem.
        return e

    def gb_guts_positional(self):
        vi = self.var_input_elems(require_name = True)
        return Positional(
            name = vi.name,
            elems = vi.elems,
        )

    def gb_guts_parameter(self):
        vi = self.var_input_elems()
        return Parameter(
            name = vi.name,
            elems = vi.elems,
        )

    def gb_guts_group(self, group_name):
        ve = self.variant_elems()
        elems = ve.elems if ve else []
        g = Group(
            name = group_name,
            elems = elems,
        )
        return self.require_elems(g)

    def gb_guts_parameter_group(self, group_name):
        elems = self.parse_some(self.any_parameter, top_level = False)
        g = Group(
            name = group_name,
            elems = elems,
        )
        return self.require_elems(g)

    def gb_guts_opt_spec_group(self, group_name):
        ose = self.opt_spec_elem()
        elems = [ose] if ose else []
        g = Group(
            name = group_name,
            elems = elems,
        )
        return self.require_elems(g)

    def require_elems(self, e):
        if e.elems:
            return e
        else:
            self.error(ErrKinds.empty_group, element = e)

    ####
    # Eating tokens.
    ####

    def eat(self, *tds):
        # This is the method used by parsing functions to get another Token.

        # The caller provides 1+ TokDefs, which are put in self.menu.
        self.menu = tds
        self.lexer.debug(wanted = '|'.join(td.kind for td in tds))

        # Ask the RegexLexer for another Token. That won't succeed unless:
        #
        # - Token is in list of TokDefs appropriate to the parsing mode.
        #
        # - Token is of immediate interest to the parsing function that
        #   called eat(), and thus is in self.menu.
        #
        # - Token satifies other criteria (indentation, etc) checked by
        #   the Token validator function: see self.taste() below.
        #
        tok = self.lexer.get_next_token()
        if tok is None:
            return None
        elif tok.isa(TokDefs.eof, TokDefs.err):
            return None
        else:
            self.lexer.debug(
                eaten = tok.kind,
                text = tok.text,
                pos = tok.pos,
                line = tok.line,
                col = tok.col,
            )
            self.eaten.append(tok)
            return tok

    def taste(self, tok):
        # This is the Token validator function used by RegexLexer. It checks
        # whether the Token is a kind of immediate interest and whether it
        # satisifes the rules regarding indentation and start-of-line status.

        # The most recent eat() call set the menu to contain the TokDefs of
        # immediate interest. Return false if the current Token does not match.
        if not tok.isa(*self.menu):
            return False

        # If SpecParser has no indent yet, we are starting a new
        # top-level ParseElem and thus expect a first-of-line Token.
        # If so, we remember that token's indent and line.
        if self.first_tok is None:
            if tok.is_first:
                self.lexer.debug(ok = True, is_first = True)
                self.first_tok = tok
                return True
            else:
                self.lexer.debug(ok = True, is_first = False)
                return False

        # A helper to call debug() for the remaining scenarios.
        # The reason explains why the token is OK.
        def do_debug(reason):
            self.lexer.debug(
                ok = bool(reason),
                indent_reason = reason,
                self_indent = self.first_tok.indent,
                tok_indent = tok.indent,
                caller_offset = 1,
            )

        # For subsequent tokens in the expression, we expect tokens either from
        # the same line or from a continuation line indented farther than the
        # first line of the expression.
        if self.first_tok.line == tok.line:
            do_debug('line')
            return True
        elif self.first_tok.indent < tok.indent:
            do_debug('indent')
            return True
        else:
            do_debug(False)
            return False

    ####
    # Converting the SpecAST to a Grammar.
    ####

    def build_grammar(self, sa):
        # TODO.
        return sa

    ####
    # Other helpers.
    ####

    def require_is_first_token(self):
        # Resets the parser's indent-related attributes, which will
        # cause self.taste() to reject the next token unless it is
        # the first on its line (aside from any indent).
        self.first_tok = None

    def parse_some(self, method, **kws):
        # Takes a parsing function.
        # Collects as many elems as possible and returns them.
        elems = []
        while True:
            e = method(**kws)
            if e is None or e == []:
                break
            else:
                elems.append(e)
        return elems

    def error(self, error_kind, **kws):
        # Called when spec-parsing fails.
        # Raises ArgleError with kws, plus position/token info.

        # Setup.
        lex = self.lexer
        tok = lex.curr
        if tok:
            tok = distilled(lex.curr, 'kind', 'text')

        # Assemble the exception keyword args, in a specific order.
        err_kws = dict(
            msg = ErrMsgs[error_kind],
            error_kind = error_kind,
        )
        err_kws.update(kws)
        err_kws.update(
            mode = self.mode,
            pos = lex.pos,
            line = lex.line,
            col = lex.col,
            next_token = tok,
            parse_stack = self.parse_stack,
        )

        # Create error, attach parse context, and raise.
        err = SpecParseError(**err_kws)
        err.parse_context = lex.get_context().for_error
        raise err

