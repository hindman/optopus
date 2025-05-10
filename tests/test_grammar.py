
################################
# OLD FILE -- DO NOT EDIT
################################

import io
from pathlib import Path

from short_con import cons
from argle.grammar import (
    SpecParser,
    TokDefs,
    Grammar,
)

####
# A StringIO you can print directly, without fuss.
####

class Sio(io.StringIO):

    def __str__(self):
        return self.getvalue()

####
# Example specs.
####

SPECS = {}

SPECS['ex01'] = '''
pgrep [-i] [-v] <rgx> <path>
'''

SPECS['ex02'] = '''
pgrep ::

<rgx> : Python regular expression
[<path>...] : Path(s) to input
[-i --ignore-case] : Ignore case
[-v --invert-match] : Select non-matching lines
'''

SPECS['ex03'] = '''
wrangle

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
-p --para          : Emit capture groups one-per-line, paragraph-style
'''

SPECS['ex04'] = '''
pgrep
[-i] [-v]
    <rgx> <path>
[--foo] <blort>
'''

SPECS['ex05'] = '''
pgrep ::
<rgx> : Python
        regular
        expression
[<path>...] : Path(s) to
              input
[-i --ignore-case] : Ignore case
[-v 
      --invert-match] : Select non-matching
                        lines
'''

SPECS['ex06'] = '''
pgrep
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
'''

def test_ex1(tr):
    spec = SPECS['ex01'].strip() + '{1,3}'
    sp = SpecParser(spec, debug = False)
    g = sp.parse()

def test_examples(tr):

    for exkey, spec in SPECS.items():
        fh = None
        sp = SpecParser(spec, debug = Sio())
        grammar = sp.parse()
        parser_debug = str(sp.debug_fh)

        got_text = '\n'.join([
            '\n# SPEC',
            spec,
            '\n# PARSER_DEBUG',
            parser_debug,
            '\n# GRAMMAR',
            grammar.pp,
            '',
        ])

        paths = example_paths(exkey)

        # Write the text we got.
        write_file(paths.got, got_text)

        # Read the text we expect, if possible.
        # Otherwise, write it for next time.
        if paths.exp.is_file():
            exp_text = read_file(paths.exp)
        else:
            write_file(paths.exp, got_text)
            exp_text = got_text

        # Assert.
        ok = got_text == exp_text
        assert ok, f'diff {paths.exp} {paths.got}'

####
# Helpers.
####

def example_paths(exkey):
    return cons(
        got = Path('tests') / 'ex_diff' / 'got' / exkey,
        exp = Path('tests') / 'ex_diff' / 'exp' / exkey,
    )

def read_file(path):
    with open(path) as fh:
        return fh.read()

def write_file(path, text):
    with open(path, 'w') as fh:
        fh.write(text)

