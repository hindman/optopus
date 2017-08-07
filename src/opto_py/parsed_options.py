from collections import OrderedDict

class ParsedOptions(object):

    def __init__(self, opts = None):
        self.parsed_opts = OrderedDict()
        for opt in (opts or []):
            po = ParsedOpt(opt, None)
            self.parsed_opts[opt.destination] = po

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
        if opt.nargs > 1:
            self.value = []
        else:
            self.value = value

    def __iter__(self):
        tup = (self.destination, self.value)
        return iter(tup)

    @property
    def needed_args(self):
        n = self.opt.nargs
        if self.value is None:
            return n
        elif n < 2:
            return 0
        else:
            return len(self.value) - n

    def __str__(self):
        fmt = 'ParsedOpt({}, {!r})'
        msg = fmt.format(self.destination, self.value)
        return msg

    def __repr__(self):
        return self.__str__()

