
####
#
# This demo is designed to exercise most features of the spec-syntax.
#
# The example is not intended to a realistic or sane.
#
# Start at the end: the generated help-text.
#
# Both the help-text and the SPEC contain footnotes detailing
# aspects of the system.
#
####

####
# Help text.
####

'''
Usage:
    blort configure --env <host> --user <id> [--indent <n>] [--person <name>] [<general-options>]
    blort submit -c <> -r <> [--start-job] [--person <name> <age>] [<general-options>]
    blort get -j <> [--json [--indent <n>] | --b64 | --yaml] [<general-options>]
    blort drop <method> <n> [--print] [<general-options>]                      ## NOTE_800
    blort <fubb>... (--fast | --slow) [-a] [-b] [-x] [chat-options]
    blort <triple>{2,7} [-x] [-y] [chat-options]

    General options:
        [--verbose]         : Blah blah
        [--log-file <path>] : Blah blah                                        ## NOTE_150
        [--examples]        : Blah blah
        [--help]            : Blah blah

Configure task:

    The configure task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Options:
        --env <host>      : Blah blah
        --user <id>       : Blah blah
        [--indent <n>]    : Blah blah
        [--person <name>] : Blah blah                                          ## NOTE_160

Submit task:

    The submit task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Options:
        -c <>                   : Blah blah
        -r <>                   : Blah blah
        [--start-job]           : Blah blah
        [--person <name> <age>] : Blah blah                                    ## NOTE_160

Get task:

    The get task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Options:
        -j <>          : Blah blah
        [--json]       : Blah blah
        [--indent <n>] : Blah blah
        [--b64]        : Blah blah
        [--yaml]       : Blah blah

Drop task:

    The drop task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Methods:
        first  : Blah blah                                                     ## NOTE_800
        last   : Blah blah
        random : Blah blah

    Options:
        <n>       : Blah blah
        [--print] : Blah blah

Other usages:                                                                  ## NOTE_1100

    Fubb arguments and options:
        <fubb>... : Blah blah
        --fast    : Blah blah
        --slow    : Blah blah
        [-a]      : Blah blah
        [-b]      : Blah blah
        [-x]      : Blah blah fubbity

    Wizz: triple: arguments and options:
        <a>  : Blah blah
        <b>  : Blah blah
        <c>  : Blah blah
        [-z] : Blah blah

    Wizz: other options:
        [-x] : Blah blah wizzity
        [-y] : Blah blah

    Chat options:
        [--hi]  : Blah blah
        [--bye] : Blah blah
        [--help]
'''

####
# The parser-spec.
####

SPEC = '''

                                                                               ## NOTE_50

    verbose! : [--verbose] [--log-file]                                        ## NOTE_150

    general! : general-options=(verbose! [--examples] [--help])                ## NOTE_170
    chat!    : chat-options=([--hi] [--bye] [--examples])

    configure! : --env --user [--indent] [--person]                            ## NOTE_200
    submit!    : -c -r [--start-job] [--person]
    get!       : -j [--json [--indent] | --b64 | --yaml]
    drop!      : <method> <n> [--print]                                        ## NOTE_800

    configure : <task=configure> configure! general!                           ## NOTE_300
    submit    : <task=submit> submit! general!
    get       : <task=get> get! general!
    drop      : <task=drop> drop! general!

    fubb : <fubb>... (--fast | --slow) [-a] [-b] [-x] chat!                    ## NOTE_400
    wizz : triples=(<a> <b> <c> [-z]){2,7} [-x] [-y] chat!

        ```Other options:```                                                   ## NOTE_420
            [--verbose]         : Blah blah
            [--log-file <path>] : Blah blah                                    ## NOTE_150
            [--examples] : Blah blah
                                                                               ## NOTE_500

    ```# ==================================================```                 ## NOTE_600


    configure >> Configure task ::                                             ## NOTE_720

        The configure task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        ```Options:```
            --env <host>      : Blah blah
            --user <id>       : Blah blah
            [--indent <n>]    : Blah blah
            [--person <name>] : Blah blah                                      ## NOTE_160


    ```# ==================================================```


    submit >> Submit task ::

        The submit task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        ```Options:```
            -c <>                   : Blah blah
            -r <>                   : Blah blah
            [--start-job]           : Blah blah
            [--person <name> <age>] : Blah blah                                ## NOTE_160


    ```# ==================================================```


    get >> Get task ::

        The get task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        ```Options:```
            -j <>          : Blah blah
            [--json]       : Blah blah
            [--indent <n>] : Blah blah
            [--b64]        : Blah blah
            [--yaml]       : Blah blah


    ```# ==================================================```


    drop >> Drop task ::

        The drop task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        ```Methods:```                                                         ## NOTE_800
            <method=first>  : Blah blah
            <method=last>   : Blah blah
            <method=random> : Blah blah

        ```Options:```
            <n>                        : Blah blah
            [--print]                  : Blah blah


    ```# ==================================================```


    Other usages ::                                                            ## NOTE_900

        ```Fubb arguments and options:```
            <fubb>...    : Blah blah
            --fast       : Blah blah
            --slow       : Blah blah
            [-a]         : Blah blah
            [-b]         : Blah blah
            fubb >> [-x] : Blah blah fubbity                                   ## NOTE_1000

        ```Wizz: triple: arguments and options:```
            <a>  : Blah blah
            <b>  : Blah blah
            <c>  : Blah blah
            [-z] : Blah blah

        ```Wizz: other options:```
            wizz >> [-x] : Blah blah wizzity                                   ## NOTE_1000
            [-y]         : Blah blah

        ```Chat options:```
            [--hi]              : Blah blah
            [--bye]             : Blah blah
            [--help]
                                                                               ## NOTE_50
'''


####
# Parser configuration.
####

from optopus import Parser

def help_dispatch(opts):
    if opts.task:
        # If possible return the relevant <task> Section.
        p = opts.ctx.parser
        return p.query_one(opts.task, kind = Section)
    else:
        # Default to the entire entire-text.
        return None

# Create Parser with ability to print task-sensitive help-text.
p = Parser(SPEC, help = help_dispatch)

# Achieves: singlar name (for help-text) and plural dest (for storage).
p.config('triples', name = 'triple')

####
# Notes.
####

'''

NOTE_50
    - Blank lines at start and end of spec are removed.

NOTE_150
    - For brevity, the variants use opt-mentions.
    - Full configuration of each Opt occurs in the opt-specs.
    - Examples: --log-file.

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
    - Not a new section: still in the usage-section.
    - Just a single-line block-quote.

NOTE_500
    - Unless block-quoted, multiple blank lines are condensed to a single
      blank line in the help-text.

NOTE_600
    - A block-comment.
    - Will not appear in help-text.
    - Used here for readability and illustration.

NOTE_720
    - A new section.
    - Includes a spec-scope to clarify how to connect the opt-spec
      configurations to the correct Opts from the variant-specs (relevant
      when different Opts have the same name).
    - All opt-specs in the section will receive the scope.

NOTE_800
    - Opt with both name and choices:
        - Name is used in generated help-text for variants and opt-specs.
        - <method> rather than <first|last|random>
    - Opt with a name and one choice (ie, arg-variant):
        - The choice is used, because it is a literal value.
        - This approach provides a mechanism (as shown) to document the
          choices themselves.
        - Examples in the generated help-text:
            - The documentation for the <method> choices.
            - The <step> variants.

NOTE_900
    - A section not scoped to a specific variant.

NOTE_1000
    - The -x Opts need different configuration.
    - So spec-scopes are applied directly to specific opt-specs rather than
      the whole section.

NOTE_1100
    - Sections are not required to map 1-to-1 with variants.

'''

