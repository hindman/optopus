import pytest
from six.moves import zip_longest
from textwrap import dedent

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

def test_parser_using_wildcards():
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

    # Scenarios exercised:
    # - Can pass nargs as keyword arg.
    # - Can also pass nargs implicitly via the option_spec.
    # - Can pass an Opt directly or via a dict.
    p = Parser(
        Opt('-n', nargs = 1),
        Opt('--foo'),
        dict(option_spec = '--bar B1 B2 B3 B4 B5'),
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

    long_help = 'The N of times to do the operation that needs to be done, either now or in the future'

    p = Parser(
        Opt('-n', nargs = 1, sections = ['foo', 'bar', 'blort'], text = long_help),
        Opt('--foo', sections = ['foo'], text = 'Some Foo behavior'),
        dict(option_spec = '--bar', nargs = 5),
        Opt('<x>', text = 'The X file'),
        Opt('<y>', text = 'The Y file'),
        Opt('--some_long_opt1'),
        Opt('--some_long_opt2'),
        Opt('--some_long_opt3'),
        Opt('--some_long_opt4'),
        Opt('--some_long_opt5'),
        Opt('--some_long_opt6'),
        Opt('--some_long_opt7'),
        formatter_config = FormatterConfig(
            Section('foo', 'Foo options'),
            Section(SectionName.POS, 'Positionals'),
            Section('bar', 'Bar options'),
            Section(SectionName.OPT, 'Some Options'),
            Section(SectionName.USAGE, 'Usage'),
        ),
    )

    exp = dedent('''
        Foo options:
          -n                   The N of times to do the operation that needs to be done,
                               either now or in the future
          --foo                Some Foo behavior

        Positional arguments:
          <x>                  The X file
          <y>                  The Y file

        Bar options:
          -n                   The N of times to do the operation that needs to be done,
                               either now or in the future

        Options:
          --bar
          --some_long_opt1
          --some_long_opt2
          --some_long_opt3
          --some_long_opt4
          --some_long_opt5
          --some_long_opt6
          --some_long_opt7

        Usage:
          cli -n --foo --bar <x> <y> --some_long_opt1 --some_long_opt2 --some_long_opt3
              --some_long_opt4 --some_long_opt5 --some_long_opt6 --some_long_opt7

        Blort options:
          -n                   The N of times to do the operation that needs to be done,
                               either now or in the future
    ''')

    got = p.help_text()
    assert exp == got

    exp = dedent('''
        Foo options:
          -n                   The N of times to do the operation that needs to be done,
                               either now or in the future
          --foo                Some Foo behavior

        Bar options:
          -n                   The N of times to do the operation that needs to be done,
                               either now or in the future
    ''')
    got = p.help_text('foo', 'bar')
    assert exp == got

    p = Parser(
        Opt('-n', nargs = 1, sections = ['foo', 'bar', 'blort'], text = 'N of times to do it'),
        Opt('--foo', sections = ['foo'], text = 'Some Foo behavior'),
        dict(option_spec = '--bar', nargs = 5),
        Opt('<x>', text = 'The X file'),
        Opt('<y>', text = 'The Y file'),
        program = 'frob',
    )

    exp = dedent('''
        Usage:
          frob -n --foo --bar <x> <y>

        Foo options:
          -n                   N of times to do it
          --foo                Some Foo behavior

        Bar options:
          -n                   N of times to do it

        Blort options:
          -n                   N of times to do it

        Options:
          --bar

        Positional arguments:
          <x>                  The X file
          <y>                  The Y file
    ''')
    got = p.help_text()
    assert exp == got

def test_formatter_config():
    fc = FormatterConfig()
    s = Section('fubbs', 'Fubb options')

def test_simple_spec_parsing():
    text = ' --foo FF GG  -x --blort -z Z1 Z2 <qq> <rr>  --debug  '
    parser = SimpleSpecParser(text)
    opts = list(parser.parse())
    got = [(o.opt_type, o.option_spec, o.nargs) for o in opts]
    exp = [
        (OptType.LONG,  '--foo FF GG', (2, 2)),
        (OptType.SHORT, '-x',          (0, 0)),
        (OptType.LONG,  '--blort',     (0, 0)),
        (OptType.SHORT, '-z Z1 Z2',    (2, 2)),
        (OptType.POS,   '<qq>',        (1, 1)),
        (OptType.POS,   '<rr>',        (1, 1)),
        (OptType.LONG,  '--debug',     (0, 0)),
    ]
    for g, e in zip_longest(got, exp):
        assert g == e

