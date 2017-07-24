####
# Parser.
####

p = Parser()

p.parse(args = None)
p.parse_known(args = None)
p.help_text(section = None)
p.error_text()
p.warn(msg)
p.error(msg = None, code = None))
p.exit(code = None, msg = None)

####
# Opts.
####

o = Opt(
    option     = '--job-id',            # Or string-spec with option, aliases, and arg_name.
    aliases    = ['-j', '-J', '--jid'], # Or just one string.
    n_args     = 1,
    repeatable = False,                 # If true, append values.
    choices    = ('A', 'B', 'C', 'D'),
    required   = False,
    tolerant   = False,                 # Setting option makes grammar fully tolerant.
)

####
# Examples.
####

p = Parser(
    # Via simple Opt.
    Opt('--since TERM', type = int, default = lib.last_updated + 1),
    Opt('--limit N', type = int, default = 0),
    Opt('--rebuild'),
    Opt('--experiment EXP'),
    Opt('--stats'),
    Opt('--month M'),
    Opt('--search TERM', repeatable = True),
    Opt('--get ITEM'),

    # Via full Opts.
    Opt(
        'task',
        choices = 'configure submit upload start get stop download find'.split(),
        desc    = 'The odin-client task to run',
    ),

    # Via dict.
    dict(
        option  = '--odin-env ENV',
        groups  = 'general',
        default = 'dev',
        desc    = "Odin environment ('production' for most users).",
    ),

)

####
# SimpleSpec.
####

'''

For example:

    --verbose --type A <x> <y> -h -g

    spec = '-n NAME --foo --bar B1 B2 <x> <y>'
    p = parser(simple = spec)


    expr        = (longoption | shortoption | posarg)+

    longoption  = longopt optarg*
    shortoption = shortopt optarg*
    posarg      = "<" char+ ">"

    longopt     = "--" char+
    shortopt    = "-" char
    optarg      = [A-Z_\-\d]+
    char        = [\w\-]

Elements:

    short opt  | -h
    long opt   | --type
    opt arg    | A
    positional | <x>


Example: from spec to Opt() instances to parsing logic:

    Spec:

        -n NAME --foo --bar B1 B2 <x> <y>

    Opt instances:

        -n      nargs=1
        --foo
        --bar   nargs=2
        x
        y

    Parsing logic:

        # Initial grammar.
        grammar = n | foo | bar | x | y

        # Keep parsing until we have used all grammar elements.
        while grammar.has_elements():
            parse
            if the ParsedOpt we got is not repeatable:
                grammer = grammar - that Opt

'''

####
# GrammarSpec.
####


'''

For example:

    configure    : [general-options] ; !task=configure --odin-env --od-user
    submit       : [general-options] ; !task=submit -c -r [--start-job]
    get          : [general-options] ; !task=get -j [--json [--indent] | --b64 | --yaml]
    help         : * --help
    other1       : [-x] [-y] (<a> <b> <c> [-z])...{2,7}

    Notes about the `other1` variant:
        - A sequence of options/positionals can be occur 2 to 7 times.
        - If the -z option appears at a group boundary, we attach it
          to the group eagerly.
        - For exampler:

            # Input.
            A1 B1 C1 -z A2 B2 C2

            # ParseOption info.
            a : [A1,   A2]
            b : [B1,   B2]
            c : [C1,   C2]
            z : [True, False]

    Notes about repeating positions:

        - Only 1 positional can repeat a variable N of times.
        - Otherwise, we cannot allocate the values unambiguously.
        - For example, all of these are ambiguous:
            <a>... <b>... <c>
            <a>...{3} <b> <c>...{2} <d>
            (<a> <b>... <c>){2}

Elements:

    short opt
    long opt
    opt arg
    positional
    variant
    destination
    literal
    option group name

    :   variant divider
    []  square: grouping, optional
    ()  round: grouping, required
    <>  angle: variable
    {}  curly: quantification
    ;   boundary
    !   anchor
    =   dest-assign
    |   alternatation
    *   tolerant
    -   option-prefix
    ... repetition

'''

