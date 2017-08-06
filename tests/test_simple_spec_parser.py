from opto_py.simple_spec_parser import SimpleSpecParser
from opto_py.opt import Opt
from opto_py.enums import OptType

def test_simple_spec_parser():
    text = ' --foo FF GG  -x --blort -z Z1 Z2 <qq> <rr>  --debug  '
    parser = SimpleSpecParser(text)
    opts = list(parser.parse())
    got = [(o.opt_type, o.option_spec, o.nargs) for o in opts]
    exp = [
        (OptType.LONG,  '--foo',   2),
        (OptType.SHORT, '-x',      0),
        (OptType.LONG,  '--blort', 0),
        (OptType.SHORT, '-z',      2),
        (OptType.POS,   '<qq>',    0),
        (OptType.POS,   '<rr>',    0),
        (OptType.LONG,  '--debug', 0),
    ]
    assert got == exp

