
####
#
# This demo is designed to exercise most features of the spec-syntax.
# It is NOT intended to represent a realistic or sane use case.
#
# Both the help-text and the SPEC contain footnotes detailing
# aspects of the system.
#
####

####
# Help text.
####

# -------------------------------------------------------------------------------------- ## NOTES

'''
Usage:
    blort configure --env <host> --user <id> [--indent <n>] [--person <name>] [<general-options>]
    blort submit -c <> -r <> [--start-job] [--person <name> <age>] [<general-options>]
    blort get -j <> [--json [--indent <n>] | --b64 | --yaml] [<general-options>]
    blort drop <method> <n> [--print] [<general-options>]                                ## NOTE_815
    blort <fubb>... (--fast | --slow) [-a] [-b] [-x] [chat-options]
    blort <triple>{2,7} [-x] [-y] [chat-options]                                         ## NOTE_1240

    General options:
        --verbose         : Blah blah
        --log-file <path> : Blah blah
        --examples        : Blah blah
        --help            : Blah blah

Configure task:

    The configure task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Arguments:                                                                           ## NOTE_440
        --env <host>    : Blah blah
        --user <id>     : Blah blah
        --indent <n>    : Blah blah
        --person <name> : Blah blah

Submit task:

    The submit task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Arguments:
        -c <>                 : Blah blah
        -r <>                 : Blah blah
        --start-job           : Blah blah
        --person <name> <age> : Blah blah

Get task:

    The get task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Arguments:
        -j <>        : Blah blah
        --json       : Blah blah
        --indent <n> : Blah blah
        --b64        : Blah blah
        --yaml       : Blah blah

Drop task:

    The drop task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Methods:
        first  : Blah blah                                                               ## NOTE_820
        last   : Blah blah
        random : Blah blah

    Options:
        <n>     : Blah blah
        --print : Blah blah

Other usages:

    Fubb arguments:
        <fubb>    : Blah blah
        --fast    : Blah blah
        --slow    : Blah blah
        -a        : Blah blah
        -b        : Blah blah
        -x        : Blah blah fubbity

    Triple: repeated group of arguments:
        <a> : Blah blah
        <b> : Blah blah
        <c> : Blah blah
        -z  : Blah blah

    Triple: other options:
        -x : Blah blah wizzity
        -y : Blah blah

    Chat options:
        --hi  : Blah blah
        --bye : Blah blah
        --help
'''

####
# The parser-spec.
####

# -------------------------------------------------------------------------------------- ## NOTES

SPEC = '''

                                                                                         ## NOTE_50

    verbose! : [--verbose] [--log-file]                                                  ## NOTE_150

    general! : general-options=(verbose! [--examples] [--help])                          ## NOTE_170
    chat!    : chat-options=([--hi] [--bye] [--examples])

    configure! : --env --user [--indent] [--person]                                      ## NOTE_200
    submit!    : -c -r [--start-job] [--person]
    get!       : -j [--json [--indent] | --b64 | --yaml]
    drop!      : <method> <n> [--print]                                                  ## NOTE_805

    configure : <task=configure> configure! general!                                     ## NOTE_300
    submit    : <task=submit> submit! general!
    get       : <task=get> get! general!
    drop      : <task=drop> drop! general!

    fubb : <fubb>... (--fast | --slow) [-a] [-b] [-x] chat!                              ## NOTE_400
    wizz : triples=(<a> <b> <c> [-z]){2,7} [-x] [-y] chat!                               ## NOTE_1210

    General options :::                                                                  ## NOTE_420
        [--verbose]         : Blah blah
        [--log-file <path>] : Blah blah                                                  ## NOTE_150
        [--examples]        : Blah blah
        [--help]
                                                                                         ## NOTE_500

    ```# ==================================================```                           ## NOTE_600


    configure >> Configure task ::                                                       ## NOTE_720

        The configure task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

            --env <host>      : Blah blah                                                ## NOTE_440
            --user <id>       : Blah blah
            [--indent <n>]    : Blah blah
            [--person <name>] : Blah blah                                                ## NOTE_160


    ```# ==================================================```


    submit >> Submit task ::

        The submit task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

            -c <>                   : Blah blah
            -r <>                   : Blah blah
            [--start-job]           : Blah blah
            [--person <name> <age>] : Blah blah                                          ## NOTE_160


    ```# ==================================================```


    get >> Get task ::

        The get task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

            -j <>          : Blah blah
            [--json]       : Blah blah
            [--indent <n>] : Blah blah
            [--b64]        : Blah blah
            [--yaml]       : Blah blah


    ```# ==================================================```


    drop >> Drop task ::

        The drop task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        Methods :::                                                                      ## NOTE_810
            <method=first>  : Blah blah
            <method=last>   : Blah blah
            <method=random> : Blah blah

        Options :::
            <n>       : Blah blah
            [--print] : Blah blah


    ```# ==================================================```


    Other usages ::                                                                      ## NOTE_900

        Fubb arguments :::
            <fubb>...    : Blah blah
            --fast       : Blah blah
            --slow       : Blah blah
            [-a]         : Blah blah
            [-b]         : Blah blah
            fubb >> [-x] : Blah blah fubbity                                             ## NOTE_1000

        Triple: repeated group of arguments :::                                          ## NOTE_1220
            <a>  : Blah blah
            <b>  : Blah blah
            <c>  : Blah blah
            [-z] : Blah blah

        Triple: other options :::                                                        ## NOTE_1230
            wizz >> [-x] : Blah blah wizzity                                             ## NOTE_1000
            [-y]         : Blah blah

        Chat options :::
            [--hi]  : Blah blah
            [--bye] : Blah blah
            [--help]
                                                                                         ## NOTE_50
'''


####
# Parser configuration.
####

from optopus import Parser

def help_dispatch(opts):                                                                 ## NOTE_1300
    if opts.task:
        # If possible return the relevant <task> Section.
        p = opts('parser')
        return p.query_one(opts.task, kind = Section)
    else:
        # Default to the entire entire-text.
        return None

# Create Parser with ability to print task-sensitive help-text.
p = Parser(SPEC, help = help_dispatch)

# Achieves: singlar name (for help-text) and plural dest (for storage).
p.config('triples', name = 'triple')                                                     ## NOTE_1240

# Usage section will list options explicitly rather than
# summarizing them with the <options> placeholder
p.config_help_text(options_summary = False)

####
# Notes.
####

'''

NOTE_50
    - Blank lines at start and end of spec are removed.

NOTE_150
    - For brevity, variant can use opt-mentions.
    - Leaving the configuration to opt-specs.

NOTE_160
    - Some Opts have the same name but different configurations.
    - Examples: --person.

NOTE_170
    - Partials can use other partials.

NOTE_200
    - The main purpose of the four task partials is to make the
      corresponding variants more readable.

NOTE_300
    - Arg-variants, based on <task>.

NOTE_400
    - Variants with different grammars, illustrating a subcommand-style
      program without the usual rigidity.

NOTE_420
    - A heading (triple-colon), not a new section (double-colon).

NOTE_440
    - The spec has no heading before the opt-listing, so Optopus will generate
      a default one, in the unified-style: "Arguments".

NOTE_500
    - Unless block-quoted, multiple blank lines are condensed to a single
      blank line in the help-text.

NOTE_600
    - A block-comment.
    - Will not appear in help-text.
    - Used here for readability and illustration.

NOTE_720
    - A new section.
    - Includes a spec-scope (the >> marker) to clarify how to connect the
      opt-spec configurations to the correct Opts from the variant-specs
      (relevant when different Opts have the same name).
    - All opt-specs in the section will receive the scope.

NOTES on <method>:
    - NOTE_805:
        - In the variant-spec, an opt-mention is used: <method>.
    - NOTE_810:
        - In the relevant section, the opt-spec configures the Opt fully.
        - It is given choices: <method=first|last|random>.
        - And each choice is documented with help text.
    - NOTE_815:
        - In the usage-text, the Opt is displayed via its name: <method>.
        - If the user had unset the Opt.name in the API, it would have been
          displayed via its choices: <first|last|random>.
    - NOTE_820:
        - Those documented choices then appear in the generated help-text.
        - Each choice is diplayed as literal text (eg as 'first') not as a
          var-input in angle brackets (as '<first>')

NOTE_900
    - A section not scoped to a specific variant.
    - Sections are not required to map 1-to-1 with variants.

NOTE_1000
    - The -x Opts need different configurations.
    - So spec-scopes are applied directly to specific opt-specs rather than
      the whole section.

NOTES on <triple>:
    - NOTE_1210:
        - In the variant-spec a Group containing three positionals and one
          Option is defined and given a plural name: 'triples'.
    - NOTE_1220:
        - Later in the spec, the user provides a heading and an opt-listing to
          document the members of that Group.
    - NOTE_1230:
        - Then the user provides another heading and opt-listing to document
          the other options in the variant where <triple> resides.
    - NOTE_1240:
        - Via the API, the user renames the Group to singular: 'triple'.
        - That achieves a plural dest (triples) to hold the 2-through-7
          repetitions of the Group's Opts.
        - But the singular name will appear in the usage-text.
        - Because the Group has a complex quantifer, the end-user will be
          exposed to the curly-braces quantifer syntax -- an unavoidable
          outcome if one wants to support complex quantifers while accurately
          conveying the command-line grammar.

NOTE_1300
    - The program has a non-standard grammar:
        - Mostly is it a subcommand-style program: based on <task>.
        - But the last two variants are different.
    - So the user provides a custom help-dispatch function.

'''

