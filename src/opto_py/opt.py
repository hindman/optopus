
class Opt(object):

    LONG_OPT   = 'LONG_OPT'
    SHORT_OPT  = 'SHORT_OPT'
    POS_OPT    = 'POS_OPT'

    def __init__(self,
                 option_spec,
                 token_type = None,
                 nargs = 0,
                 repeatable = False,
                 tolerant = False,
                 required = False):

        self.option_spec = option_spec
        self.token_type = token_type
        self.nargs = nargs
        self.repeatable = repeatable
        self.tolerant = tolerant
        self.required = required

        self.option = option_spec
        self.destination = self.option.replace('-', '_')
        self.opt_type = (
            self.LONG_OPT if option_spec.startswith('--') else
            self.SHORT_OPT if option_spec.startswith('-') else
            self.POS_OPT
        )

    def __repr__(self):
        fmt = 'Opt({}, opt_type = {}, nargs = {})'
        return fmt.format(self.option, self.opt_type, self.nargs)

    @property
    def is_long_opt(self):
        return self.opt_type == self.LONG_OPT

    @property
    def is_short_opt(self):
        return self.opt_type == self.SHORT_OPT

    @property
    def is_positional_opt(self):
        return self.opt_type == self.POS_OPT

