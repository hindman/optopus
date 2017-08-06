from .enums import OptType

class Opt(object):

    def __init__(self,
                 option_spec,
                 nargs = 0,
                 ntimes = (0, 1),
                 tolerant = False):

        self.option_spec = option_spec
        self.nargs = nargs
        self.ntimes = ntimes
        self.tolerant = tolerant

        self.option = option_spec
        self.destination = self.option.strip('--<>')

        self.opt_type = (
            OptType.LONG if self.option.startswith('--') else
            OptType.SHORT if self.option.startswith('-') else
            OptType.POS
        )

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

