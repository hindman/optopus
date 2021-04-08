import sys
from collections import OrderedDict

from .constants import MODES, RGXS

class Parser:

    def __init__(self,
                 spec = None,
                 grammar = None,
                 mode = None):
        self.spec = spec
        self.grammar = grammar
        self.mode = MODES.flag    # TEMP: only one mode so far.

    def parse(self, args = None, mode = None):
        args = sys.argv[1:] if args is None else args
        mode = mode or self.mode
        if mode == MODES.flag:
            return self.parse_noconfig(args, mode)
        else:
            msg = 'Invalid mode: {}'.format(mode)
            raise NotImplementedError(msg)

    def parse_noconfig(self, args, mode):
        # Quick and dirty no-config arg parsing.

        # Index of current arg and N of args.
        ai = 0
        n = len(args)

        # Return data.
        pos_key = 'others'
        options = OrderedDict()
        others = []

        # Process arguments.
        while ai < n:

            # Setup.
            arg = args[ai]
            dest = None

            # Look for an option that is not a negative integer.
            if not RGXS.negative_num.search(arg):
                m = RGXS.short_option.search(arg) or RGXS.long_option.search(arg)
                if m:
                    dest = hyphen2under(m.group(1))

            # Store option or positional.
            if dest:
                options[dest] = True
            else:
                others.append(arg)

            # Advance.
            ai += 1

        # Return.
        if others:
            options[pos_key] = others
        return Result(options)

def hyphen2under(s):
    return s.replace('-', '_')

class Result:
    
    def __init__(self, d):
        self.__dict__ = d

    def __iter__(self):
        return iter(self.__dict__.items())

    def __getitem__(self, k):
        return self.__dict__[k]

    def __len__(self):
        return len(self.__dict__)

    def __contains__(self, k):
        return k in self.__dict__

    def __eq__(self, other):
        return (
            isinstance(other, Result) and
            self.__dict__ == other.__dict__
        )

    def __repr__(self):
        fmt = '{}={!r}'
        inside = ', '.join(fmt.format(*tup) for tup in self.__dict__.items())
        return 'Result({})'.format(inside)

    def __str__(self):
        return repr(self)

