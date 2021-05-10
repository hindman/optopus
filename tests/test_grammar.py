
from optopus.grammar import (
    RegexLexer,
    toktypes,
)

def test_readme_examples(tr):
    # A minimal test to make sure we can lex the examples
    # from the README to completion.
    TESTS = (
        (14, toktypes.variant, 'pgrep [-i] [-v] <rgx> <path>'),
        (27, toktypes.opt_help, '''pgrep ::
            <rgx> : Python regular expression
            [<path>...] : Path(s) to input
            [-i --ignore-case] : Ignore case
            [-v --invert-match] : Select non-matching lines'''),
        (180, toktypes.opt_help, '''wrangle
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
    )
    for exp, tts, text in TESTS:
        lex = RegexLexer(text, tts)
        toks = []
        while not lex.end:
            tok = lex.get_next_token()
            toks.append(tok)
        assert toks
        assert toks[-1].kind == 'eof'
        assert len(toks) == exp

