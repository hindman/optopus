import re

from short_con import cons


r'''

TODO:

    - Unify RGXS (below) and Rgxs (grammar.py).

    - Tighten the regexes for options. Don't use \w. Two reasons:

        - Options either use underscores or hyphens as dividers; they don't
          mix-and-match.

            ^ -- ( [a-z][a-z0-9]* (-[a-z0-9]+)* ) $     # Hyphens
            ^ -- ( [a-z][a-z0-9]* (_[a-z0-9]+)* ) $     # Underscores

        - Cominglng underscore and \w in the context of nested quantifiers can
          lead to catastrophic backtracking.

'''

MODES = cons(
    # Modes for a configured Parser: can be combined.
    'normal',
    'unknown_ok',
    'unconverted_ok',
    'invalid_ok',
    # Modes for a no-config Parser: mutually exclusive.
    'flag',
    'key_val',
    'greedy',
)

RGXS = cons(
    short_option = re.compile(r'^ - ([a-z]) $', re.X + re.I),
    long_option = re.compile(r'^ -- ( [a-z]\w* ([_-]\w+)* ) $', re.X + re.I),
    negative_num = re.compile(r'^ - \d+ $', re.X),
)

