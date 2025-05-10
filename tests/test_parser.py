import pytest
from collections import OrderedDict

from argle import (
    Parser,
    Result,
)

def test_parse_noconfig_flag(tr):
    p = Parser()

    # Simple use case.
    args = 'rgx path -i -v'.split()
    exp = {
        'i': True,
        'v': True,
        'positionals': ['rgx', 'path'],
    }
    got = p.parse(args)
    assert dict(got) == exp

    # More elaborate inputs.
    args = 'AA BB CC -27 -f F --go G1 G2 --blort-maker_2 -- DD EE'.split()
    exp = {
        'f': 'F',
        'go': ['G1', 'G2'],
        'blort_maker_2': True,
        'positionals': ['AA', 'BB', 'CC', '-27', 'DD', 'EE'],
    }
    got = p.parse(args)
    assert dict(got) == exp

    # No arguments.
    args = []
    exp = {}
    got = p.parse(args)
    assert dict(got) == exp

    # Just positionals.
    args = 'A B C'.split()
    exp = {'positionals': args}
    got = p.parse(args)
    assert dict(got) == exp

def test_result(tr):
    d = OrderedDict((
        ('f', True),
        ('go', True),
        ('positionals', ['A', 'B']),
    ))
    res = Result(d)
    # Iterable.
    assert tuple(res) == tuple(d.items())
    # Support for key access and membership tests.
    assert 'go' in res
    assert res['f'] is True
    # Support for str() and len().
    exp_str = "Result(f=True, go=True, positionals=['A', 'B'])"
    assert str(res) == exp_str
    assert repr(res) == exp_str
    assert len(res) == len(d)

