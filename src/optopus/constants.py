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
        # TODO: fix.
        #
        # (1) Don't use \w. Use [a-z0-9]
        #
        # (2) Catastrophic backtracking due to the interaction of underscore
        #     and \w within the context of nested quantifiers.
        #     Fixing the underscore vs \w isse will also address
        #     the backtracking problem: for example, this would be
        #     OK because the hyphen and \w have no overlap/ambiguity.
        #
        #         ^ -- ( [a-z]\w* (-\w+)* ) $
        #
        #     Even better would be to drop \w altogether. In a real use
        #     case, command-line options either use underscores or hyphens
        #     as dividers; they don't mix-and-match.
        #
        #         ^ -- ( [a-z][a-z0-9]* (-[a-z0-9]+)* ) $     # Hyphens
        #         ^ -- ( [a-z][a-z0-9]* (_[a-z0-9]+)* ) $     # Underscores
        #
        long_option = re.compile(r'^ -- ( [a-z]\w* ([_-]\w+)* ) $', re.X + re.I),
        negative_num = re.compile(r'^ - \d+ $', re.X),
    ),
)

