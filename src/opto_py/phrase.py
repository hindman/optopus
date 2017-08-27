from .enums import PhraseType, PhraseLogicType
from .errors import OptoPyError
from .opt import Opt, ZERO_TUPLE, ONE_TUPLE
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
        elif self.opt.is_wildcard_opt:
            return PhraseType.WILD
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
        prev_opt = None
        prev_pos = None
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

                # Make sure we are not expecting an option-arg.
                if prev_opt and popts[prev_opt].requires_args:
                    fmt = 'Found option, but expected option-argument: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Try to find a matching Opt.
                prev_opt = None
                for sph in self.subphrases:
                    if sph.phrase_type == PhraseType.WILD:
                        opt = Opt(arg)
                        popts.add_opt(opt)
                        prev_opt = opt.destination
                        break
                    elif sph.phrase_type == PhraseType.OPT:
                        if sph.opt.option == arg:
                            prev_opt = sph.opt.destination
                            break

                # Failed to find a match.
                if prev_opt is None:
                    fmt = 'Found unexpected option: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Found a match, but we've already seen it.
                if prev_opt in seen:
                    fmt = 'Found repeated option: {}'
                    msg = fmt.format(arg)
                    raise OptoPyError(msg)

                # Valid Opt.
                seen.add(prev_opt)
                po = popts[prev_opt]
                if po.opt.nargs == ZERO_TUPLE:
                    po.add_value(True)
                continue

            # The arg is not an option, but the previous option
            # can still take opt-args.
            elif prev_opt and popts[prev_opt].can_take_args:
                po = popts[prev_opt]
                po.add_value(arg)
                continue

            # Otherwise, treat the arg as a positional.
            # - Either use the previous positional (if it can take more args).
            # - Or use the next positional (if there is one).
            if prev_pos and popts[prev_pos].can_take_args:
                pass
            else:
                pos_i += 1
                try:
                    prev_pos = pos_opts[pos_i].destination
                except IndexError:
                    prev_pos = None

            # No more positional args are expected.
            if not prev_pos:
                fmt = 'Found unexpected positional argument: {}'
                msg = fmt.format(arg)
                raise OptoPyError(msg)

            # Valid positional.
            po = popts[prev_pos]
            po.add_value(arg)

        # Boom!
        return popts

