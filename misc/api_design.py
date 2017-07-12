####
# Parser.
####

p = Parser()

p.parse(args = None)
p.parse_known(args = None)
p.help_text(section = None)
p.error_text()
p.warn(msg)
p.error(msg = None, code = None))
p.exit(code = None, msg = None)

####
# Opts.
####

o = Opt(
    option     = '--job-id',            # Or string-spec with option, aliases, and arg_name.
    aliases    = ['-j', '-J', '--jid'], # Or just one string.
    n_args     = 1,
    repeatable = False,                 # If true, append values.
    choices    = ('A', 'B', 'C', 'D'),
    required   = False,
    tolerant   = False,                 # Setting option makes grammar fully tolerant.
)

####
# Examples.
####

p = Parser(
    # Via simple Opt.
    Opt('--since TERM', type = int, default = lib.last_updated + 1),
    Opt('--limit N', type = int, default = 0),
    Opt('--rebuild'),
    Opt('--experiment EXP'),
    Opt('--stats'),
    Opt('--month M'),
    Opt('--search TERM', repeatable = True),
    Opt('--get ITEM'),

    # Via full Opts.
    Opt(
        'task',
        choices = 'configure submit upload start get stop download find'.split(),
        desc    = 'The odin-client task to run',
    ),

    # Via dict.
    dict(
        option  = '--odin-env ENV',
        groups  = 'general',
        default = 'dev',
        desc    = "Odin environment ('production' for most users).",
    ),

)

