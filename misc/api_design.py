####
# Parser.
####

p = Parser()

p.parse(args = None)
p.parse_known(args = None)
p.help_text(section = None)
p.error_text()
p.warn(msg)
p.error(code = None, msg = None))
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
    high       = False,                 # A high-precedence option (eg --help).
)

####
# Examples.
####

p = Parser(
    # Via simple Opt.
    Opt('--since TERM', type = int, default = 123),
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

    parsing_config = {
        allow_abbrev = True,
        opt_prefix_rgx = ...,
    },

    formatter_config = {
        program_name = '...',
        etc ...
    },

)

# All help-text section, in order.
p.help_text()

# Specific help-text sections, in the requested order.
p.help_text('usage')
p.help_text('section-foo')
p.help_text('section-foo', 'section-bar')


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

    general`      : [--verbose] [--log-file <path>]
    other`        : [--hi] [--bye]

    configure     : general` ; task=configure! --odin-env --od-user
    submit        : general` ; task=submit! -c -r [--start-job]
    get           : general` ; task=get! -j [--json [--indent] | --b64 | --yaml]
    drop          : general` ; task=drop! what=(first|last|random)! [--print] <n>
    help          : --help*
    other1        : [-a] [-b] other` <fubb>...
    other2        : [-x] [-y] other` (<a> <b> <c> [-z]){2,7}

Naming:

    short opt
    long opt
    opt arg
    positional
    variant
    partial
    destination
    literal
    option group name
    zone

Overall structure:

    foo` : PARTIAL_DEFINITION
    bar  : VARIANT_DEFINITION

Definition syntax:

    foo`      Insert the "foo" partial definition.
    ;         Divider between zones.
    !         Anchor item(s) to the front of a zone.

    -x        Short-option.
    --xy      Long-option.

    []        Grouping, optional.
    ()        Grouping, required.
    |         Alternation.

    <xy>      Variable text; assigned to "xy" in results.
    foo=bar   Literal text "bar"; assigned to "foo" in results.

    ...       Repetition: 1+ or 0+ depending on parens.
    {m,n}     Repetition: m to n, inclusive.

    *         High precedence option: if present, do a best-effort parse
              and dispatch to a callable rather that executing the
              normal program or halting on bad input.

Notes about the `other2` variant:

    - A sequence of options/positionals can be occur 2 to 7 times.

    - If the -z option appears at a group boundary, we attach it
      to the group eagerly.

    - For example:

        # Input.
        A1 B1 C1 -z A2 B2 C2      # -z with first group

        # ParseOption info.
        a : [A1,   A2]
        b : [B1,   B2]
        c : [C1,   C2]
        z : [True, False]

Notes about varying positionals:

    - Only 1 positional can occur a variable N of times.

    - Otherwise, we cannot allocate the values unambiguously.

    - For example, all of these are ambiguous:

        <a>... <b>... <c>
        <a>...{3} <b> <c>...{2} <d>
        (<a> <b>... <c>){2}

    - Similarly a varying positional cannot be used with an option taking a
    varying nargs, unless the user tells opto-py to allow it.

        - In that case, opt-py will attach arguments eagerly.

        - And users should advise their end-user to use the double-hyphen to
        designate the start of positional arguments.

'''

