from opto_py import Parser
from opto_py.parser import SimpleSpec

def test_parser():
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

def test_parser():
    spec = '-n NAME --foo --bar B1 B2 <x> <y>'

    ss = SimpleSpec(spec)
    print()
    for t in ss.tokens:
        print(t)
    print()
