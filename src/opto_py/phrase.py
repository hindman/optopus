from .opt import Opt
from .parsed_options import ParsedOptions

class Phrase(object):

    OPT = 'OPT'
    POS = 'POS'
    PHRASE = 'PHRASE'
    ZONE = 'ZONE'

    AND = 'AND'
    OR = 'OR'

    def __init__(self,
                 subphrases = None,
                 opt = None):
        self.subphrases = subphrases or []
        self.opt = opt

    @property
    def phrase_type(self):
        if self.opt is None:
            return self.PHRASE
        elif self.opt.is_positional_opt:
            return self.POS
        else:
            return self.OPT

    def parse(self, args):
        pos = ParsedOptions()
        return {}

