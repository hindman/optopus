
import io
import pytest

from pathlib import Path
from textwrap import dedent

from short_con import cons, constants

from argle.grammar import (
    SpecParser,
)

# @pytest.mark.skip

####
# A StringIO you can print directly, without fuss.
####

class Sio(io.StringIO):

    def __str__(self):
        return self.getvalue()

####
# Tests to parse each ex00 into a grammar.
#
# Current status:
#   - just exercises code
#   - no assertions
#   - current object returned by parse() is a SpecAST, not Grammar
####

def test_ex01(tr):
    sp = SpecParser(SPECS.ex01, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex02(tr):
    sp = SpecParser(SPECS.ex02, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex03(tr):
    sp = SpecParser(SPECS.ex03, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex04(tr):
    sp = SpecParser(SPECS.ex04, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex05(tr):
    sp = SpecParser(SPECS.ex05, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex06(tr):
    sp = SpecParser(SPECS.ex06, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

@pytest.mark.skip
def test_ex07(tr):
    sp = SpecParser(SPECS.ex07, debug = True)
    g = sp.parse()
    # tr.dump(g.pp)

####
# Basline tests to reveal errors as the code spec-parsing code evolves.
#
# For each ex00, parses the spec into a grammar, with debug=True.
# Captures the debug output and the pp-style text representing
# the grammar and writes them to a text file. That text file
# becomes a baseline to detect regressions for subsequent runs
# of the test, using a simple equality assertion.
#
# Current status:
#   - the object return by parse() is a SpecAST, not Grammar.
####

def test_against_baselines(tr):
    for k, spec in SPECS:

        # TODO: remove
        if k == 'ex07':
            continue

        # Parse the spec into a grammar, with debug=True.
        sp = SpecParser(spec, debug = Sio())
        g = sp.parse()
        parser_debug = str(sp.debug)

        # Assemble the spec, debug output, and pretty-printable
        # grammar into a block of text.
        got_text = '\n'.join([
            '\n# SPEC',
            spec,
            '\n# PARSER_DEBUG',
            parser_debug,
            '\n# GRAMMAR',
            g.pp,
            '',
        ])

        # Write the text we got.
        paths = ex_paths(k)
        write_file(paths.got, got_text)

        # Read the text we expect, if it exists.
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

def ex_paths(k):
    f = f'{k}.txt'
    return cons(
        spec = Path('tests') / 'data' / 'specs' / f,
        got  = Path('tests') / 'data' / 'got' / f,
        exp  = Path('tests') / 'data' / 'exp' / f,
    )

def read_spec(k):
    return read_file(ex_paths(k).spec)

def read_file(path):
    with open(path) as fh:
        return fh.read()

def write_file(path, text):
    with open(path, 'w') as fh:
        fh.write(text)

####
# Example specs.
####

SPECS = constants({
    k : read_spec(k)
    for k in [
        'ex01',
        'ex02',
        'ex03',
        'ex04',
        'ex05',
        'ex06',
        'ex07',
    ]
})

