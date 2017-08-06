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
        return {}

        # TODO:
        # - needed_args is on ParsedOpt, but I'm dealing with Opt instances here.
        # - bind
        # - error

        pos = ParsedOptions()

        used = set()
        pos_i = -1
        arg_i = -1
        prev = None

        pos_opts = [
            sph.opt
            for sph in self.subphrases
            if sph.phrase_type == PhraseType.POS
        ]

        while True:
            # Get the next arg.
            arg_i += 1
            try:
                arg = args[arg_i]
            except IndexError:
                break

            # The arg is an option.
            if is_option(arg):
                if prev and prev.needed_args:
                    # error
                    pass

                prev = None
                for sph in self.subphrases:
                    if sph.phrase_type == PhraseType.OPT:
                        if sph.opt.option == arg:
                            prev = sph.opt
                            break

                if prev is None:
                    # error
                    pass
                elif prev.destination in used:
                    # error
                    pass
                else:
                    # bind
                    used.add(prev.destination)
                    pass

            # The arg is not an option, and the
            # previous option still needs opt-args.
            elif prev and prev.needed_args:
                # bind
                pass

            # Otherwise, we treat the arg as a positional.
            pos_i += 1
            try:
                prev = pos_opts[pos_i]
            except IndexError:
                prev = None
            if prev:
                # bind
                pass
            else:
                # error
                pass

        return {}

