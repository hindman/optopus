import pytest
from collections import OrderedDict

from optopus import (
    Parser,
    Result,
)

def test_parse_noconfig_flag(tr):
    p = Parser()

    # Example 1: positionals and various options.
    args = '-f AA --go BB CC --blort-maker_2 DD -27'.split()
    exp = {
        'f': True,
        'go': True,
        'blort_maker_2': True,
        'others': ['AA', 'BB', 'CC', 'DD', '-27'],
    }
    got = p.parse(args)
    assert dict(got) == exp

    # Example 2: no arguments beyond [0] element.
    args = ''.split()
    exp = {}
    got = p.parse(args)
    assert dict(got) == exp

    # Example 3: just positionals.
    args = 'A B C'.split()
    exp = {'others': ['A', 'B', 'C']}
    got = p.parse(args)
    assert dict(got) == exp

def test_result(tr):
    d = OrderedDict((
        ('f', True),
        ('go', True),
        ('others', ['A', 'B']),
    ))
    res = Result(d)
    # Iterable.
    assert tuple(res) == tuple(d.items())
    # Support for key access and membership tests.
    assert 'go' in res
    assert res['f'] is True
    # Support for str() and len().
    exp_str = "Result(f=True, go=True, others=['A', 'B'])"
    assert str(res) == exp_str
    assert repr(res) == exp_str
    assert len(res) == len(d)

