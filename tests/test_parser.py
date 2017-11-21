import pytest
from six.moves import zip_longest

from opto_py import (
    FormatterConfig,
    Opt,
    OptoPyError,
    Parser,
    Section,
    SectionName,
)
from opto_py.parser import (
    OptType,
    SimpleSpecParser,
)

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

    # Invalid.
    args = [
        'phasers',
        'beam',
        '--foo',
        '--foo',
        '--bar', '11', '12', '13', '14', '15',
        '-n',
    ]
    with pytest.raises(OptoPyError) as einfo:
        popts = p.parse(args)
    msg = str(einfo.value)
    assert 'Found repeated option' in msg
    assert '--foo' in msg

def test_basic_help_text():

    p = Parser(
        Opt('-n', nargs = 1),
        Opt('--foo'),
        dict(option_spec = '--bar', nargs = 5),
        Opt('<x>'),
        Opt('<y>'),
        formatter_config = FormatterConfig(
            Section('foo', 'Foo options'),
            Section(SectionName.POS, 'Positionals'),
            Section('bar', 'Bar options'),
            Section(SectionName.OPT, 'Some Options'),
            Section(SectionName.USAGE, 'USAGE'),
        ),
    )

    exp = 'Usage: blort\n'
    got = p.help_text()
    assert exp == got

    return
    print('\n-----------------')
    print(got)
    print('-----------------')

def test_formatter_config():
    fc = FormatterConfig()
    s = Section('fubbs', 'Fubb options')

def test_simple_spec_parser():
    text = ' --foo FF GG  -x --blort -z Z1 Z2 <qq> <rr>  --debug  '
    parser = SimpleSpecParser(text)
    opts = list(parser.parse())
    got = [(o.opt_type, o.option_spec, o.nargs) for o in opts]
    exp = [
        (OptType.LONG,  '--foo',   (2, 2)),
        (OptType.SHORT, '-x',      (0, 0)),
        (OptType.LONG,  '--blort', (0, 0)),
        (OptType.SHORT, '-z',      (2, 2)),
        (OptType.POS,   '<qq>',    (1, 1)),
        (OptType.POS,   '<rr>',    (1, 1)),
        (OptType.LONG,  '--debug', (0, 0)),
    ]
    for g, e in zip_longest(got, exp):
        assert g == e

