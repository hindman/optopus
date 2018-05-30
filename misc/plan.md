--------

# Project name

Project names in various languages:

  - opto-py
  - opto-sc
  - opto-rb
  - opto-pl

Motto:

  - The option parser that lends a hand.

Mascot: an octopus.

--------

# Road map

- GrammarSpecParser and complex Phrase parsing.
  - Planning.
  - Basic GrammarSpecParser implementation.
  - Complex grammars:
    - Varying nargs and ntimes.
    - Keeping track of partially-parsed results.
    - Pruning no-longer-eligible subphrases.
    - Keeping track of alternatives.
    - Backtracking using those alternatives.

- Support tolerant.

- Check argparse for other behaviors.

- Opt: allow `x` or `<x>`

- Handle --opt=val.

- Constructors should support dict-based configuration. Parser does, but not
  FormatterConfig and Section.

- help_text(): usage section: when wrapping, keep options together with their
  option args.

- Wildcards mode: allow user to specify pos/opt/both/True.

- nargs and ntimes: support regex-style quantifiers, both in specs and in the
  generated USAGE help-text.

- Negatable options: `--smart-case` and `--no-smart-case`.

- API thematic configuration.

- Help text customization.

- Support allow_abbreviation boolean.

- Option customization: eg, the regex to identify long opt, short opt, etc.

- Better exception strategy.

- Man-page support.

- Integration with configuration files.

- Integration with ENV variables.

- Miscellaneous.

--------

# Notes on parsing

- https://github.com/rspivak/lsbasi
- https://en.wikipedia.org/wiki/Recursive_descent_parser
- http://effbot.org/zone/simple-iterator-parser.htm
- http://jayconrod.com/posts/37/a-simple-interpreter-from-scratch-in-python-part-1
- Language Implementation Patterns: Create Your Own Domain-Specific and General Programming Languages
- https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form

--------

# Object overview

Parser:

  - Command line option and argument parser.

Opt:

  - Configuration object used by the Parser.

  - Each represents either an option or positional argument.

ParsedOptions:

  - Object returned by Parser.parse().

  - Basic form: self.DESTINATION = VALUE.

  - Also behaves like a collection: iterable, dictable, etc.

ParsedOpt:

  - Object used by the Parser to store parsing data.

  - Represents one DESTINATION-VALUE pair.

  - Holds those two attributes, plus a collection of all Opt instances that
    played a role in arriving at that pair.

  - The Parser will store a collection of ParsedOpt instances.

  - That collection is the basis for ParsedOptions.

Phrase:

  - Object used by the parser to represent the CLI grammar and to do the
    parsing work.

  - Each Phrase can store subphrases, so the grammar forms a tree.

  - The leaves of the tree will be Phrase objects corresponding to specific Opt
    intances (ie, the options and positional arguments of interest to the
    user).

SimpleSpecParser:

  - Used to parse a simple-spec given by the user.

  - For example: `--foo FF GG -x --blort -z Z1 Z2 <q> <r> --debug`.

  - The SimpleSpecParser.parse() method returns a Phrase representing the
    CLI grammar desired by the user.

GrammarSpecParser:

  - Just like SimpleSpecParser, but can parse the more featureful variant-based
    grammars.

RegexLexer:

  - General purpose lexer used by SimpleSpecParser and GrammarSpecParser.

Token:

  - Emitted by the RegexLexer.

--------

# Terminology

Users:

  - Library: the opto-py code base.
  - User: a developer using opto-py.
  - End-user: a user running a program that uses opto-py.

Command line components:

  - For example:

        frob (find | copy) <path> [--verbose] [--type (file | dir | link)] [--rgx <patt>]

  - Positional arguments
    - Literal: `(find | copy)`
    - Variable: `<path>` or `PATH`

  - Options
    - Flags: `--verbose`
    - Non-flags: `--type` and `--rgx`

  - Option arguments
    - Literal: `(file | dir | link)`
    - Variable: `<patt>` or `PATT`

Help text sections:

  - CLI style:
    - Usage.
    - Positional arguments.
    - Options and/or option groups.
    - Custom sections.

  - Man-page style:

    - NAME
    - SYNOPSIS
    - DESCRIPTION
    - OPTIONS
    - Custom sections.

  - Terminology in opto-py:
    - Usage text: conveys the CLI grammar.
    - Options text: documents the options and positional arguments, perhaps in groups.
    - Custom sections.

--------

## Key points

There are two fundamental configuration strategies:

  - API-driven:

    - User configures a parser via the programmatic API.

    - The parser generates the help text.

    - Typically allows user to override with literal help text, if desired.

    - Examples: argparse and many others.

  - Text-driven:

    - User writes literal usage and options text.

    - Library derives the parser from that text.

    - This approach is much less common.

    - Examples: docopt.

The octo-py library combines the approaches:

  - In most respects, it is API-driven.

    - Tends to require less typing.

    - Generated usage text is mostly fine, especially for simpler projects.

    - Most developers probably prefer an API-driven approach over
      hand-formatting help text themselves.

    - API-generated help text will follow the conventions for documenting
      command-line programs -- conventions that few developers have studied in
      depth and would rather not worry about.

    - Examples confirming these points:

        # Simple programs.
        examples/daily-reading
        examples/get-pocket-items

        # More complex examples: contrast the API vs the two text examples.
        examples/odin-client-via-api
        examples/odin-client-via-text
        examples/odin-client-via-text-subparsers

  - Nonetheless, text-driven option parsers have some advantages:

    - Text-driven parsers emphasize the idea of **usage variants**, a technique
      that can greatly enhance usage-text readability -- both for simple
      programs and especially for complex programs:

            # Simple.
            frob [--debug] [--foo <f>] <path>...
            frob --help
            frob --version

            # Complex.
            git diff [options] [<commit>] [--] [<path>...]
            git diff [options] --cached [<commit>] [--] [<path>...]
            git diff [options] <commit> <commit> [--] [<path>...]

    - API-driven parsers struggle with command-lines that need any grammar that
      falls beyond the most typical cases (mainly mutually-exclusive groups and
      subcommands). On stackoverflow and bugs.python.org, for example, one can
      find many CLI use cases (some of them quite simple) that are not
      supported easily by argparse but that are straightforward in docopt.

    - And when users discuss CLI-grammar scenarios, they invariably use a
      text-oriented approach to specify the problem. In my own research, I
      experimented with defining the needed grammars via an API, but I always
      found the text-based approach simpler to express and read.

    - For those reasons, opto-py encourages a compact text-based configuration
      syntax for expressing the CLI grammar. That syntax does not try to
      address other option configurations (data types, choices, etc), and it is
      not literal usage text. Rather, it is an intuitive mechanism for
      configuring a CLI grammar. The grammar is also configurable via an API,
      but most users will prefer the simple text syntax.

    - Also, for most use cases a simple specification like `--foo F1 F2` is an
      easy way to declare an option --foo with nargs=2 and arg names F1 and F2.

Although opto-py is primarily an API-driven library, it also aims to address
some key weaknesses found in most parsing libraries.

  - Providing users with simple ways to handle CLI grammars and usage variants
    (just noted).

  - Supporting everything from quick-and-dirty scripts to complex, highly
    customized CLI programs, with other variants in between.

    - At once extreme, opto-py allows you to parse a standard command line with
      zero configuration. Just import and go.

            import opto_py
            opts = opto_py.parse_args()

    - At the other extreme, you could build the next Git or a variety of
      programs with idiosyncratic grammars, heavily customized help text, and
      many other features.

    - Sitting between the two extremes are numerous conveniences and sensible
      defaults to make option parsing easy, no matter what level of control
      your application needs.

  - Allowing users to control the generated help text in a fine-grained manner.
    One core premise of opto-py is that program complexity increases the need
    to organize and fine-tune help text, but not necessarily to hand-craft it.
    Some examples:

    - Simple top-level configurations to control basic layout and titling
      features.

    - Support for common styles: CLI vs man-page.

    - Ability to group options into sections.

    - Ability to supply hand-crafted sections whenever needed.

    - Ability to control virtually every aspect of the help text contruction
      process via basic functions (no need to subclass or dig into the parser's
      private methods and attributes).

  - Allowing users to enhance usage-text readability by being able to refer to
    groups of options and to omit either short or long options.

    - API-generated usage text tends to be poor not only because it lacks usage
      variants but also because the generated text exhaustively lists all
      options in all of their permutations (short and long).

    - Especially as the number of options grows, readability can be improved
      greatly by referring to sets of options by symbolic names rather than by
      enumerating every possibility.

    - Similarly, readability can be enhanced by focusing the usage text on just
      the long-options (or just the short-options) and then providing a mapping
      between short and long options latter in the help text.

  - Allowing users to define their arguments and options in ways that encourage
    modularity.

    - In opto-py a user defines options and arguments at atomic units, separate
      from the issues of CLI grammar, usage variants, and options help text.

    - Each of those atomic units can be assigned to one or more groups of
      related options.

    - Then those options or option-groups can be leveraged when defining the
      CLI grammar, when expressing the generated usage text, and when
      organizing the options text into sections.

  - Providing users with full access to the parser configuration. both via the
    API and in the form of standard, serializable data structures.

--------

## Why opto-py does not include subparser features

Adding the subcommand/subparser concept to an option parsing brings a bunch of
new syntax. And ultimately, the subparser concept is much less flexible (and
less intuitive) than supporting the key concepts noted above: (1) usage
variants, and (2) command line grammar.

Very few CLI tools need a full-blown subparser strategy, especially if the
option parsing library provides good support for variants and CLI grammars.

And even if we were building the next Git, we would not need the subparser
in an option parsing library. We would just do this instead:

- Use a general parser:

        git [general-options] <subcommand> [args]

- Then parse `args` with the appropriate parser, based on the value of
  `subcommand`. As long as the library makes it easy to merge the
  general-options with the subcommand-options, there is no benefit
  to modeling the library to include a subparser concept.

In other words, a complex program does not need subparsers; in just needs N
parsers.

The opto-py library will support use cases like this by providing easy ways to
combine the opts obtained from both the top-level parse and the subcommand
parse -- both the ability to fully merge those two sets of options or to keep
them separately namespaced (eg, Git uses `-C` both and the top level and in
subcommands like `git-diff`).

--------

## CLI grammars

First start with the normal rules of CLI grammar, as commonly understood:

  - Positional arguments are ordered among each other:

        P1 P2 P3 ...

  - Options can be ordered in any way:

        --x4 --x1 --x3 --x2 ...

  - Options can be freely interspersed among the ordered positional arguments.

        --x3 P1 --x1 --x4 P2 --x2 P3 ...

In addition, a CLI grammar can have boundary points:

  - Each boundary creates a division between "zones" in a given usage variant.

  - Within a zone, the grammar can require that one or more positional
    arguments and/or options appear first, in order.

Side note on CLI grammars relative to regexes:

  - opto-py will borrow many concepts from regular expressions.

  - But CLI grammar parsing seems not directly amenable to handling via regex
    parsing approaches.

  - The crucial difference:

    - Positionals are ordered among themselves.

    - Options can appear in any order (ignoring boundaries and anchors).

  - That special flexibility makes it not very intuitive to convert a CLI
    grammar into a corresponding regex-style grammar.

      - At every stage, any of the options are possible.
      - But then once an option appears, it cannot appear again.
      - That means CLI parsing is highly context-sensitive.
  
Within those rules in mind, we can handle the grammar of a typical subcommand
program as follows:

  - For example:

        frob [general-options] ; !<subcommand> <x> <y> [-a] [-b]

        General options:
          --log
          --debug

  - Requirements of that grammar:

    - Zone 1: some general options in any order.

    - Boundary point.

    - Zone 2: first the subcommand and then other positional args and options
      using the normal rules.

  - Usage examples:

        # Valid.
        frob               delete X Y
        frob --log         diff   X Y -a -b
        frob --log --debug copy   -a X -b Y

        # Invalid.
        frob --log -a diff X Y

  - A complex CLI with multiple layers of subcommands:

        frob [optsA]
             ; !<comm1> !<a> <b> <c> [optsB]
             ; <comm2> <d> <e> [optsC]
             ; !<comm3> !<h> !<i> [optsD]

  - The grammar has 4 zones:

    - optsA:
      - Normal rules.

    - comm1
      - Two positionals must appear first, then normal rules.
      - Note: optsA must be to left of comm1, and optsB to right.

    - comm2
      - Normal rules.
      - Note: either comm2 or any optsC means that no more optsB can appear.

    - comm3
      - Three positionals must appear first, and then normal rules.

  - You do not need a way to anchor items to the end of a zone.

    - Imagine that we wanted to adjust the grammar to require two positionals
      at the end of the comm2 zone:

            frob [optsA]
                 ; !<comm1> !<a> <b> <c> [optsB]
                 ; <comm2> <d> <e> [optsC] <f>! <g>!
                 ; !<comm3> !<h> !<i> [optsD]

    - We could achieve that instead by establishing a new zone:

            frob [optsA]
                 ; !<comm1> !<a> <b> <c> [optsB]
                 ; <comm2> <d> <e> [optsC] ; <f> <g>
                 ; !<comm3> !<h> !<i> [optsD]

Handling literal option-arg choices.

- Consider these examples:

        frob (find|copy|delete) <path> --type (file|dir|link) --rgx <patt>

        frob --group (a|b|c|d) (x|y)

- Both raise ambiguities: are `--type` and `--group` flags or options that take
  literal args?

- Or here: is --group a flag or an option taking one, or even two, args?

        frob --group <g> (x|y)

- The equal-sign syntax seems to clarify, but it helps only for the case when
  nargs=1.

        frob --group=(a|b|c|d) (x|y)

- We could use curly braces only for literal option-args, but that doesn't
  provide a way to specify variable option-args.

        frob --group {a|b|c|d} (x|y)

- The way to resolve these problems is as follows:

  - If an option takes args, the option-phrase must be enclosed in brackets,
    either square or round.

        (-x <x1> <x2>)
        [-y Y]
        [-z Z1...]

    - The CLI grammar rule is that if brackets begin with an option, the
      remaining args inside the brackets are option-args, not positionals.

    - With this convention in place, expressing literal option-args is
      straightforward too. For example, this option takes 3 args, the first 2
      are literal-choices and the last is a variable-arg:

            (-x (a|b|c) (d|e) <x>)

    - And it even becomes possible to define grammar variants based on literal
      option-args values. For example, we can elaborate on the previous
      example, creating 3 variants driven by literal option-arg values:

            (-x (b|c) d <x1>)
            (-x a     e <x1> <x2>)
            (-x a     d <x1> <x2> <x3>)

- The SimpleSpecParser glosses over these issues via some assumptions:

  - It does not support literal args.

  - It uses different syntaxes for variable args: option vs positional:

        --foo F1 F2 <x1> <x2>

--------

## The configuration API

- See examples/odin-client-via-api.

- All options can be defined with fairly simple dictionaries, an approach
  similar to many option parsers, one with a key difference: it encourages the
  user to create a data structure rather than messing so much with API calls.

- The `option` key has a short syntax to define the option, short alias,
  arg_name, and nargs: '--job-config-file -c PATH'

- Several keys support a fully explicit syntax and a compact form for basic use
  cases.

- A list-of-dicts is sufficient for many CLI use cases. With that, the library
  could parse well and generate good usage text.

- If needed, the user could supply a grammar. Either way, the library will end
  up having a grammar that it could deliver back to the user (eg, for
  debugging).

- If desired, the user can customize the sections in the usage text, some of
  them hand-crafted and some of them generated by the library. In this way the
  user can control the key aspects of the usage: section ordering; section
  titles; layout style (eg, compact 2-column or man-page); capitalization
  rules; widths; and conventions for showing default values.

- Positional options (eg `task` below) are mostly like any other option: in
  particular they can take arguments. One difference is that the option always
  takes at least one argument -- the value itself.

--------

## Misc

- Should be intuitive and declarative, not based on a bizarre syntax or on
  user-created complex data structures.

- That said, the parser's configuration should be expressible as a data
  structure. This is important for testing, debugging, easy integration with
  config files, and using other libraries for data validation.

- If needed (eg, for complex applications) users should have full control over
  documentation. This includes both usage/help text and the styling of error
  messages.

- For quick-and-dirty projects, the module should generate automatic
  documentation based on requirements specified for the arguments and options.

- Should handle both positional arguments and options.

- Should have a design that is friendly to customization.

- Easy system for validators to be combined flexibly.

- Should be applicable to validating subroutine arguments, both positional and
  key-value.

- Should support subcommand applications, like svn or git.

- Should easily support different help types: (a) brief usage/synopsis, (b)
  full help or man-page, and (c) extras or examples.

- Include ability to merge options from several sources: ENV variables, config
  files, command-line options. Note that the purpose of the configuration
  sources (ENV vars and config files) is to set the default values used by the
  command-line option parser. When defaults are supplied, it should also cause
  a required option to become non-required (in other words, whenever default is
  set for an option, it forces required to become False).

- Combine the best of many approaches seen in other arg parsers.

- Make it easy to test the option parser.

- Error handling should be under the user's control, if they want it. This is a
  serious flaw in some parsers (eg argparse). The library should support both
  "automatic" mode (where the parser will eagerly print help or error-msg and
  quit) or non-automatic mode (where the parser will simply return an object
  containing all information and allow the user to decide what to do).

- If possible, allow users to customize by writing simple functions or hooks
  rather than having to subclass everything. Consider using the pluggy library
  so that users can implement simple function hooks.

- Start simple: begin with core behaviors; don't support more flexibility until
  a basic working system is in place.

- Convention over configuration: sensible defaults to allow the most common
  path to be followed with minimal setup.

- Support for --version. Show the application's name and version number.

- Provide helper functions for warn(), exit().

- Support both configuration styles: (1) Per-option configuration (eg, argparse
  and most other systems); and (2) thematic configuration (eg, set several
  default values at once, or several data-types at once).

- Allow the user to have hidden options (eg for developers only).

- The Click documentation criticizes the docopt approach, because the help text
  cannot be rewrapped in the face of different terminal widths. Point taken ...
  but so what: if the terminal is very wide, I still want the help text to be
  80 chars or less, for readability. And almost no one uses terminals less than
  80 characters wide.

- Usage text in man-page or CLI style.

- For file args, handle `-` as stdin or stdout.

- Add a --bash-completion option.

- Support @somefile.txt: user supplies CLI args via a file.

- Support file and dir types.

- Support parse_known_args() and parse_tolerant().

- Support allow_abbreviation boolean.

- Flexible parse: just accept any `--key VAL` pairs on the command line.

- Late parser config: configure parser; get args; call user's code; user can
  check args, and modify the parser at run-time

- When building usage text, allow control over opts-then-positionals vs
  positionals-then-opts.

- The continuum of use cases:

  - Zero configuration.
    - opts are flags
    - everything else goes in args

            opts = Parser().parse_args()

  - Mostly-zero configuration.
    - zero: True if zero is None and self.opts is empty

            p = Parser(
              Opts('--foo X', type = int)
              zero = True
            )

  - Bare-minimum configuration
    - User supplies a simple spec.
    - <x> for positionals.
    - X for option args.
    - All values are strings.

            spec = '-n NAME --foo --bar B1 B2 <x> <y>'
            p = Parser(simple = spec)

  - Basic configuration via API.
    - Similar to argparse.
    - But a more compact API.
    - More powerful and flexible.

  - Full control.
    - Fine tuned usage text.
    - CLI grammars.
    - Lots more.

--------

## Grammar-configuration syntax

- The grammar-configuration syntax will look roughly like usage text.

- But it will be more compact, easier to type, and easier to scan visually and
  grasp quickly.

- And it will include a small number of additional syntax elements focused on
  issues of CLI grammar.

  - Variants and their names.
  - Ability to refer to entire groups of options.
  - Zone boundaries.
  - Anchored items.
  - Destinations for literal-positionals.
  - Fully tolerant variants.

- General syntax:

        VARIANT_NAME : VARIANT_SPEC

- An example:

        get : [general-options] ; !task=get (-j XX) [--json [--indent] | --b64 | --yaml]

- Syntax elements:

        :         # divider between variant-name and variant-spec

        []        # grouping + optional
        ()        # grouping + required
        |         # logical OR

        -x        # short option
        --zoo     # long option

        <x>       # variable argument (supplied by end-user)
        X         # ditto
        x         # literal argument

        ;         # zone boundary
        !         # anchor

--------

## A collection of argparse problems and scenarios

    https://stackoverflow.com/questions/18025646

        Grammar needed:

            frob -x [other-opts]
            frob -y -z [other-opts]

    https://stackoverflow.com/questions/4466197

        Grammar needed:

            frob [ -s | -f [-m] ] <host>
            frob -h

    https://stackoverflow.com/questions/28660992

        Grammar needed:

            - Option takes 2 args.
                - The 1st arg must be A|B|C.
                - The 2nd arg must be X|Y|Z.

            frob [-a {A,B,C} {X,Y,Z}]
            frob -h

        Solvable if the parser allows `choices` to take a list:

            dict(
                option = '-a',
                nargs = 2,
                choices = [(A, B, C), (X, Y, Z)],
            )

    https://stackoverflow.com/questions/25626109

        Grammar needed: if -x if present, -a and -b are also required.

            frob [-y] [-z]
            frob -x -a -b [-y] [-z]

    http://bugs.python.org/issue11588

        "mutually inclusive group"

        Grammar needed:

            frob -o           [-x]
            frob -r (-p | -s) [-x]

        Grammar needed:

            frob -a -b [-x]
            frob -c -d [-x]

    http://bugs.python.org/issue10984

        Grammar needed:

            - User has three flags: -a -b -c
            - Plus some other flags: -x -y
            - The -b flag is incompatible with both -a and -c.

            frob [-b]      [-x] [-y]
            frob [-a] [-c] [-x] [-y]

    https://stackoverflow.com/questions/11455218

        Grammar needed:

            - If -y is given, -x is required.

            frob [-x] [-z]
            frob -y -x [-z]

    https://stackoverflow.com/questions/27681718

        Grammar needed:

            frob [-x] [-y] (<a> <b> <c>)...

        Approach:

            - Allow positionals to be repeated, with append-like action.

    https://stackoverflow.com/questions/19114652

        Grammar needed:

            - The entire CLI grammar can be repeated.

            frob (version <n> --file <p1> <p2>)...

        Control how choices are listed in usage text:

            - eg, don't repeat them.

                -n {foo,bar,baz}, --name {foo,bar,baz}

            - or refer to them by name, and then define the name later

                --othername FOO

                where FOO
                    foo
                    bar
                    baz

    Help text with subparsers:

        frob -h
            - some people want just top-level help
            - others want all help : top-level all subparsers

    https://stackoverflow.com/questions/4042452

        If program has required args/options, but it is run
        with zero args, provide help text, not error text.

        It's trivial if you have a grammar:

            frob <x> <y> [-z]
            frob --help
            frob

    https://stackoverflow.com/questions/27258173

        - Required: -x, -y, or both

        frob -x [-y] [-z]
        frob -y [-x] [-z]

    https://stackoverflow.com/questions/5257403

        - wants nargs to allow a range: eg, 1 to 3.

        - this works, but starts to look ugly if N gets larger

            frob -x A [B [C]]

            frob -x A [B [C [D [E [F]]]]]

        - other possibilities:

            frob -x A...{7}
            frob -x A...{1,3}
            frob -x A...{0,3}
            frob -x A...{3,}

    https://stackoverflow.com/questions/4692556

        frob [-x] [-y] all
        frob [-x] [-y] <pos>...

--------

## Phrase objects

Attributes:

    subphrases      : []
    ntimes          : examples: N * + ? (m,n) (m,None), func, iterable of ints
    required        : not needed; can be handled by ntimes
    phrase_type     : OPT | POS | PHRASE | ZONE
    subphrase_logic : AND | OR
    anchored        : bool

The top-level Phrase represents the entire CLI grammar and is the root node
in a tree of Phrase objects.

The leaf nodes of the tree are always OPT or POS.

There needs to be restrictions on nodes in the tree that take variable N of
arguments. This applies especially to POS nodes with a varying ntimes attribute
and, in more limited ways, to OPT nodes that have a varying nargs attribute.

- The entire tree cannot contain more than one POS node with a variable
  ntimes attribute. Conceivably, a rule or policy could be applied
  to resolve the ambiguity created by multiple POS nodes with variable
  ntimes. But at least in the default case (ie, without such a policy)
  only one POS can have a variable ntimes.

- In addition, a POS node with variable ntimes and an OPT node with variable
  nargs raise similar ambituities -- at least in the absence of a
  policy. In this case, one possible policy is the use of `--` to signal
  the boundary between options and positional arguments.

- Similar issues arrive if an option resides in multiple leaves in the Phrase
  tree and if those Opt instances have varying ntimes attributes. For example,
  if -x is in one leaf with ntimes=(1,3) and also in another leaf with
  ntimes=(1,3), and if there are 4 -x options in the CLI args, there is not an
  unambiguous way to bind those CLI args to the leaves.

Example 1:

    # Grammar:

    [-b]      [-x] [-y]   # -a and -b are mutex,
    [-a] [-c] [-x] [-y]   # and -b also allows -c

    # Phrase tree:

    PHR  (1,1)  OR

        PHR  (1,1)  AND
            OPT -b (0,1)
            OPT -x (0,1)
            OPT -y (0,1)

        PHR  (1,1)  AND
            OPT -a (0,1)
            OPT -c (0,1)
            OPT -x (0,1)
            OPT -y (0,1)

    # Phrase alternatives:

        -b  [0,0]
        -a  [1,0]
        -c  [1,1]
        -x  [0,1]  [1,2]
        -y  [0,2]  [1,3]

Example 2:

    # Grammar:

    [-x]  [-z] <a>
    -y -x [-z] <a> [<b>]   # If -y, then -x is required and <b> is allowed.

    # Phrase tree:

    PHR  (1,1)  OR

        PHR  1  AND
            OPT -x (0,1)
            OPT -z (0,1)
            POS a  1

        PHR  1  AND
            OPT -y 1
            OPT -x 1
            OPT -z (0,1)
            POS a  1
            POS b  (0,1)

    # Phrase alternatives:

        -x  [0,0]  [1,1]
        -z  [0,1]  [1,2]
        -y  [1,0]
        pos [0,1]  [1,3]  [1,4]

Example 3:

    # Grammar:

    [-x] [-y] (<a> <b> <c>)...

    # Phrase tree:

    PHR  (1,1)  AND

        OPT -x (0,1)

        OPT -y (0,1)

        PHR (1,None) AND
            POS a  1
            POS b  1
            POS c  1

    # Phrase alternatives:

        -x  [0,0]
        -y  [1,0]
        pos [2,0]  [2,1]  [2,2]

Example 4:

    # Grammar:

    (-x | -y | -z -q) [-a] <b>

    # Phrase tree:

    PHR  (1,1)  AND

        PHR (1,1) OR

            OPT -x 1
            OPT -y 1
            PHR    1  AND
                OPT -z 1
                OPT -q 1

        OPT -a (0,1)
        POS b  1

Example 5:

    # Grammar:

    (-a -x | -b... | [-a] -c -d) [-e | -f] [-g] <h> [<i>...] ([-j -k]... | -m -n)

    # Phrase tree:

    PHR  (1,1)  AND

        PHR (1,1) OR

            PHR (1,1) AND
                OPT -a 1        # Note: -a could go here.
                OPT -x 1

            OPT -b (1,None)

            PHR (1,1) AND
                OPT -a (0,1)    # Note: or here.
                OPT -c 1
                OPT -d 1

        PHR (0,1) OR
            OPT -e 1
            OPT -f 1

        OPT -g (0,1)

        POS h (1,1)

        POS i (0,None)

        PHR 1 OR

            PHR (0,None) AND
                OPT -j 1
                OPT -k 1

            PHR 1 AND
                OPT -m 1
                OPT -n 1

Example 6:

    # Grammar:

    --foo F1 F2 -x -y <a> <b>

    # Phrase tree:

    PHR  (1,1)  AND
        OPT --foo 1  nargs=2
        OPT -x    1
        OPT -y    1
        POS a     1
        POS b     1

Example 7:

    # Grammar:

    (-x X1 -y Y1)...

    # Phrase tree:

    PHR  (1,None)  AND
        OPT -x 1  nargs=1
        OPT -y 1  nargs=1

Example 8:

    # Grammar:

    .general-options : [-m] [-n] [-o]
    configure        : [general-options] ; !task=configure --odin-env --od-user
    submit           : [general-options] ; !task=submit -c -r [--start-job]
    get              : [general-options] ; !task=get -j [--json [--indent] | --b64 | --yaml]
    help             : * --help
    other1           : [-x] [-y] (<a> <b> <c> [-z])...{2,7}

    # Phrase tree:

    PHR  (1,1)  OR

        # configure
        PHR (1, 1) AND

            # general-options zone
            ZONE
                PHR 1 AND
                    OPT -m (0,1)
                    OPT -n (0,1)
                    OPT -o (0,1)

            ZONE
                PHR 1 AND
                    POS task 1         value=configure  anchored=True
                    OPT --odin-env 1
                    OPT --od-user  1

        # submit
        PHR (1, 1) AND

            # general-options zone
            ZONE
                ...

            ZONE
                PHR 1 AND
                    POS task 1         value=submit  anchored=True
                    OPT -c 1
                    OPT -r 1
                    OPT --start-job (0,1)

        # get
        PHR (1, 1) AND

            # general-options zone
            ZONE
                ...

            ZONE
                PHR 1 AND
                    POS task 1         value=get  anchored=True
                    OPT -j 1
                    PHR 1 OR
                        PHR 1 AND
                            OPT --json 1
                            OPT --indent (0,1)
                        OPT --b64 1
                        OPT --yaml 1

        # help
        PHR (1, 1) AND
            OPT --help 1      tolerant=True

        # other1
        PHR (1, 1) AND
            OPT -x (0,1)
            OPT -y (0,1)
            PHR (2,7) AND
                POS a 1
                POS b 1
                POS c 1
                OPT -z (0,1)

--------

## Phrase.parse()

What causes the parsing to require alternatives and backtracking?

- Options that reside in multiple alternative locations in the Phrase tree. For
  example, when we encounter an -x among the CLI args, we do not know in
  advance which subphrase to bind it with:

        PHR OR
            PHR AND
                -x
                -z
            PHR AND
                -x
                -y

- Options that reside in multiple non-alternative locations in the Phrase tree,
  and where one of those leaves has a varying ntimes attribute. In this
  example, we do not know in advance how greedily to bind -x CLI args to the
  first leaf in the tree.

        PHR AND
            PHR AND
                -x  ntimes=(1,3)
            PHR OR
                PHR AND
                    -x  ntimes=1
                    -y
                PHR AND
                    -z
                    a

- Destinations for positional arguments with varying ntimes attributes or
  (closely related) options with varying nargs attributes. In these two
  examples, when we encounter a non-option CLI arg, we do not know in advance
  whether to bind it greedily:

        PHR AND
            POS a (1,3)
            POS b 1
            POS c 1

        PHR AND
            OPT -x nargs=(1,3)
            POS b 1
            POS c 1

Decisions when processing a CLI arg:

- Is it an option or non-option?

  - Option:

    - If it can bind to only one leaf in the Phrase tree, do so.

    - If there are alternatives leaves, collect them and prepare for possible
      backtracking. We will try each leaf in order.

  - Non-option:

    - Is there a current-option that can take args?

      - No: do not bind.
      - Yes, static: just bind.
      - Yes, variable: bind with possible backtracking.

    - Otherwise, we will bind to positional Opts.

      - Static: just bind.
      - Variable: bind with possible backtracking.

--------

## nargs, ntimes, and the returned data structures

General principles:

  - ntimes controlls optional/required behavior: is the thing (an option or
    positional) present and, if so, how many times?

  - nargs is straightforward for options: how many args does the option take?

  - For positionals, the nargs/ntimes distinction is not quite as obvious, but
    the optional/required note above points us in the right direction. For
    example:

        frob <x> <y> <y> [<z>]

        opt   nargs   ntimes
        --------------------
        x     1       1       # A typical positional: required with 1 arg.
        y     2       1       # Also required, but 2 args.
        z     1       (0,1)   # Optional, with 1 arg.

  - In other words, for positionals:

    - Optional/required behavior is governed by ntimes.
    - Adjacent-repetition of a positional is governed by nargs.
    - Positionals always have a nargs of at least 1.

  - Internally, a ParsedOpt will store values as a 2D array:

      self._values = [
          [a1, a2, ...],  # First time.
          ...             # Etc.
      ]

  - But ParsedOpt.value will return a value flat as possible, based on nargs
    and ntimes (unless user requests non-flattened data). See the examples
    below.

Options:

  - nargs 0

        # ntimes 0 or 1
        foo: True

        # ntimes 2+
        foo: [
            True,  # First time.
            True,  # Second time.
            ...    # Etc.
        ]

  - nargs 1

        # ntimes 0 or 1
        foo: a1

        # ntimes 2+
        foo: [
            a1,   # First time.
            a2,   # Second time.
        ]

  - nargs 2+

        # ntimes 0 or 1
        foo: [a1, a2, ...]

        # ntimes 2+
        foo: [
            [a1, a2, a3, ...],  # First time.
            [a1, a2, ...],      # Second time.
            ...                 # Etc.
        ]

Positionals:

  - Example grammar and corresponding params:

        frob (<a> <a> <b> <c>){3} <d> [<e>]

            nargs  ntimes
        -----------------
        a   2      3
        b   1      3
        c   1      3
        d   1      1
        e   1      (0,1)

  - Example usage and returned data:

        frob  10 11 20 30  100 101 200 300  1000 1001 2000 3000  DD

        a: [
            [10, 11],      # First time.
            [100, 101],    # Second time.
            [1000, 1001],  # Third time.
        ],
        b: [
            20,
            200,
            2000,
        ],
        c: [
            30,
            300,
            3000,
        ],
        d: DD
        e: None

--------

## Other tools

App::Cmd

- Conclusion: not sure that I'm sold on this.

- The documentation is difficult.

- The module is uses Params::Validate and Getopt::Long::Descriptive, and it
  does not appear to be flexible in that regard.

Getopt::Long::Descriptive

- Front end for Getopt::Long

- Promising in several respects.

- One could write a subclass to modify help text output.

- But it does not support the basic element of a option arg name (eg --logfile
  PATH)

- So subclassing will take you only so far.

- Supports concept of "implies": if -X, then -Y and -Z are required.

- Support concept of a hidden option (not in help text).

Getopt::Tabular

- Tabular spec definition

- Validation

- Help text -- not bad, but not controllable

- Can parse an array besides ARGV

- Looks unmaintained.

Getopt::Lucid:

- Interesting approach

- emphasizes readability of specification

- uses a chainable module when defining specs

- also allows you to merge options with config

- does not produce help text

Getopt::Euclid

- Creates parser from your application's POD, specifically:

- The POD can also include validation assertions.

- Still active.

- Takes input from @ARGV and puts results in %ARGV

- I don't like the fact that it uses globals and is non-OO

Getopt::Simple

- Wrapper around Getopt::Long

- Produces help text.

Getopt::Declare

- Builds option parser from a help-text string

- It's an interesting idea.

- Requires a special syntax to define the spec and that syntax is embedded in
  the help string

Other Perl modules I briefly checked:

- Abridged
- Auto
- Base
- Chain
- Clade
- Compac
- Complete::Args
- Easy
- Fancy
- Flex
- Helpful
- Lazy
- LL
- OO
- Param
- Plus
- Regex
- Tiny
- Usaginator
- Params::Validate
- Params::Smart
- Getargs::Mixed
- Getargs::Long
- Pod::WikiDoc

Pod::Usage

- You document your application with POD.

- Then you simply use  Getopt::Long and PodUsage.

- In addition to getting a usage message, you get a man page (based on pod2man)
  and your application is CPAN-ready.

- As a result, you have a decent level of control over the look of the usage
  and help text. To the extent that you can't control appearance, at least your
  documentation looks standard.

- When you invoke pod2usage, you can specify a verbosity level, which controls
  the POD sections that are rendered.

- The main drawback is POD itself.

- You could wrap the module to simplify usage further: trap the WARN from
  GetOptions and invoke your own help(); then invoke pod2usage if --help or
  --man are requested.

MooseX::GetOpt

- front end for Geopt::Long

- requires using Moose

- not many new ideas here

Python plac module

- This module wraps argparse.

- It deduces the needed parser based on: the signature of the main() function
  (for positional arguments); annotations of the main() function (for options).

- Advertises itself as being super easy to use and setup, but by the time you
  create all of the awkward-looking annotations, it seems like argparse would
  have been simpler.

Ruby Trollop

- Very simple to use

- Not much customizability.

Python argparse module

- Important concept: the module should parse/validate arguments or options

Python's docopt:

- important concept: write good usage text; build opt parser from it

- important (but ultimately flawed) concept: parsing should be separate from
  validation

- Explicitly does not provide data validation. Rather, it focuses on option
  parsing and logical validation (ie, the presence/absence of args/options in
  relation to each other).

- tried to use it, but seems half-baked

- seems to have a lofty goal (infer complex logic and arg/option
  interdependencies and requires simply from a usage text), but it's not clear
  that the parsing code is up to the task

- It's easy, for example, to cause their demo example (naval_fate.py) to fail
  just be making a few obvious changes to the configuration.

- There is a fundament problem with separating arg parsing from data
  validation. Because docopt does not validate, it lacks the concept like
  argparse's `choices`. This is a fundamental problem: a library focused on
  giving the user clear usage text has no mechanism for telling the user what
  the allowed values are for an option-argument.

- The library also has an awkward way of creating the returned opts dictionary,
  with keys like `--foo` and `<path>`.

- The library's returned dict also divorces an option's presence (a True/False
  flag) from the value of its argument. For example, a spec like `-C PATH`
  would produce a dict like `{'-C': True, 'PATH', '/tmp/blah'}`. That seems
  like a fundamental problem.

Python: Click

- interesting but opinionated

- explicitly rejects customizability of help output

- option parsing configuration ends up spread widely across your code base,
  next to the actual functions that do the work, rather than centralized

- is lazily composable

- follows the Unix command line conventions

- supports loading values from environment variables

- supports for prompting of custom values

- nestable and composable

- supports file handling

- useful helpers: getting terminal dimensions; ANSI colors; fetching direct
  keyboard input; screen clearing; finding config paths; launching apps and
  editors.

Ruby Thor

- Similar to Fabric in its approach.

Ruby GLI

Python invoke:

- Part of the Fabric ecosystem.

