from collections import OrderedDict

from .opt import ONE_TUPLE

class ParsedOptions(object):

    def __init__(self, opts = None):
        self.parsed_opts = OrderedDict()
        for opt in (opts or []):
            po = ParsedOpt(opt, None)
            self.parsed_opts[opt.destination] = po

    def add_opt(self, opt):
        po = ParsedOpt(opt, None)
        self.parsed_opts[opt.destination] = po

    def del_opt(self, opt):
        del self.parsed_opts[opt.destination]

    def __getitem__(self, destination):
        return self.parsed_opts[destination]

    def __iter__(self):
        # User can iterate directory over the ParsedOpt instances.
        # In addition, because ParsedOpt also defines __iter__(), a
        # ParsedOptions instance can be converted directly to a dict.
        return iter(self.parsed_opts.values())

class ParsedOpt(object):

    def __init__(self, opt, value):
        self.destination = opt.destination
        self.opt = opt
        self._values = []

    def __iter__(self):
        tup = (self.destination, self.value)
        return iter(tup)

    def add_value(self, val):
        self._values.append(val)

    @property
    def value(self):
        m, n = self.opt.nargs
        if n > 1:
            return self._values
        elif len(self._values) == 0:
            return None
        else:
            return self._values[0]

    @property
    def requires_args(self):
        m, n = self.opt.nargs
        v = len(self._values)
        return m > v

    @property
    def can_take_args(self):
        m, n = self.opt.nargs
        v = len(self._values)
        return v < n

    def __str__(self):
        fmt = 'ParsedOpt({}, {!r})'
        msg = fmt.format(self.destination, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

