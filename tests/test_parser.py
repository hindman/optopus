from opto_py import Parser
from opto_py.parser import SimpleSpec

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
    # Setup.
    spec = '-n NAME --foo --bar B1 B2 <x> <y>'
    ss = SimpleSpec(spec)
    # Expected.
    exp_tokens = [
        ('short_opt', '-n', 0),
        ('opt_arg', 'NAME', 1),
        ('long_opt', '--foo', 2),
        ('long_opt', '--bar', 3),
        ('opt_arg', 'B1', 4),
        ('opt_arg', 'B2', 5),
        ('pos_arg', 'x', 6),
        ('pos_arg', 'y', 7),
    ]
    exp_opts = [
        ('-n', 'short', 1),
        ('--foo', 'long', 0),
        ('--bar', 'long', 2),
        ('x', 'positional', 1),
        ('y', 'positional', 1),
    ]
    # Actual.
    got_tokens = ss.tokens
    got_opts = [
        (o.option, o.opt_type, o.nargs)
        for o in ss.opts
    ]
    # Assert.
    assert got_tokens == exp_tokens
    assert got_opts == exp_opts

