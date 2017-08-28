from .enums import OptType

ZERO_TUPLE = (0, 0)
ONE_TUPLE = (1, 1)
MAX_INT = 999999

WILDCARD_OPTION = '*'

def nargs_incremented(nargs):
    m, n = nargs
    return (m + 1, n + 1)

class Opt(object):

    def __init__(self,
                 option_spec,
                 nargs = ZERO_TUPLE,
                 ntimes = (0, 1),
                 tolerant = False):

        self.option_spec = option_spec
        self.option = option_spec
        self.nargs = nargs
        self.ntimes = ntimes
        self.tolerant = tolerant

        if self.option == WILDCARD_OPTION:
            self.destination = None
            self.opt_type = OptType.WILD
        else:
            self.destination = self.option.strip('--<>').replace('-', '_')
            self.opt_type = (
                OptType.LONG if self.option.startswith('--') else
                OptType.SHORT if self.option.startswith('-') else
                OptType.POS
            )

        if self.opt_type == OptType.POS and self.nargs == ZERO_TUPLE:
            self.nargs = ONE_TUPLE

    def __repr__(self):
        fmt = 'Opt({}, opt_type = {}, nargs = {})'
        return fmt.format(self.option, self.opt_type, self.nargs)

    @property
    def is_long_opt(self):
        return self.opt_type == OptType.LONG

    @property
    def is_short_opt(self):
        return self.opt_type == OptType.SHORT

    @property
    def is_positional_opt(self):
        return self.opt_type == OptType.POS

    @property
    def is_wildcard_opt(self):
        return self.opt_type == OptType.WILD

    @property
    def nargs(self):
        return self._nargs

    @nargs.setter
    def nargs(self, val):
        # TODO: validate m<=n.
        # TODO: factor out common parts in setters for nargs/ntimes.
        if isinstance(val, (list, tuple)):
            self._nargs = val
        else:
            self._nargs = (val, val)

    @property
    def ntimes(self):
        return self._ntimes

    @ntimes.setter
    def ntimes(self, val):
        if isinstance(val, (list, tuple)):
            self._ntimes = val
        else:
            self._ntimes = (val, val)

