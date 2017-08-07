from opto_py import Parser

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

