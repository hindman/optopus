import pytest

from opto_py import Parser, OptoPyError, Opt

from opto_py.simple_spec_parser import SimpleSpecParser

def test_zero_config_parser():
    args = [
        'tigers',
        'Bees',
        '--spy',
        '--end_run',
        '12.34',
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
    popts = p.parse(args)
    got = dict(popts)
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

def test_basic_api_usage():

    p = Parser(
        Opt('-n', nargs = 1),
        Opt('--foo'),
        dict(option_spec = '--bar', nargs = 5),
        Opt('<x>'),
        Opt('<y>'),
    )

    # Valid.
    args = [
        '-n', 'Spock',
        '--foo',
        '--bar', '11', '12', '13', '14', '15',
        'phasers',
        'beam',
    ]
    exp = dict(
        n = 'Spock',
        foo = True,
        bar = ['11', '12', '13', '14', '15'],
        x = 'phasers',
        y = 'beam',
    )
    popts = p.parse(args)
    got = dict(popts)
    assert got == exp

    # Invalid.
    args = [
        'phasers',
        'beam',
        '-n', 'Spock',
        '--foo',
        '--bar', '11', '12',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    msg = str(einfo.value)
    assert 'expected N of arguments' in msg
    assert '--bar' in msg

    # Invalid.
    args = [
        'phasers',
        '-n', 'Spock',
        '--foo',
        '--bar', '11', '12', '13', '14', '15',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    msg = str(einfo.value)
    assert 'expected N of arguments' in msg
    assert '<y>' in msg

    # Invalid.
    args = [
        'phasers',
        'beam',
        '--foo',
        '--bar', '11', '12', '13', '14', '15',
        '-n',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    msg = str(einfo.value)
    assert 'expected N of arguments' in msg
    assert '-n' in msg

