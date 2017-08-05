from opto_py.simple_spec_parser import (
    LONG_OPT,
    POS_OPT,
    SHORT_OPT,
    SIMPLE_SPEC_TOKENS,
    RegexLexer,
    SimpleSpecParser,
)

def test_simple_spec_parser():
    text = ' --foo FF GG  -x --blort -z Z1 Z2 <qq> <rr>  --debug  '
    lexer = RegexLexer(text, SIMPLE_SPEC_TOKENS)
    parser = SimpleSpecParser(lexer)
    opts = list(parser.parse())
    got = [(o.token_type, o.value, o.nargs) for o in opts]
    exp = [
        (LONG_OPT,  '--foo',   2),
        (SHORT_OPT, '-x',      0),
        (LONG_OPT,  '--blort', 0),
        (SHORT_OPT, '-z',      2),
        (POS_OPT,   '<qq>',    0),
        (POS_OPT,   '<rr>',    0),
        (LONG_OPT,  '--debug', 0),
    ]
    assert got == exp

