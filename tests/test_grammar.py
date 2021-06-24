
from optopus.grammar import (
    SpecParser,
    TokDefs,
)

def test_readme_examples(tr):
    # A minimal test to make sure we can parse the examples
    # from the README to completion.
    TESTS = (
        # README examples:
        (14, '''pgrep [-i] [-v] <rgx> <path>'''),
        (27, '''pgrep ::
            <rgx> : Python regular expression
            [<path>...] : Path(s) to input
            [-i --ignore-case] : Ignore case
            [-v --invert-match] : Select non-matching lines'''),
        (180, '''wrangle
            <task=grep>   [-i] [-v] [-m] [-C]
                          [--color <red|green|blue>]
                          <rgx> [<path>...]
            <task=sub>    [-i] [-n] <rgx> <rep> [<path>...]
            <task=search> [-i] [-g] [-d | -p] <rgx> [<path>...]

            ::

            <task>             : Task to perform
            <task=grep>        : Emit lines matching pattern
            <task=sub>         : Search for pattern and replace
            <task=search>      : Emit text matching pattern
            <rgx>              : Python regular expression
            <path>             : Path(s) to input
            <rep>              : Replacement text
            -i --ignore-case   : Ignore case
            -v --invert-match  : Select non-matching lines
            -m --max-count <n> : Stop searching after N matches
            -C --context <n>   : Print N lines of before/after context
            --color <>         : Highlight matching text
            -n --nsubs <n>     : N of substitutions
            -g --group <n>     : Emit just capture group N [0 for all]
            -d --delim <s>     : Delimeter for capture groups [tab]
            -p --para          : Emit capture groups one-per-line, paragraph-style'''
         ),
        # OTHER.
        (0, '''pgrep
               [-i] [-v]
                    <rgx> <path>
               [--foo] <blort>'''),
        (27, '''pgrep ::
            <rgx> : Python
                    regular
                    expression
            [<path>...] : Path(s) to
                          input
            [-i --ignore-case] : Ignore case
            [-v 
                  --invert-match] : Select non-matching
                                    lines'''),
        (0, '''pgrep
               [-i]? [-v]...
                    <rgx> <path>{1,7}?
               [--foo] <blort>?

Positionals needed ::

```
Positionals blorty blorty blort blort
foo bar fubb.
```

    <rgx> : Regular
            expression
    <path> : Path to
             the
             file

Options::

```
Positionals blorty blorty blort blort
foo bar fubb.
```

    -i  : Ignore case
          during search
    -v  : Ivert: emit non-matched
          lines

         '''),
    )

    for exp, text in TESTS:
        sp = SpecParser(text)
        g = sp.parse()

        continue

        tr.dump('')
        print('# TEXT')
        print(sp.text)
        print('\n# GRAMMAR')
        for line in g.pp(g):
            print(line)

