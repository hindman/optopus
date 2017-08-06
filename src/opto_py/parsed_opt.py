
class ParsedOpt(object):

    def __init__(self, destination, value, opt):
        self.destination = destination
        self.value = value
        self.opt = opt

    @property
    def needed_args(self):
        n = self.opt.nargs
        if n < 1:
            return 0
        else:
            return len(self.value) - n

