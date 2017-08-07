from .enums import PhraseType, PhraseLogicType
from .errors import OptoPyError
from .opt import Opt
from .parsed_options import ParsedOptions

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

        # Set up the ParsedOptions that we will return.
        opts = [sph.opt for sph in self.subphrases]
        popts = ParsedOptions(opts = opts)

        # The expected positional Opt instances.
        pos_opts = [
            sph.opt
            for sph in self.subphrases
            if sph.phrase_type == PhraseType.POS
        ]

        # Bookkeeping variables.
        # - Indexes to args and pos_opts.
        # - The most recently seen Opt.
        # - A set of already seen Opt.destination values.
        arg_i = -1
        pos_i = -1
        prev = None
        seen = set()

        # Process the args.
        while True:
            arg_i += 1
            try:
                arg = args[arg_i]
            except IndexError:
                break

            # The arg is an option.
            if is_option(arg):

                # Make sure we are not expecting and option-arg.
                if prev and popts[prev].needed_args:
                    fmt = 'Found option, but expected option-argument: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Try to find a matching Opt.
                prev = None
                for sph in self.subphrases:
                    if sph.phrase_type == PhraseType.OPT:
                        if sph.opt.option == arg:
                            prev = sph.opt.destination
                            break

                # Failed to find a match.
                if prev is None:
                    fmt = 'Found unexpected option: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Found a match, but we've already seen it.
                if prev in seen:
                    fmt = 'Found repeated option: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Valid Opt.
                seen.add(prev)
                po = popts[prev]
                if po.opt.nargs == 0:
                    po.value = True
                continue

            # The arg is not an option, and the
            # previous option still needs opt-args.
            elif prev and popts[prev].needed_args:
                po = popts[prev]
                if po.opt.nargs == 1:
                    po.value = arg
                else:
                    po.value.append(arg)
                continue

            # Otherwise, treat the arg as a positional.
            # Try to get a matching Opt.
            pos_i += 1
            try:
                prev = pos_opts[pos_i].destination
            except IndexError:
                prev = None

            # No more positional args are expected.
            if not prev:
                fmt = 'Found unexpected positional argument: {}'
                msg = fmt.format(arg)
                raise OptoPyError(msg)

            # Valid positional.
            po = popts[prev]
            po.value = arg

        # Boom!
        return popts

