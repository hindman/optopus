#! /usr/bin/env python

import sys
import json

from opto_py import (
    Parser,
    Opt,
    FormatterConfig,
    Section,
    SectionName,
    OptoPyError,
)

p = Parser(

    # Searching optionss.
    Opt('-i --ignore-case', sections = ['searching'], text = 'Ignore case distinctions in PATTERN'),
    Opt('--smart-case', sections = ['searching'], text = 'Ignore case distinctions in PATTERN, only if PATTERN contains no upper case. Ignored if -i is specified'),
    Opt('--invert-match', sections = ['searching'], text = 'Invert match: select non-matching lines'),
    Opt('--work-regexp', sections = ['searching'], text = 'Force PATTERN to match only whole words'),
    Opt('--literal', sections = ['searching'], text = 'Quote all metacharacters; PATTERN is literal'),

    # Output options.
    Opt('--lines NUM', sections = ['output'], text = 'Only print line(s) NUM of each file'),
    Opt('--files-with-matches', sections = ['output'], text = 'Only print filenames containing matches'),
    Opt('--files-without-matches', sections = ['output'], text = 'Only print filenames with no matches'),
    Opt('--output EXPR', sections = ['output'], text = 'Output the evaluation of expr for each line (turns off text highlighting)'),
    Opt('--passthru', sections = ['output'], text = 'Print all lines, whether matching or not'),
    Opt('--match', sections = ['output'], text = 'Specify PATTERN explicitly.'),
    Opt('--max-count NUM', sections = ['output'], text = 'Stop searching in each file after NUM matches'),
    Opt('--with-filename', sections = ['output'], text = 'Print the filename for each match (default: on unless explicitly searching a single file)'),
    Opt('--no-filename', sections = ['output'], text = 'Suppress the prefixing filename on output'),
    Opt('--count', sections = ['output'], text = 'Show number of lines matching per file'),
    Opt('--column', sections = ['output'], text = 'Show the column number of the first match'),
    Opt('--after-context NUM', sections = ['output'], text = 'Print NUM lines of trailing context after matching lines.'),
    Opt('-b --before-context NUM', sections = ['output'], text = 'Print NUM lines of leading context before matching lines.'),
    Opt('--context NUM', sections = ['output'], text = 'Print NUM lines (default 2) of output context.'),

    # File presentation options.
    Opt('--pager COMMAND', sections = ['files'], text = 'Pipes all ack output through COMMAND.  For example, --pager="less -R".  Ignored if output is redirected.'),
    Opt('--nopager', sections = ['files'], text = 'Do not send output through a pager.  Cancels any setting in ~/.ackrc, ACK_PAGER or ACK_PAGER_COLOR.'),

    # Positional args.
    Opt('<file>', nargs = (1, 10), text = 'Files or directories to search.'),

    # Section 
    formatter_config = FormatterConfig(
        Section(SectionName.POS, label = 'Positional arguments'),
        Section('searching', label = 'Searching'),
        Section('output', label = 'Search output'),
        Section('files', label = 'File presentation'),
    ),

    # Other.
    program = 'blort',
)

DEFAULT_ARGS = '''
    --lines 12
    --output X
    --max-count 2
    --after-context 1
    -b 2
    --context 3
    --pager 12
    FILE1 FILE2
'''.split()

args = sys.argv[1:] or DEFAULT_ARGS

try:
    parsed_opts = p.parse(args)
except OptoPyError as e:
    print(p.help_text())
    print(e)
    quit()

d = dict(parsed_opts)

print(json.dumps(d, indent = 4))

