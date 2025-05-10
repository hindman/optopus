
# Argle

## Because Python needs a better command-line argument parser

To varying degrees of success, command-line argument parsing libraries do a
mostly adequate job handling the common use cases. They are able to parse
garden-variety command-line inputs and provide help text to end users. Some
libraries take partial steps to support a larger set of features: basic
conversion and validation; varying numbers of optional parameters or positional
arguments; mutually exclusive options; subcommand-style programs like git; and
occasionally a small amount of help text customization or the ability to
control error handling.

But why settle at such low expectations? Every year thousands of command-line
scripts are written in Python using argument parsers that are just OK: they are
less intuitive, more verbose, and more hemmed in by restrictions than they need
to be.

Argle will change that by providing a library that is easy and efficient to
configure; powerful when needed for complex, specialized, unusual, or merely
particular situations; and designed with an eye toward customization and
flexibility. At every level of program complexity — ranging from throwaway
scripts to the next-big-thing — Argle will offer a superior approach to
handling command-line arguments.

The library is under active development and an alpha release has been published.
The purpose of that release was mainly to reserve the project name in
[PyPI][pypi_argle] but it already provides one small bit of useful
functionality, one not currently available in other libraries — namely,
no-configuration parsing, which is handy for temporary or experimental scripts
that require nothing more than open-ended support for options and positionals.

```bash
# Install the library in the usual way.

$ pip install argle
```

```python
# Write almost no code to parse arguments.

from argle import Parser

p = Parser()
opts = p.parse()

# Check out the returned data object.

print(opts)
print(opts.bar)               # Attribute access.
print(opts['bar'])            # Key access.
print('bar' in opts)          # Membership testing.
for dest, val in opts:        # Direct iteration.
    print((dest, val))
```

```bash
# Demo usage.

$ python demo.py Z1 Z2 --bar B1 B2 -x -y Y1 -- Z3
Result(positionals=['Z1', 'Z2', 'Z3'], bar=['B1', 'B2'], x=True, y='Y1')
['B1', 'B2']
['B1', 'B2']
True
('positionals', ['Z1', 'Z2', 'Z3'])
('bar', ['B1', 'B2'])
('x', True)
('y', 'Y1')
```

## Argle vs. the competition

Rather than starting with my opinions about the state of command-line argument
parsers in Python, Ruby, and, from an earlier era, Perl, a more compelling case
can be made by starting with something concrete: side-by-side comparisons
across a spectrum of program types.

I will use [argparse][py_argparse] in the comparisons, but not because it is a
bad library. To the contrary, it is better than the vast majority of
alternatives. Argparse is a dream to use compared to its predecessor,
[optparse][py_optparse], and it is easier to configure than the argument parser
built into [Ruby][rb_optparse]. Basically, argparse is among the best of a
barely-adequate bunch.

#### Example 1

The comparisons will start with a minimal script: a bare-bones grep clone that
will allow us to use Python regular expressions rather than whatever grep ships
with. Schematically, we want to handle this usage:

    pgrep [-i] [-v] <rgx> <path>

Here is the argparse configuration:

```python
ap = argparse.ArgumentParser()
ap.add_argument('-i', action = 'store_true')
ap.add_argument('-v', action = 'store_true')
ap.add_argument('rgx')
ap.add_argument('path')
```

The equivalent Argle configuration dispenses with all of that hassle.
Instead, it relies on the conventions that most programmers already know
regarding command-line usage syntax — the same syntax you just read and
understood a few paragraphs above. That syntax, along with a small number of
sensible additions, will allow Argle to reduce developer hassle significantly
while also providing a more powerful and flexible argument parser. The
difference between the two configurations is striking.

```python
p = Parser('[-i] [-v] <rgx> <path>')
```

#### Example 2

As a second comparison, we will take the same script and make it more
fleshed-out with some help text and the ability to support zero or more file
paths.

```python
ap = argparse.ArgumentParser()
ap.add_argument('-i', '--ignore-case', action = 'store_true', help = 'Ignore case')
ap.add_argument('-v', '--invert-match', action = 'store_true', help = 'Select non-matching lines')
ap.add_argument('rgx', help = 'Python regular expression')
ap.add_argument('path', nargs = '*', help = 'Path(s) to input')
```

The Argle configuration is more efficient (48% the size of argparse), more
readable, and requires less API knowledge. You just type what you want and have
to remember little more than a mostly already-known syntax. Note that [Example
1](#example-1) used what Argle calls a usage-variant syntax: it expressed the
full command-line grammar in schematic form. Example 2 uses a closely related
syntax, called opt-spec syntax. Each line configures a single Opt (a
configuration object representing a positional argument or option) using the
same syntax seen in the first example, optionally accompanied by one or more
aliases and help text. Because the opt-spec syntax is more featureful at the
level of individual Opts (it can declare aliases and help text), it is often
the easiest mechanism to use for non-trivial scripts that do not have any
special grammatical needs.

```python
p = Parser('''
    <rgx> : Python regular expression
    [<path>...] : Path(s) to input
    [-i --ignore-case] : Ignore case
    [-v --invert-match] : Select non-matching lines
''')
```

#### Example 3

The next step in the script's evolution might be to add some more options,
along with conversion and validation of the inputs. The argparse code starts to
get a bit heavy.

```python
ap = argparse.ArgumentParser()
ap.add_argument('rgx', metavar = '<rgx>', type = re.compile, help = 'Python regular expression')
ap.add_argument('path', metavar = '<path>', type = pathlib.Path, nargs = '*', help = 'Path(s) to input')
ap.add_argument('--ignore-case', '-i', action = 'store_true', help = 'Ignore case')
ap.add_argument('--invert-match', '-v', action = 'store_true', help = 'Select non-matching lines')
ap.add_argument('--max-count', '-m', metavar = '<n>', type = int, help = 'Stop searching after N matches')
ap.add_argument('--context', '-C', metavar = '<n>', type = int, help = 'Print N lines of before/after context')
ap.add_argument('--color', metavar = '<col>', choices = ('red', 'green', 'blue'), help = 'Highlight matching text: red, green, blue')
```

By comparison, the Argle configuration remains compact (67% the size of
argparse), intuitive, and easy to scan. If you want to spiff it up further you
can have your editor line everything up on the colon separators. Also notice
the two phases of configuration: most of the work is done in the text syntax
(called a parser `spec`, short for specification); and then extra configuration
is applied via a programmatic API. Notice also that the API emphasizes simple
conveniences: if any Opts share configuration parameters (options `-m` and `-C`
in our example), they can be handled jointly in a single `config()` call. The
last `config()` call is not required, but it helps to clean up the help text,
which we will examine shortly. In spite of its brevity, the Argle
configuration actually does more validation (in the example, `isfile` and
`ispositive` are assumed to be callables defined by the user).

```python
p = Parser('''
    <rgx> : Python regular expression
    [<path>...] : Path(s) to input
    [-i --ignore-case] : Ignore case
    [-v --invert-match] : Select non-matching lines
    [-m --max-count <n>] : Stop searching after N matches
    [-C --context <n>] : Print N lines of before/after context
    [--color red|green|blue] : Highlight matching text
''')

p.config('rgx', convert = re.compile)
p.config('path', convert = Path, validate = isfile)
p.config('max_count', 'context', convert = int, validate = ispositive)
```

#### Example 3 help text

Before looking at the final code comparison, we can also consider the
differences in help text between the two libraries. The output from argparse is
familiar and reasonable, if a bit awkward at times. It is also mildly annoying
if you are among those who care about finer details related to capitalization,
spacing, and overall readability.

```
usage: pgrep [-h] [--ignore-case] [--invert-match] [--max-count <n>]
             [--context <n>] [--color <col>] <rgx> [<path> ...]

positional arguments:
  <rgx>                 Python regular expression
  <path>                Path(s) to input

optional arguments:
  -h, --help            show this help message and exit
  --ignore-case, -i     Ignore case
  --invert-match, -v    Select non-matching lines
  --max-count <n>, -m <n>
                        Stop searching after N matches
  --context <n>, -C <n>
                        Print N lines of before/after context
  --color <col>         Highlight matching text: red, green, blue
```

The Argle help text is cleaner and easier to read. Those gains mostly come
from a couple of alternative techniques that Argle supports but does not
require: first, the ability to flexibly summarize groups of options
symbolically in the usage text (as `[options]` in this example, which was done
in the last `p.config()` call above); and second, the separation of option help
from an alias listing.

```
Usage:
  pgrep [<options>] <rgx> [<path>...]

Arguments:
  <rgx>                  Python regular expression
  <path>                 Path(s) to input
  --ignore-case, -i      Ignore case
  --invert-match, -v     Select non-matching lines
  --max-count <n>, -m    Stop searching after N matches
  --context <n>, -C      Print N lines of before/after context
  --color <col>          Highlight matching text: red, green, blue
  --help, -h             Print help text and exit
```

#### Example 4

As a final comparison, we will expand beyond grepping into a suite of
regex-based text wrangling utilities: grep (search for matching lines), sub
(search and replace), and search (search and grab). For this script, we will
need to use argparse subparsers, which makes the configuration even heavier and
harder to read or scan. It requires users to learn and remember even more API.
To avoid code repetition for options shared across the subcommands, the user
has to take some care in defining a secondary data structure (`argconf` in this
example). And if you work with colleagues who frown on long lines (as they
probably should, for readability reasons well-understood for decades by the
publishing industry) you will have to expand the code footprint further by
wrapping the lines sensibly or by extracting help text into a separate data
structure to de-bulk the main configuration code.

```python
ap = argparse.ArgumentParser(prog = 'wrangle')

sps = ap.add_subparsers(dest = 'task', help = 'Task to perform', metavar = '<task>')
sp1 = sps.add_parser('grep', help = 'Emit lines matching pattern')
sp2 = sps.add_parser('sub', help = 'Search for pattern and replace')
sp3 = sps.add_parser('search', help = 'Emit text matching pattern')

argconf = {
    'rgx': dict(metavar = '<rgx>', type = re.compile, help = 'Python regular expression'),
    'path': dict(metavar = '<path>', type = pathlib.Path, nargs = '*', help = 'Path(s) to input'),
    '-i': dict(action = 'store_true', help = 'Ignore case'),
}

sp1.add_argument('--ignore-case', '-i', **argconf['-i'])
sp1.add_argument('--invert-match', '-v', action = 'store_true', help = 'Select non-matching lines')
sp1.add_argument('--max-count', '-m', metavar = '<n>', type = int, help = 'Stop searching after N matches')
sp1.add_argument('--context', '-C', metavar = '<n>', type = int, help = 'Print N lines of before/after context')
sp1.add_argument('--color', metavar = '<col>', choices = ('red', 'green', 'blue'), help = 'Highlight matching text: red, green, blue')
sp1.add_argument('rgx', **argconf['rgx'])
sp1.add_argument('path', **argconf['path'])

sp2.add_argument('--ignore-case', '-i', **argconf['-i'])
sp2.add_argument('--nsubs', '-n', metavar = '<n>', type = int, help = 'N of substitutions')
sp2.add_argument('rgx', **argconf['rgx'])
sp2.add_argument('rep', metavar = '<rep>', help = 'Replacement text')
sp2.add_argument('path', **argconf['path'])

sp3.add_argument('--ignore-case', '-i', **argconf['-i'])
sp3.add_argument('--group', '-g', metavar = '<n>', type = int, help = 'Emit just capture group N [0 for all]')
sp3.add_argument('--delim', '-d', metavar = '<s>', help = 'Delimeter for capture groups [tab]')
sp3.add_argument('--para', '-p', action = 'store_true', help = 'Emit capture groups one-per-line, paragraph-style')
sp3.add_argument('rgx', **argconf['rgx'])
sp3.add_argument('path', **argconf['path'])
```

Once again, the comparison with Argle is striking. Even with subcommands, the
Argle configuration remains intuitive and compact (60% the size of argparse).
The user does have to learn a few additional syntax rules (the double-colon as
a section marker, and the syntax for positional usage variants like
`<task=grep>`), but the API burden remains low. A Python programmer unfamiliar
with the library could quickly infer the basic intent even without knowing the
all of the rules. This example illustrates both syntax styles mentioned above:
usage-variant syntax to define the subcommand-style grammar that our program
needs in the first section (for convenience, this section can refer to the Opts
via their short aliases); followed by another section using opt-spec syntax to
configure the individual Opts more fully. Finally, notice that this
configuration does more than the argparse example: it defines the `-d` and `-p`
options as alternatives (mutually exclusive). That behavior is achievable in
argparse, at the cost of looking up even more API. Argle simply builds on a
usage syntax already known to many developers: a pipe to delimit alternatives.

```python
p = Parser('''wrangle
    <task=grep>   [--ignore-case] [--invert-match] [--max-count] [--context]
                  [--color <red|green|blue>]
                  <rgx> [<path>...]
    <task=sub>    [--ignore-case] [--nsubs]
                  <rgx> <rep> [<path>...]
    <task=search> [--ignore-case] [--group] [--delim | --para]
                  <rgx> [<path>...]

    <task>               : Task to perform
    <task=grep>          : Emit lines matching pattern
    <task=sub>           : Search for pattern and replace
    <task=search>        : Emit text matching pattern
    <rgx>                : Python regular expression
    <rep>                : Replacement text
    [<path>...]          : Path(s) to input
    [-i --ignore-case]   : Ignore case
    [-v --invert-match]  : Select non-matching lines
    [-m --max-count <n>] : Stop searching after N matches
    [-C --context <n>]   : Print N lines of before/after context
    [--color <>]         : Highlight matching text
    [-n --nsubs <n>]     : N of substitutions
    [-g --group <n>]     : Emit just capture group N [0 for all]
    [-d --delim <s>]     : Delimeter for capture groups [tab]
    [-p --para]          : Emit capture groups one-per-line, paragraph-style
''')

p.config('rgx', convert = re.compile)
p.config('path', convert = Path, validate = isfile)
p.config('max_count', 'context', 'nsubs', convert = int, validate = ispositive)
p.config('group', convert = int, validate = nonnegative)

p.config_help_text(options_summary = False)
```

#### Example 4 help text

The help text comparison for the last example further highlights the awkward
adequacy of argparse: yes it works, but no more than that. Here are the outputs
from four uses of `--help` (generally and for each of the three subcommands).

```
usage: wrangle [-h] <task> ...

positional arguments:
  <task>      Task to perform
    grep      Emit lines matching pattern
    sub       Search for pattern and replace
    search    Emit text matching pattern

optional arguments:
  -h, --help  show this help message and exit
```

```
usage: wrangle grep [-h] [--ignore-case] [--invert-match] [--max-count <n>]
                    [--context <n>] [--color <col>]
                    <rgx> [<path> ...]

positional arguments:
  <rgx>                 Python regular expression
  <path>                Path(s) to input

optional arguments:
  -h, --help            show this help message and exit
  --ignore-case, -i     Ignore case
  --invert-match, -v    Select non-matching lines
  --max-count <n>, -m <n>
                        Stop searching after N matches
  --context <n>, -C <n>
                        Print N lines of before/after context
  --color <col>         Highlight matching text: red, green, blue
```

```
usage: wrangle sub [-h] [--ignore-case] [--nsubs <n>] <rgx> <rep> [<path> ...]

positional arguments:
  <rgx>                Python regular expression
  <rep>                Replacement text
  <path>               Path(s) to input

optional arguments:
  -h, --help           show this help message and exit
  --ignore-case, -i    Ignore case
  --nsubs <n>, -n <n>  N of substitutions
```

```
usage: wrangle search [-h] [--ignore-case] [--group <n>] [--delim <s>]
                      <rgx> [<path> ...]

positional arguments:
  <rgx>                Python regular expression
  <path>               Path(s) to input

optional arguments:
  -h, --help           show this help message and exit
  --ignore-case, -i    Ignore case
  --group <n>, -g <n>  Emit just capture group N [0 for all]
  --delim <s>, -d <s>  Delimeter for capture groups [tab]
  --para, -p           Emit capture groups one-per-line, paragraph-style
```

The Argle help text is cleaner, easier to read, and more compact. It is also
unified rather than separate (everything from a single usage of `--help`). If
needed, the parser can be easily configured to support use cases that need
separate help text for different usage variants (many programs do not).

```
Usage:
  wrangle grep [--ignore-case] [--invert-match] [--max-count <n>] [--context <n>]
          [--color <red|green|blue>] [--help] <rgx> [<path>...]
  wrangle sub [--ignore-case] [--nsubs <n>] [--help] <rgx> <rep> [<path>...]
  wrangle search [--ignore-case] [--group <n>] [--delim <s> | --para] [--help]
          <rgx> [<path>...]
  wrangle --help

Arguments:
  <task>                 Task to perform:
    grep                 - Emit lines matching pattern
    sub                  - Search for pattern and replace
    search               - Emit text matching pattern
  <rgx>                  Python regular expression
  <path>                 Path(s) to input
  <rgx>                  Python regular expression
  <rep>                  Replacement text
  <path>                 Path(s) to input
  --ignore-case, -i      Ignore case
  --invert-match, -v     Select non-matching lines
  --max-count <n>, -m    Stop searching after N matches
  --context <n>, -C      Print N lines of before/after context
  --color <>             Highlight matching text: red, green, blue
  --nsubs <n>, -n        N of substitutions
  --group <n>, -g        Emit just capture group N [0 for all]
  --delim <s>, -d        Delimeter for capture groups [tab]
  --para                 Emit capture groups one-per-line, paragraph-style
  --help, -h             Print help text and exit
```

## Powerful grammars built from simple parts

Most argument parsing libraries start from the a basic model of command-line
usage: an ordered sequence of positionals along with an unordered set of short
and long options that can be freely mixed among the positionals and that can
take zero or more ordered parameters.

The argparse library is a representative example in this vein: it does a
reasonable job for common use cases but struggles with command lines that
require a grammar falling beyond the typical. On [Stack Overflow][stack_home]
and the [Python bug tracker][py_bugs], for example, one can find a variety of
desired and generally sensible use cases that argparse cannot support at all or
can support only partially after some uncomfortable hackery.

The most frequently desired grammatical features seem to fall into the
following buckets:

**Mutual exclusion beyond the simplest case**. The argparse library supports
mutual exclusion among options considered individually. But it cannot apply
that type of requirement to groups of options (for example, `-x` OR `-y` `-z`).
See [here][grammar_ex01] or [here][grammar_ex02].

**Conditional requirements or exclusions**. The argparse library does offer
subparsers as one mechanism to apply conditional requirements, but this can be
a heavy device for what are often fairly simple grammatical needs (for example,
if `-x` then require either `-y` or `-z`; or if `-a` then disallow `-b`). See
[here][grammar_ex03], [here][grammar_ex04], [here][grammar_ex05], or
[here][grammar_ex06].

**Flexible specification of alternatives**. Again, argparse supports this
partially (via subparsers or mutually exclusive options), but it lacks a
simple, general-purpose mechanism for alternatives (for example, either `-a` OR
`-b` OR `-a` `-b`). See [here][grammar_ex07], [here][grammar_ex08], or
[here][grammar_ex09].

**Flexible quantification**. The argparse library supports four basic
quantifiers (`N`, `?` `*`, and `+`), but it lacks support for regex-style
ranges (e.g., `{1,3}`), which can arise in a variety of plausible uses cases.
There is no strong reason not to support them. See [here][grammar_ex10],
[here][grammar_ex15], or [here][grammar_ex16].

**More complex repetition**. The argparse library can apply quantifiers to
individual options or positionals, but not to groups (for example, two
positionals, `<x> <y>`, repeatable in pairs). Sometimes the group that needs to
be repeated is the full command-line grammar. In fact, after Argle, my next
project involves such a program: a Python tool for quick text transformation
pipelines in the spirit of sed/awk/perl one-liners, but with more intuitive
usage, a built-in set of core utilities, and an easy mechanism for users to
define their own. Because the tool is literally a pipeline for text running
through various conversion and computation stages, it makes sense to model the
command-line grammar as repeatable. This use case is mostly supportable by
cobbling together multiple argparse parsers, but it is awkward and requires a
bit of special logic. Argle will support a use case like that with almost no
extra API-learning cost for the user. See [here][grammar_ex11],
[here][grammar_ex12], or [here][grammar_ex13].

**Parameter or argument independence**. When an option has multiple parameters
or a positional has multiple arguments, most argument parsers force them to be
configured identically. But sometimes independence makes sense (for example,
`-a <A|B|C> <X|Y>`, where each parameter has different choices). See
[here][grammar_ex14].

The deeper problem with most argument parsing libraries is that they rest on a
weak foundation. Perhaps a bit uncharitably, one could say that they started
with the simplest model of command-line grammar (described at the start of this
section). Then they tacked on additional features to meet some of the more
common usage patterns: if users occasionally need subcommand-style programs,
add a new API to create and configure subparsers; if users occasionally need
simple mutual exclusion, add a new API to handle it; and so forth until the
library reaches the technical limits of the weak foundation.

A better model is to look to related domains for a small number of general,
composable concepts: elements (in this case, positionals, options, and their
parameters), groups, alternatives, usage variants, and quantifiers. At least
for most developers, those concepts are frequently observed in regular
expressions and in the related set of conventions observed in technical
documentation for command-line programs — namely, their usage syntax. By
resting on these composable ideas, Argle will be able to achieve both
simplicity and greater power.

In more schematic terms, Argle supports a wide variety of command-line
grammars by combining a few core ideas:

- Groups enclosed either by parentheses (if required) or square brackets (if
  optional). Groups as first-class citizens is one of the crucial missing
  ingredients in most libraries.

- Angle brackets for any kind of variable end-user input, whether it be
  positionals (`<foo>`) or option parameters (`--point <x> <y>`). The universe of
  command-line programs lacks a consistent convention on how to represent
  variable inputs. There are four main styles relying on different bracketing
  conventions (angle, square, or curly) and different capitalization schemes
  (all uppercase, all lower, or mixed). For a variety of technical and
  practical reasons, Argle mimics Git and some other tools in using angle
  brackets consistently.

- Pipes to separate alternatives — a ubiquitous convention both in usage text
  and regex.

- Quantifiers that can applied to single elements or groups. This is another
  one of the crucial missing ingredients in most parsers. Argle relies
  primarily on the quantifiers from usage-syntax conventions: `...` for
  one-or-more and square brackets to convey optionality. To those it adds the
  regex `{m,n}` syntax for quantity ranges.

- Like regular expressions, grammar elements and parsing itself are greedy by
  default. This policy decision is necessary to resolve a variety of parsing
  ambiguities that can arise. Argle also follows regex in using `?` as the
  device to make a quantifier non-greedy.

- The ability to name elements or groups symbolically both for display in usage
  text and for the purpose of naming things in the parsed result. This behavior
  is important not for grammatical reasons but in order to be able to organize
  the parsed data in usable ways, especially for more complex grammars.

Examples of most of those grammatical features have already been shown, but
another might help to make things more explicit. The example below defines a
grammar for a program with two usage variants (named Add and Delete) triggered
by the value of the `<task>` positional (add or delete), along with a third
variant (named Examples) that allows the user to request some help text showing
examples. Note that usage variants can have explicit names (as shown below) or
not (the more common case); if defined, a variant name is mainly useful as a
convenient label/handle when using the Parser's configuration API.

```python
p = Parser('''name-db
    Add      : <task=add> (<name> <id>)...
    Delete   : <task=delete> <id>{1,5} [--archive [--json [--indent] | --xml]]
    Examples : --examples
''')
```

Each usage variant above has something noteworthy.

- The Add variant requires the `<name>` and `<id>` positionals to come in pairs.

- The Delete variant uses a regex-style quantifier for `<id>`, and the `--archive`
  option is configured so that it can be accompanied by other options in
  different combinations (either `--xml` or `--json` plus an optional `--indent`).

- The Examples variant takes an entirely different form from the
  subcommand-style of the other two variants. It illustrates the general point
  noted above: if you start with a narrow vision for command-line grammars and
  then tack on a subparser API, you can support typical subcommand-style
  programs, but nothing else; however, if you start with composable concepts
  you can support subcommand-style programs and all kinds of other needs as
  well — with almost no additional API burden on users.

Defining command-line grammar via a configuration syntax based on usage text is
not a new idea. While most argument parsing libraries are like argparse in
configuring the parser's grammar via a programmatic API, some libraries take a
different approach: the user writes the usage and help text (sometimes enhanced
with special syntax elements), the parser is derived from that text, and the
text (minus any special syntax) is used as the literal usage and help text
presented to end users. Examples include [docopt][docopt_url] in Python or
[Getopt::Long::Descriptive][getopt_long_desc], [Getopt::Euclid][getopt_euclid],
and [Getopt::Declare][getopt_declare] in Perl.

I believe my first exposure to such ideas came in the early 2000s from Damian
Conway, a great programming educator and the initial author of Getopt::Euclid.
He is arguably the inspiration for this library: I have been thinking, on and
off, about how to make a better argument parser since then. A second debt is
owed to Vladimir Keleshev, the primary author of Python's docopt. That library,
in my view, has unfortunate and signficant limitations, but it is based on some
compelling ideas. The 2012 PyCon [video][docopt_vid] promoting the library is
entertaining and wonderfully polemical in the best sense of the word — well
worth the time of anyone interested in the subject. Watching the video in the
early 2010s rekindled my interest in the Argle project and helped me refine
ideas I had been mulling over for a long time.

In spite of those intellectual debts to this alternative tradition in argument
parsers, my experiments with many libraries convinced me that both approaches
— API-driven configuration and usage-syntax-driven configuration — have their
strengths and weaknesses. Argle aims to build on the strengths of each:

**Usage-syntax to define the core**. Argle encourages the use of text as the
primary mechanism to configure the command-line grammar and the logical
relationships among the elements, along with the names to be used when
referring to options, parameters, positionals, groups, and usage variants. It
also encourages the text syntax for defining option aliases and the help text
for individual positionals and options. Those are the areas where the
text-driven approach shines, either because the configuration is unavoidably
textual (for example, help text for individual Opts) or because text is simply
a more efficient and intuitive configuration mechanism than API calls (the
grammatical relationships among the elements). Consider the example grammar
shown above: it conveys a lot of information very efficiently and intuitively
when compared against what most API-driven libraries would require of the user
(and none of them could fully support the example). In spite of the benefits of
text-based configuration, most programmers do not want to handcraft the
end-user-facing usage and help text if a computer program can do it
consistently and well (not to mention dynamically responding to terminal width
or to runtime configurations). That is why Argle takes substantial
inspiration from, but does not fully adopt, the ideas motivating the
text-driven parsers like Getopt::Euclid and docopt. Argle treats the text
primarily as a configuration syntax, not literal usage text. Naturally, it does
provide an easy mechanism for that syntax to include blocks of literal text.

**Programmatic API for the rest**. To apply other configurations (defaults,
conversion, validation, and various other details), Argle builds on the
strength of the API approach and adds some additional conveniences to keep the
developer burden low. Although it is theoretically possible to configure some
of those things via a text syntax, the approach has rapidly diminishing
returns, because each feature addition requires increasingly baroque syntactic
elements. Argle takes a hybrid approach, combining the benefits of each
configuration style.

Finally, it should be noted that all of the library's behaviors will be
configurable via the API, including the grammar — not merely to satisfy
traditionalists, but because, at least for simpler use cases, configuring the
parser's grammar via the API also works well. Note also that even the API
configuration can leverage as much or little of the grammar syntax as desired.
To illustrate, the following configurations achieve the same thing: an optional
`--dim` having an alias and taking 2 to 3 parameters. I suspect that many
developers will prefer the efficiency and intuitiveness of the text syntax, but
that opinion is not enforced by the library. Users can freely operate at any
point they prefer along the text-to-API spectrum.

```python
# All text syntax.
Opt('[-d --dim <> <> [<>]]')

# Hybrid.
Opt('-d --dim', nparams = (2,3), ntimes = (0,1))

# All API.
Opt(dest = 'dim', kind = 'option', nparams = (2,3), ntimes = (0,1), aliases = 'd')
```

## Designed for flexibility

In addition to having an insufficiently powerful grammatical foundation,
existing argument parsers tend to be inflexible in their design and thus not
open to very much customization. Two areas are particularly noteworthy.

**Help and error text**. Most libraries offer only limited control over the
formatting, arrangement, and style of help and error text. Argparse, for
example, offers a few subclasses that adjust help text in small ways or allow
the user to supply regular text blocks that will be presented as-is rather than
wrapped. But the underlying `HelpFormatter` class is not friendly to
customization generally. Some of its stylistic choices seem non-standard or
inelegant to my eye and I have never found ways to adjust them without awkward
hacks. More fundamentally, argparse is not prepared to handle bigger changes,
ranging from fairly standard needs (for example, help text in man-page format)
to more innovative approaches. Argle will offer some of those approaches
directly with the aim of giving programmers the ability to lighten-up and
improve the readability of help text.

**Side effects**. Many argument parsers, including argparse until Python 3.9,
are rigid in response to invalid input. They start with sensible default
behavior: in the face of bad input, print brief usage text and an error
message, then exit. But they turn that default into a requirement by providing
no good way to prevent the side effects from occurring. By good way, I mean one
where the library would include sufficient contextual data about the error,
rather than just providing the error text as a string. That default behavior
works in the most common cases, but sometimes programs have other needs.
Argument parsing libraries should follow ordinary best practices by giving the
user the ability to bypass major side effects like printing and exiting.
Imagine any other data oriented library imposing such effects without easy
disabling.

To the extent that the existing libraries do allow customization, the
mechanisms for doing that are often awkward. Argparse is an apt example: many
suggested workarounds to user difficulties with the library involve
subclassing, but most argparse classes do not appear to be well-designed for
inheritance (and some of their docstrings seem to discourage it outright). At a
minimum, one a can say that the library does not provide authoritative guidance
on which classes are amenable to subclassing, if any, and what users should do
or avoid when doing so.

Argle will be built with an eye toward flexibility and customization. To the
extent feasible, all controllable parameters governing the generation of text
will be adjustable. And for dynamic configuration needs — whether related to
help text, error text, side effects, or parsing — the library will support
them via hooks rather than subclassing. Developers needing special behavior
will not have to worry whether they have implemented a method override robustly
enough in the face of edge cases or future evolution of the library. Instead,
they will just have to write an ordinary hook function based on a documented
API.

## Reducing the burden on developers

Flexibility and customization are aimed not only at a small minority of
developers with strong opinions about technical documentation and page layout.
They also have practical ramifications. Developers want to build tools that
users can easily understand. Without that, those developers face higher
short-term and long-term support costs.

The broad theme connecting such matters is to reduce developer hassle as it
relates to argument handling. Some examples on the Argle roadmap.

#### Efficient Opt configuration API

When a program needs more than a few Opts, it is not uncommon for some them to
have similar configuration needs. Argle includes a simple, minimal-hassle API
to query for one or more grammar elements (mainly Opts, but sometimes Variants
or Groups) and apply supplemental configurations to all elements contained in
the query result. Those configurations are applied to the Opts in an additive
fashion, making it possible to configure many Opts very efficiently. This was
demonstrated briefly in a few in the examples above, where multiple Opts were
configured in one call to accept only positive integers.

#### Handy utilities for exiting and error messages

Argument parsers are all used in the same general context and such programs
have many common needs during the early phase of execution when arguments are
parsed and validated — namely, printing different types of help or error text
and sometimes exiting. Those behaviors can be implemented haphazardly or
robustly and well (for example, exiting with a proper status code, emitting
error messages to stderr rather than stdout, or even adding color to error
output). Even when done well, such utilities need to be reimplemented (or
copy-pasted) from script to script, because it is not necessarily worth the
trouble to package them as a separate library.

Argle is fundamentally an argument parser and will not stray too far from
that focus, but it will provide commonly needed functionality related to
argument handling, help text selection and printing, error message creation,
and proper exiting.

#### Composable data conversion and validation

Argument parsing is very much concerned with the problem of data conversion and
validation: for example, a command-line grammar can include validation-adjacent
concepts, such as choices for positionals or option parameters.

Argle will not attempt to become a data conversion and validation library --
that falls beyond the scope of the project. But Opts (and possibly Variants)
will have `convert` and `validate` attributes that can be set to one or more
callables. That approach is not a revolutionary idea, of course, but it is an
arrangement well-suited to easy composition of functionality that the user
might already have at-hand, either from Python itself (`int`, `float`,
`re.compile`, `os.path.isdir`, and so forth), from user-written functions or
classes, and from third-party libraries.

#### Convenient dispatching

Just as argument parsing is closely linked to conversion and validation, its
ultimate purpose is dispatch: most command-line scripts take arguments, execute
one or more functions in response, and then exit.

Argle will include convenient mechanisms to do that type of thing. One
involves the concept of usage variants. As already discussed, variants provide
a powerful means of expressing a command-line grammar and conveying its usage
text. But variants also work well as a dispatch device. Both Opts and Variants
can be configured with one or more dispatch functions, which will be called
with the parsed result, along with any other args/kwargs the user specifies.

#### Readable usage text, via symbolic grouping

As illustrated in a few of the examples above, a program's usage text can be
made more readable and helpful to end-users by condensing groups of options (or
groups of choices) with symbolic names. Such techniques are sometimes seen in
command-line programs with large numbers of options — so large than an
exhaustive listing in the usage text actively undermines usability because it
overwhelms user attention and patience. For example, this simplified snippet of
usage text from `git diff` illustrates the technique.

```
git diff [options] [<commit>] [<path>...]
git diff [options] --cached [<commit>] [<path>...]
```

Because Argle treats groups as first-class citizens in command-line grammar,
and because it will also offer flexible query/configuration APIs allowing
developers to organize options into meaningful arrangements with symbolic
names, developers working on larger scripts (or really any script that could
benefits from such devices) will have flexible mechanisms to generate effective
usage text that actually helps end-users rather than exhaustively "correct"
usage text churned out by a rigid algorithm.

#### Flexible help text, without API burden

Most command-line programs are sufficiently documented simply by listing all
arguments and options, each with a line of help text. Sometimes, however, a
different approach works better, such as organizing options into labeled
sections or simply interspersing blocks of text or sub-headings in between
various groupings of the listed options. Argparse mostly supports those needs
via argument groups — even more API to learn.

Because Argle configuration rests on a textual foundation, providing users
with more flexibility and control over the structuring of help text is easy to
accommodate. To illustrate, consider [Example 4](#example-4) (the wrangle
script) and imagine that the developer wanted to organize the help text by
subcommand, with various chunks of literal text and sub-headings mixed in. That
can probably be achieved with argparse using multiple argument groups per
subparser, but most developers would not bother with the hassle. With Argle,
developers will be able to directly type what is wanted (provided that a few
simple syntax rules are followed). Here is an illustration of what the grep
section of that help text might look like. Admittedly, this presentation is too
elaborate for the script at hand, but the main point is just to illustrate the
ease of organizing help text as needed.

```
    ```
    The grep command emits input lines matching (or not
    matching) the regular expression.

    Positionals:
    ```

        <rgx> : Python regular expression
        <path> : Path(s) to input

    ```
    Search options:
    ```

        -i --ignore-case : Ignore case
        -v --invert-match : Select non-matching lines
        -m --max-count <n> : Stop searching after N matches

    ```
    Output options:
    ```

        -C --context <n> : Print N lines of before/after context
        --color <> : Highlight matching text
```

Finally, to reiterate a point noted above, the configuration syntax is not
primarily literal help text: for example, the blocks of regular text (marked by
triple back-quotes above) will still be paragraph-wrapped to proper width by
Argle, while preserving the intended indentation level. And of course, that
wrapping behavior can be turned off globally, by section, or at the level of
individual text blocks, if needed.

#### More helpful help, via high-precedence Opts

Most users of command-line programs have had the experience of assembling a
fairly large command line of positionals and options only to be greeted by a
usage error message. What happens next? Ideally, the user would hit the up
arrow to recall the shell command and simply add `--help` to the end of the
command line. But most argument parsers, including argparse, insist on griping
rather than helping. Instead of printing relevant help (which should be easy to
support since `'--help' in sys.argv` is true), they doggedly report the same
usage error.

Argle will address that issue via a mechanism call high-precedence options:
if a high-precedence option is present among the arguments, its dispatch
behavior will be triggered. Every Opt can have its dispatch attribute set with
one or more callables that will be invoked when the option is seen. Normally,
dispatch occurs only after a successful parse. But if such configuration is
combined with a high-precedence setting for an Opt, its dispatch functions are
called even in the face of end-user error. This feature is envisioned mainly
for help-related scenarios, but it is not limited to any specific use case.

#### Dynamically hidden Opts

Sometimes the development or debugging process can be helped by having the
ability to include hidden Opts, meaning that they work but are never mentioned
in the usage or help text. A related need is for Opts that apply only under
specific conditions that must be determined at runtime. Although the latter is
achievable via argparse — just wrap parts of the argparse setup code in the
needed conditional logic — Argle will support such behaviors via simple API
configurations.

#### Relaxed parsing modes

Existing libraries either ignore or support only small number of parsing modes.
Argparse, for example, has long supported a [parse-known
mode][py_argparse_known] and in Python 3.7 it added a [parse-intermixed
mode][py_argparse_intermixed], which allows positionals and options to be
intermixed a bit more flexibly on the command line.

Standard argument parsing in Argle will be similar to the flexibility
exhibited by the argparse intermixed mode. That behavior is basically the
logical result of applying the core concepts defining the grammar syntax, along
with a default greedy policy as it relates to parsing and the interpretation of
the syntax itself.

In addition, Argle will support a feature that allows the user to create a
set of related parsing modes that relax one or more requirements. These modes
can be combined as needed.

- Allow-unknown: similar to parse-known behavior in argparse.

- Allow-unconverted: overlook data-conversion problems.

- Allow-unvalidated: overlook data-validation problems.

The intended use case for relaxed parsing is either to parse the known part of
the input and leave the rest to be handled differently, or to parse as much of
the input as possible (even in the face of some end-user errors) in order to
glean more information about end-user intent, perhaps with an eye toward
providing more specific help.

#### No-configuration parsing

Argle will support no-configuration parsing that will parse any input based
on standard rules. The purpose is to support low-stakes or temporary scripts
that could benefit from a few command-line options, but are not important
enough to warrant much configuration work.

In addition to the default no-config parsing, demonstrated in the introduction,
the library will include a simple mechanism to achieve a few different flavors
of almost-no-config parsing. Those flavors relate to the number of parameters
that options will bind to. By default, no-config parsing is greedy, both for
consistency with the rest of the library and also because greedy binding
provides the most flexibility to the end-user. That parameter-binding behavior
can be configured with a quantifier to achieve different results.

```python
Parser()                # Default: greedy.
Parser(noconf = '0')    # Flag style.
Parser(noconf = '1')    # Key-value style.
Parser(noconf = '2,')   # 2+ parameters.
```

Those examples blur the line between config and no-config, of course, and the
last two violate the spirit of no-config by imposing some validation
requirements on the arguments. But they are consistent with the spirit of
Argle, which is to make it easy to parse arguments under a variety of
situations with minimal hassle.

#### Good cooperation with configuration files and environment variables

Some command-line programs are substantial enough that developers want to allow
users to declare some preferences in configuration files. The typical
relationship between preferences and argument parsing is in the area of default
setting:

- Persistent settings in a configuration file (possibly adjusted based on
  environment variables).

- Just-in-time settings from the command-line arguments. These override
  preferences.

That order of operations implies that the data from preferences are mainly used
to dynamically influence the default values for Opts. Additionally, when an Opt
acquires an alternative default value from an upstream source, its status can
change from being required on the command line to optional.

Argle will not try to support direct integration with configuration parsing
libraries: the universe of config files types and config parsing libraries is
too large for that.

Instead, Argle will allow users to combine configuration data and
command-line arguments with minimal hassle. There are two key issues here:

- A convenient mechanism to take preferences into account during argument
  parsing and when assembling the ultimate `Result` containing the parsed data.

- For more complex scenarios, the ability to report back to the user where all
  of the parsed data values came from (command-line arguments supplied by the
  end-user, preferences settings from the end-user, or defaults configured into
  the Parser).

The API details for this behavior are still under consideration, but this
example illustrates one approach.

```python
from argle import Parser, defkeys
import os

# User loads their own prefs.
prefs = load_prefs(...)

# User configures an Argle Parser in the usual way.
p = Parser(...)

# User applies the prefs to the configured Parser.
p.apply_defaults(prefs)

# User parses arguments and gets:
# (1) A Result of the parsed data (as usual).
# (2) A data structure that can report data provenance (for complex cases).
opts, sources = p.parse(ARGUMENTS, with_sources = True)
```

--------

[docopt_url]: http://docopt.org/
[docopt_vid]: https://www.youtube.com/watch?v=pXhcPJK5cMc
[getopt_declare]: https://metacpan.org/pod/Getopt::Declare
[getopt_euclid]: https://metacpan.org/pod/Getopt::Euclid
[getopt_long_desc]: https://metacpan.org/pod/Getopt::Long::Descriptive
[grammar_ex01]: https://stackoverflow.com/questions/18025646
[grammar_ex02]: http://bugs.python.org/issue10984
[grammar_ex03]: https://stackoverflow.com/questions/4466197
[grammar_ex04]: https://stackoverflow.com/questions/25626109
[grammar_ex05]: http://bugs.python.org/issue11588
[grammar_ex06]: https://stackoverflow.com/questions/11455218
[grammar_ex07]: http://bugs.python.org/issue10984
[grammar_ex08]: https://stackoverflow.com/questions/27258173
[grammar_ex09]: https://stackoverflow.com/questions/4692556
[grammar_ex10]: https://stackoverflow.com/questions/5257403
[grammar_ex11]: https://stackoverflow.com/questions/27681718
[grammar_ex12]: https://stackoverflow.com/questions/19114652
[grammar_ex13]: https://stackoverflow.com/questions/62524681
[grammar_ex14]: https://stackoverflow.com/questions/28660992
[grammar_ex15]: https://stackoverflow.com/questions/4194948
[grammar_ex16]: https://bugs.python.org/issue11354
[py_argparse]: https://docs.python.org/3/library/argparse.html
[py_argparse_intermixed]: https://docs.python.org/3/library/argparse.html#intermixed-parsing
[py_argparse_known]: https://docs.python.org/3/library/argparse.html#partial-parsing
[py_bugs]: https://bugs.python.org/
[py_optparse]: https://docs.python.org/3/library/optparse.html
[pypi_argle]: https://pypi.org/project/argle/
[rb_optparse]: https://ruby-doc.org/stdlib-3.0.1/libdoc/optparse/rdoc/OptionParser.html
[stack_home]: https://stackoverflow.com/

