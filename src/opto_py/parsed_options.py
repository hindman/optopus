from .parsed_opt import ParsedOpt

class ParsedOptions(object):

    def __init__(self):
        self.parsed_options = []
        self.i = None

    def add(self, destination, value, opt):
        popt = ParsedOpt(destination, value, opt)
        self.parsed_options.append(popt)

    def __iter__(self):
        self.i = -1
        return self

    def __next__(self):
        try:
            self.i += 1
            return self.parsed_options[self.i]
        except IndexError:
            raise StopIteration

