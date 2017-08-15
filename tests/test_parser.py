import pytest

from opto_py import Parser
from opto_py import OptoPyError

def test_zero_config_parser():
    args = [
        'tigers',
        'Bees',
        '12.34',
        '--spy',
        '--end-run',
        '--fbi-and-cia',
        'x99',
    ]
    exp = {
        'spy': True,
        'end_run': True,
        'fbi_and_cia': True,
        'positionals': ['tigers', 'Bees', '12.34', 'x99'],
    }
    p = Parser()
    got = p.parse(args)
    assert got == exp

def test_simple_spec_parser():

    # Valid.
    spec = '-n NAME --foo --bar B1 B2 <x> <y>'
    p = Parser(simple_spec = spec)
    args = [
        '-n', 'Spock',
        '--foo',
        '--bar', '12', '13',
        'phasers',
        'beam',
    ]
    exp = dict(
        n = 'Spock',
        foo = True,
        bar = ['12', '13'],
        x = 'phasers',
        y = 'beam',
    )
    popts = p.parse(args)
    got = dict(popts)
    assert got == exp

    # Valid.
    spec = '<x> -a A <y>'
    p = Parser(simple_spec = spec)
    args = [
        'phasers',
        'beam',
        '-a', 'hi bye',
    ]
    exp = dict(
        x = 'phasers',
        y = 'beam',
        a = 'hi bye',
    )
    popts = p.parse(args)
    got = dict(popts)
    assert got == exp

    # Invalid.
    spec = '<x> -a A <y>'
    p = Parser(simple_spec = spec)
    args = [
        'phasers',
        'beam',
        'foo',
        '-a', 'hi bye',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    assert 'unexpected positional' in str(einfo.value)

    # Invalid.
    spec = '-n NAME --foo --bar B1 B2 <x> <y>'
    p = Parser(simple_spec = spec)
    args = [
        '-n',
        '--foo',
        '--bar', '12', '13',
        'phasers',
        'beam',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    assert 'expected option-argument' in str(einfo.value)

    # Invalid.
    spec = '-n NAME --foo --bar B1 B2 <x> <y>'
    p = Parser(simple_spec = spec)
    args = [
        '-n', 'Spock',
        '--foo',
        '--bar', '12', '13',
        'phasers',
        'beam',
        '--fuzz',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    assert 'unexpected option' in str(einfo.value)

