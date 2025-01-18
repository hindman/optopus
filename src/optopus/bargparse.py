####
# Constants and functions for command-line scripts.
####

import sys
import argparse

from io import StringIO

from short_con import cons, constants

####
# Parsing command-line arguments.
####

def parse_args(args,
               arg_configs,
               description = None,
               epilog = None,
               default_group = 'Arguments',
               add_help = False,
               handle_help = True):
    '''
    Takes a sequences of command-line arguments and a sequence of dicts to
    configure argparse arguments, plus other optional parameters. Configures an
    argparse parser, parses args, and returns the parsed data and the parser.
    '''
    # Define the parser.
    ap = argparse.ArgumentParser(
        description = description,
        epilog = epilog,
        add_help = add_help,
    )

    # Configure the parser using the arg_configs data.
    H = 'help'
    for i, ac in enumerate(arg_configs):
        kws = dict(ac)

        # Get option group, if any.
        g = kws.pop('group', default_group if i == 0 else None)
        if g:
            ag = ap.add_argument_group(g)

        # Add a help option, if requested.
        if kws.pop('add_help', None):
            h = dict(
                name = f'--{H} -h',
                action = 'store_true',
                help = kws.get(H, None) or 'Print help text and exit',
            )
            kws = h

        # Add the argument to the current group.
        xs = kws.pop('name').split()
        ag.add_argument(*xs, **kws)

    # Parse args, then handle help or return.
    opts = ap.parse_args(args)
    if handle_help and getattr(opts, H, False):
        exit_with_help(ap)
    else:
        return (ap, opts)

def parse_args_no_exit(*xs, **kws):
    '''
    Like parse_args() but prevents SystemExit and instead returns
    a short-con instance holding ap, opts, usage, err_msg.
    '''
    # Setup.
    ap, opts, usage, err_msg = (None, None, None, None)
    fh = StringIO()
    real_stderr = sys.stderr
    try:
        # Redirect sys.stderr.
        sys.stderr = fh
        ap, opts = parse_args(*xs, **kws)
    except SystemExit as e:
        # Don't let argparse exit(). Get its STDERR output.
        output = sys.stderr.getvalue()
        usage, err_msg =  [
            txt.rstrip()
            for txt in output.split('\n', maxsplit = 1)
        ]
    finally:
        # Restore sys.stderr.
        sys.stderr = real_stderr
        fh.close()
    # Return.
    opts_kws = dict(
        parser = ap,
        opts = opts,
        usage = usage,
        err_msg = err_msg,
    )
    return constants(opts_kws, frozen = False)

####
# Exiting scripts.
####

EXIT = cons(ok = 0, fail = 1)

def halt(code, msg = None):
    '''
    Takes an exit code and optional message.
    Prints msg to stdout/stderr (based on code) and calls sys.exit(code).
    '''
    if msg is not None:
        print(
            msg,
            file = sys.stderr if code else sys.stdout,
            end = '' if msg.endswith('\n') else None,
        )
    sys.exit(code)

def exit_with_help(ap):
    '''
    Takes an argparse parser.
    Prints its help text and calls sys.exit(0).
    '''
    msg = 'U' + ap.format_help()[1:].rstrip()
    halt(EXIT.ok, msg)

def exit_with_usage(ap, err_msg = None):
    '''
    Takes an argparse parser and optionally an error message.
    Prints the argparse usage text and error message; then calls sys.exit(1).
    '''
    msg = 'U' + ap.format_usage()[1:].rstrip()
    if err_msg:
        msg += f'\n{ap.prog}: error: {err_msg}'
    halt(EXIT.fail, msg)

