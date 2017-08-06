from .opt import Opt
from .parsed_options import ParsedOptions
from .enums import PhraseType, PhraseLogicType

def is_option(arg):
    return (
        arg.startswith('--') or
        arg.startswith('-')
    )

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

        i = -1
        max_i = len(args) - 1

        while i < max_i:
            i += 1
            arg = args[i]

            # if option:
            #   if there is prev-opt needed nargs:
            #     error
            #   elif option matches:
            #     bind
            #     set prev-opt
            #   else:
            #     error
            # elif there is a prev-opt needing nargs:
            #   bind
            # elif there are remaining positional slots:
            #   bind
            # else:
            #   error

