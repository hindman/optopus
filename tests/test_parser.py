import pytest

from optopus import (
    Parser,
)

def test_parse_noconfig_flag(tr):
    p = Parser()

    # Example 1: positionals and various options.
    args = 'frob -f AA --go BB CC --blort-maker_2 DD -27'.split()
    exp = {
        'f': True,
        'go': True,
        'blort_maker_2': True,
        'others': ['AA', 'BB', 'CC', 'DD', '-27'],
    }
    got = p.parse(args)
    assert got == exp

    # Example 1: check Result implementation.
    # TODO: move to separate test.
    exp_str = "Result(f=True, go=True, blort_maker_2=True, others=['AA', 'BB', 'CC', 'DD', '-27'])"
    assert str(got) == exp_str
    assert len(got) == len(exp)
    assert 'go' in got
    assert got['f'] == True
    for k, v in got:
        pass

    # Example 2: no arguments beyond [0] element.
    args = 'frob'.split()
    exp = {}
    got = p.parse(args)
    assert got == exp

    # Example 3: just positionals.
    args = 'frob A B C'.split()
    exp = {'others': ['A', 'B', 'C']}
    got = p.parse(args)
    assert got == exp

