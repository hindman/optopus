
import io
import pytest

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

from short_con import cons, constants

from argle.grammar import (
    SpecParser,
    Rgxs,
    TokDefs,
    Scope,
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
    esp = ESpecs.ex01
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex02(tr):
    esp = ESpecs.ex02
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex03(tr):
    esp = ESpecs.ex03
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex04(tr):
    esp = ESpecs.ex04
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex05(tr):
    esp = ESpecs.ex05
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex06(tr):
    esp = ESpecs.ex06
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex07(tr):
    esp = ESpecs.ex07
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex08(tr):
    esp = ESpecs.ex08
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex09(tr):
    esp = ESpecs.ex09
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex10(tr):
    esp = ESpecs.ex10
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex11(tr):
    esp = ESpecs.ex11
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex12(tr):
    esp = ESpecs.ex12
    sp = SpecParser(esp.spec, debug = False)
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
    for k, esp in ESpecs:
        # Parse the spec into a grammar, with debug=True.
        spec = esp.spec
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
        gpath = esp.got_path
        epath = esp.exp_path
        write_file(gpath, got_text)

        # Read the text we expect, if it exists.
        # Otherwise, write it for next time.
        if epath.is_file():
            exp_text = read_file(epath)
        else:
            write_file(epath, got_text)
            exp_text = got_text

        # Assert.
        ok = got_text == exp_text
        assert ok, f'diff {epath} {gpath}'

####
# Helpers.
####

def read_file(path):
    with open(path) as fh:
        return fh.read()

def write_file(path, text):
    with open(path, 'w') as fh:
        fh.write(text)

####
# Example specs.
####

@dataclass
class ESpec:
    key: str
    label: str
    spec: str
    spec_path: Path
    got_path: Path
    exp_path: Path

    @classmethod
    def from_key(cls, key, label):
        fname = f'{key}.txt'
        data_path = Path('tests') / 'data'
        spec_path = data_path / 'specs' / fname
        got_path  = data_path / 'got' / fname
        exp_path  = data_path / 'exp' / fname
        return cls(
            key = key,
            label = label,
            spec = read_file(spec_path),
            spec_path = spec_path,
            got_path = got_path,
            exp_path = exp_path,
        )

ESpecLabels = cons(
    ex01 = 'pgrep-1',
    ex02 = 'pgrep-2',
    ex12 = 'pgrep-3',
    ex03 = 'wrangle',
    ex04 = 'line-wrap-1',
    ex05 = 'line-wrap-2',
    ex06 = 'line-wrap-3',
    ex07 = 'blort',
    ex08 = 'naval-fate',
    ex09 = 'repo',
    ex10 = 'neck-diagram',
    ex11 = 'nab',
)

ESpecs = constants({
    key : ESpec.from_key(key, label)
    for key, label in ESpecLabels
})

