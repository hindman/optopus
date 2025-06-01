
import io
import pytest

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

from short_con import cons, constants

from argle.spec_parser import SpecParser

# @pytest.mark.skip

####
# A StringIO you can print directly, without fuss.
####

class Sio(io.StringIO):

    def __str__(self):
        return self.getvalue()

####
# Tests to parse each ESpec into a grammar.
#
# Current status:
#   - just exercises code
#   - no assertions
#   - current object returned by parse() is a SpecAST, not Grammar
####

def test_ex_pgrep_1(tr):
    esp = ESpecs.pgrep_1
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_pgrep_2(tr):
    esp = ESpecs.pgrep_2
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_pgrep_3(tr):
    esp = ESpecs.pgrep_3
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_wrangle(tr):
    esp = ESpecs.wrangle
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_line_wrap_1(tr):
    esp = ESpecs.line_wrap_1
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_line_wrap_2(tr):
    esp = ESpecs.line_wrap_2
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_line_wrap_3(tr):
    esp = ESpecs.line_wrap_3
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_blort(tr):
    esp = ESpecs.blort
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_naval_fate(tr):
    esp = ESpecs.naval_fate
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_repo(tr):
    esp = ESpecs.repo
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_neck_diagram(tr):
    esp = ESpecs.neck_diagram
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

def test_ex_nab(tr):
    esp = ESpecs.nab
    sp = SpecParser(esp.spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp)

####
# Basline tests to reveal errors as the code spec-parsing code evolves.
#
# For each ESpec, parses the spec into a grammar, with debug=True.
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

        # Skip inactive test cases.
        if not esp.active:
            continue

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
        assert ok, f'vimdiff {epath} {gpath}'

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
    active: bool
    spec: str
    spec_path: Path
    got_path: Path
    exp_path: Path

    @classmethod
    def from_key(cls, key, active):
        fname = key.replace('_', '-') + '.txt'
        data_path = Path('tests') / 'data'
        spec_path = data_path / 'specs' / fname
        got_path  = data_path / 'got' / fname
        exp_path  = data_path / 'exp' / fname
        return cls(
            key = key,
            active = active,
            spec = read_file(spec_path),
            spec_path = spec_path,
            got_path = got_path,
            exp_path = exp_path,
        )

ESpecs = constants({
    key : ESpec.from_key(key, active)
    for active, key in [
        (True, 'pgrep_1'),
        (True, 'pgrep_2'),
        (True, 'pgrep_3'),
        (True, 'wrangle'),
        (True, 'line_wrap_1'),
        (True, 'line_wrap_2'),
        (True, 'line_wrap_3'),
        (True, 'blort'),
        (True, 'naval_fate'),
        (True, 'repo'),
        (True, 'neck_diagram'),
        (True, 'nab'),
    ]
})

