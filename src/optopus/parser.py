import sys

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
        args = args or sys.argv
        mode = mode or self.mode
        if mode == MODES.flag:
            return self.parse_noconfig(args, mode)
        else:
            raise NotImplementedError(f'Invalid mode: {mode}')

    def parse_noconfig(self, args, mode):
        # Quick and dirty no-config arg parsing.

        # Index of current arg and N of args.
        ai = 1
        n = len(args)

        # Return data.
        pos_key = 'others'
        options = {}
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
        return Result(**options)

def hyphen2under(s):
    return s.replace('-', '_')

class Result:
    
    def __init__(self, **kws):
        for k, v in kws.items():
            setattr(self, k, v)

    def __iter__(self):
        return iter(self.__dict__.items())

    def __getitem__(self, k):
        return self.__dict__[k]

    def __len__(self):
        return len(self.__dict__)

    def __contains__(self, k):
        return k in self.__dict__

    def __eq__(self, other):
        return self.__dict__ == dict(other)

    def __str__(self):
        inside = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'Result({inside})'

