
class Opt(object):

    LONG = 'long'
    SHORT = 'short'
    POSITIONAL = 'positional'

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
            self.LONG if option_spec.startswith('--') else
            self.SHORT if option_spec.startswith('-') else
            self.POSITIONAL
        )

    def __repr__(self):
        fmt = 'Opt({}, opt_type = {}, nargs = {})'
        return fmt.format(self.option, self.opt_type, self.nargs)

