
####
# The parser-spec.
####

'''

TODO:

    - Add notes to usage-text.
    - Add notes to Parser configuration
    - Recheck other notes.

Notes on SPEC:

    - NOTE_50
        - Blank lines at start and end of spec are removed.

    - NOTE_150
        - For brevity, the variants use opt-mentions.
        - Full configuration of each Opt occurs in the opt-specs.
        - Two specific examples: --log-file and --person.

    - NOTE_170
        - Partials can use other partials.

    - NOTE_200
        - Partial whose main purpose is to make the task-variants
          more readable in the spec.

    - NOTE_300
        - Arg-variants, based on <task>.

    - NOTE_400
        - Variants with different grammars, illustrating a subcommand-style
          program without the usual rigidity.

    - NOTE_420
        - Not a new section: still in the usage-section.
        - Just a single-line block-quote.

    - NOTE_500
        - Unless block-quoted, multiple blank lines are condensed to a single
          blank line in the help-text.

    - NOTE_520
        - Opt-specs do not require help text.

    - NOTE_600
        - A block-comment.
        - Will not appear in help-text.
        - Used here for readability and illustration.

    - NOTE_700
        - A new section.
        - Includes an spec-scope because some Opt names are repeated, and
          in some cases those Opts need different configuration.
        - All opt-specs in the section will receive the scope.

    - NOTE_800
        - Opt with both name and choices:
            - Name is used in generated help-text for variants and opt-specs.
            - <method> rather than <first|last|random>
        - Opt with a name and one choice (ie, arg-variant):
            - The choice is used, because it is a literal value.
            - This approach provides a mechanism (as shown) to document the
              choices themselves.

    - NOTE_900
        - A section not scoped to a specific variant.

    - NOTE_1000
        - The -x Opts need different configuration.
        - So spec-scopes are applied directly to specific opt-specs rather than
          the whole section.




    - Other notes:

        - In an argument-variant, the choice operates as a literal:
            - In usage-text a literal is prioritized over the name.
            - Hence the usage text uses 'configure', 'submit', and so forth,
              rather than '<task>'.
        - The user declared the names 'method' and 'triples' in the spec
          because they wanted the underlying dests.
            - The usage-text below assumes the user made API calls to unset the
              names to suppress them from usage-text.

            - If the user had not unset the Opt(method).name, the relevant
              usage-text snippets would have looked like this:

                blort drop <method> ...

                ...

                Where method:
                    first|last|random

'''

SPEC = '''
                                                                               ## NOTE_50

    general! : general-options=([--verbose] [--log-file])                      ## NOTE_150
    help!    : help-options=([--help] [--examples])

    other!   : other-options=(general! help!)                                  ## NOTE_170
    chat!    : chat-options=([--hi] [--bye] [--help])

    configure! : --env --user [--indent] [--person]                            ## NOTE_200
    submit!    : -c -r [--start-job] [--person]
    get!       : -j [--json [--indent] | --b64 | --yaml]
    drop!      : <method> <n> [--print]

    configure : <task=configure> configure! other!                             ## NOTE_300
    submit    : <task=submit> submit! other!
    get       : <task=get> get! other!
    drop      : <task=drop> drop! other!

    fubb : <fubb>... (--fast | --slow) [-a] [-b] [-x] chat!                    ## NOTE_400
    wizz : triples=(<a> <b> <c> [-z]){2,7} [-x] [-y] chat!

        ```Other options:```                                                   ## NOTE_420
            [--verbose]         : Blah blah
            [--log-file <path>] : Blah blah                                    ## NOTE_150
            [--help]                                                           ## NOTE_520
            [--examples] : Blah blah
                                                                               ## NOTE_500

    ```# ==================================================```                 ## NOTE_600


    configure >> Configure task ::                                             ## NOTE_700

        The configure task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        ```Options:```
            --env <host>      : Blah blah
            --user <id>       : Blah blah
            [--indent <n>]    : Blah blah
            [--person <name>] : Blah blah                                      ## NOTE_150


    ```# ==================================================```


    submit >> Submit task ::

        The submit task blah blah. Blah blah blah. Blah blah. Blah blah.
        Blah blah. Blah blah...

        ```Options:```
            -c <>                   : Blah blah
            -r <>                   : Blah blah
            [--start-job]           : Blah blah
            [--person <name> <age>] : Blah blah                                ## NOTE_150


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
# Configuring the Parser.
####

from optopus import Parser

p = Parser(SPEC)

p.config('method', name = None)
p.config('triples', name = 'triple')


####
# The generated help-text.
####

'''
Usage:
    blort configure --env <host> --user <id> [--indent <n>] [--person <name>] [other-options]
    blort submit -c <> -r <> [--start-job] [--person <name> <age>] [other-options]
    blort get -j <> [--json [--indent <n>] | --b64 | --yaml] [other-options]
    blort drop <method> <n> [--print] [other-options]
    blort <fubb>... (--fast | --slow) [-a] [-b] [-x] [chat-options]
    blort <triple>{2,7} [-x] [-y] [chat-options]

    Other options:
        [--verbose]         : Blah blah
        [--log-file <path>] : Blah blah
        [--help]            : Blah blah
        [--examples]        : Blah blah

Configure task:

    The configure task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Options:
        --env <host>      : Blah blah
        --user <id>       : Blah blah
        [--indent <n>]    : Blah blah
        [--person <name>] : Blah blah

Submit task:

    The submit task blah blah. Blah blah blah. Blah blah. Blah blah.
    Blah blah. Blah blah...

    Options:
        -c <>                   : Blah blah
        -r <>                   : Blah blah
        [--start-job]           : Blah blah
        [--person <name> <age>] : Blah blah

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
        first  : Blah blah
        last   : Blah blah
        random : Blah blah

    Options:
        <n>       : Blah blah
        [--print] : Blah blah

Other usages:

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

