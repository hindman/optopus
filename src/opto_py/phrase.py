from .opt import Opt
from .parsed_options import ParsedOptions
from .enums import PhraseType, PhraseLogicType

class Phrase(object):

    def __init__(self,
                 subphrases = None,
                 opt = None):
        self.subphrases = subphrases or []
        self.opt = opt

    @property
    def phrase_type(self):
        if self.opt is None:
            return PhraseType.PHRASE
        elif self.opt.is_positional_opt:
            return PhraseType.POS
        else:
            return PhraseType.OPT

    def parse(self, args):
        pos = ParsedOptions()
        return {}

