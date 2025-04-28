
import io

from optopus.grammar import (
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

EX01 = '''
pgrep [-i] [-v] <rgx> <path>
'''

EX02 = '''
pgrep ::

<rgx> : Python regular expression
[<path>...] : Path(s) to input
[-i --ignore-case] : Ignore case
[-v --invert-match] : Select non-matching lines
'''

EX03 = '''
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

EX04 = '''
pgrep
[-i] [-v]
    <rgx> <path>
[--foo] <blort>
'''

EX05 = '''
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

EX06 = '''
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

def dump_grammar(tr, sp, g):
    lines = [
        '# TEXT',
        sp.text,
        '',
        '# GRAMMAR',
        *Grammar.pp(g)
    ]
    msg = '\n'.join(lines)
    tr.dump(msg)

def test_readme_ex1(tr):
    spec = EX01.strip() + '{1,3}'
    sp = SpecParser(spec, debug = False)
    g = sp.parse()
    # dump_grammar(tr, sp, g)

def test_readme_examples(tr):
    TESTS = (
        (EX01, False, 0),
        (EX02, False, 0),
        (EX03, False, 0),
        (EX04, False, 0),
        (EX05, False, 0),
        (EX06, False, 0),
    )

    for text, debug, exp in TESTS:
        fh = None
        sp = SpecParser(text, debug = fh)
        g = sp.parse()

        # dump_grammar(tr, sp, g)
        # tr.dump(sp.debug_fh)

