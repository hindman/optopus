from .enums import OptType
from collections import Iterable

ZERO_TUPLE = (0, 0)
ONE_TUPLE = (1, 1)
MAX_INT = 999999

OPT_PREFIX = '-'
UNDERSCORE = '_'
WILDCARD_OPTION = '*'
LONG_OPT_PREFIX = OPT_PREFIX + OPT_PREFIX
SHORT_OPT_PREFIX = OPT_PREFIX
OPT_SPEC_STRIP_CHARS = OPT_PREFIX + '<>'

def nargs_incremented(nargs):
    m, n = nargs
    return (m + 1, n + 1)

class Opt(object):

    def __init__(self,
                 option_spec,
                 nargs = ZERO_TUPLE,
                 ntimes = (0, 1),
                 text = None,
                 sections = None,
                 tolerant = False):

        self.option_spec = option_spec
        self.option = option_spec
        self.nargs = nargs
        self.ntimes = ntimes      # Not supported now.
        self.text = text
        self.sections = list(sections or [])
        self.tolerant = tolerant

        if self.option == WILDCARD_OPTION:
            self.destination = None
            self.opt_type = OptType.WILD
        else:
            self.destination = self.option.strip(OPT_SPEC_STRIP_CHARS).replace(OPT_PREFIX, UNDERSCORE)
            self.opt_type = (
                OptType.LONG if self.option.startswith(LONG_OPT_PREFIX) else
                OptType.SHORT if self.option.startswith(SHORT_OPT_PREFIX) else
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
        self._nargs = self._get_nx_tuple(val, 'nargs')

    @property
    def ntimes(self):
        return self._ntimes

    @ntimes.setter
    def ntimes(self, val):
        self._ntimes = self._get_nx_tuple(val, 'ntimes')

    def _get_nx_tuple(self, val, attr_name):
        #
        # Convert val to a tuple. For example, these are
        # valid inputs: (0, 1), (1, 1), 1, 2, etc.
        if isinstance(val, Iterable):
            tup = tuple(val)
        else:
            tup = (val, val)
        #
        # Get m, n values from the tuple.
        try:
            m, n = map(int, tup)
        except Exception:
            m, n = (None, None)
        #
        # Return the valid tuple or raise.
        if m is None or m < 0 or m > n:
            fmt = 'Invalid {}: {}'
            msg = fmt.format(attr_name, val)
            raise OptoPyError(msg)
        else:
            return tup

