import re

from short_con import constants

MODES = constants(
    'ParsingModes',
    (
        # Modes for a configured Parser: can be combined.
        'normal',
        'unknown_ok',
        'unconverted_ok',
        'invalid_ok',
        # Modes for a no-config Parser: mutually exclusive.
        'flag',
        'key_val',
        'greedy',
    ),
)

RGXS = constants(
    'Regexes',
    dict(
        short_option = re.compile(r'^ - ([a-z]) $', re.X + re.I),
        long_option = re.compile(r'^ -- ( [a-z]\w* ([_-]\w+)* ) $', re.X + re.I),
        negative_num = re.compile(r'^ - \d+ $', re.X),
    ),
)

