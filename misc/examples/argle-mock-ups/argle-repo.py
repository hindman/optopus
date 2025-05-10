
'''

repo: Argle vs click.

The problems with click noted in the discussion of the naval-fate comparison
also apply here.

In addition:

    - Argle provides various views of the help text: summary,
      command-specific, and complete.

    - Argle supports nearly all of the extras supplied by the Click API:
        - Automatic --version flag.
        - Negating flags: --shallow vs --deep.
        - Environment variables.
        - Prompted inputs, in various ways.
        - Helper conversion functions.

    - The exceptions:
        - Unlike Click, Argle does not focus on dispatching to the degree
          that click does (because it comes with too high of cost).
        - This mockup does not address whether/how Argle would support a
          confirmation option like --yes (closely related to dispatching).

    - The API and help-text sizes are roughly comparable, but in both cases the
      Argle versions are more directly understandable for the user (writing
      the code) and the end-user (running the program).

Size:
    104%

Help size:
    121%

'''

####
# Argle.
####

SPEC = '''

general! : general-options=([--repo-home] [--config]... [--verbose])

clone   : general! <command=clone> <src> [<dst>] [--shallow | --deep] [--rev]
commit  : general! <command=commit> [<file>]... [--message]
copy    : general! <command=copy> [<src>]... <dst> [--force]
delete  : general! <command=delete> [--yes]
setuser : general! <command=setuser> [--username] [--email] [--password]

```
Repo is a command line tool that showcases how to build complex command line
interfaces with Argle.

This tool is supposed to look like a distributed version control system to
show how something like this can be structured.
```

Commands :::
    <command=clone>   : Clones a repository
    <command=commit>  : Commits outstanding changes
    <command=copy>    : Copies files
    <command=delete>  : Deletes a repository
    <command=setuser> : Sets the user credentials

General options :::
    [--repo-home <path>]        : Changes the repository folder location
    [--config <key> <value>]... : Overrides a config key/value pair [repeatable]
    [-v --verbose]              : Enables verbose mode
    [--version]
    [--help]

Command: clone ::

```
This will clone the repository at <src> into the folder <dst>. If <dst> is not
provided this will automatically use the last path component of <src> and create
that folder.
```

    <src>               : Repository source
    [<dst>]             : Directory path in which to put the cloned repo
    [--deep]            : Deep checkout [the default]
    [--shallow]         : Shallow checkout
    [-r --rev <commit>] : Clone a specific revision instead of HEAD

Command: commit ::

```
Commits outstanding changes.

Commit changes to the given files into the repository. You will need to
"repo push" to push up your changes to other repositories.

If a list of files is omitted, all changes reported by "repo status" will be
committed.
```

    [<file>]...              : File path
    [-m --message <text>]... : Commit message [if multiple, joined by newline]

Command: copy ::

```
Copies one or multiple files to a new location. This copies all files from
<src> to <dst>.
```

    [<src>]... : File path
    <dst>      : Directory path of destination
    [--force]  : Forcibly copy over an existing file

Command: delete ::

```
Deletes a repository.

This will throw away the current repository.
```

    [--yes] : Confirm the action without prompting

Command: setuser ::

```
Sets the user credentials.

This will override the current user config.
```

    [--username <user>] : Username
    [--email <address>] : Email address
    [--password <pw>]   : Login password
'''

from argle import Parser, Path

def help_dispatch(opts):
    # Summary help: just usage if no args given.
    ctx = opts('context')
    p = opts('parser')
    if not ctx.args:
        return p.query_one('Usage', kind = Section)

    # Command-specific help: return relevant (Section, Variant).
    cmd = opts.command
    if cmd:
        # If possible return the relevant (Section, Variant).
        s = p.query_one(cmd, kind = Section)
        v = p.query_one(cmd, kind = Variant)
        return (s, v)

    # Otherwise fallback to entire help-text.
    return None

# Create Parser with:
# - Ability to print command-sensitive help-text.
# - Support for --version flag.
p = Parser(SPEC, help = help_dispatch, version = '1.0')

# Usage section will list options explicitly.
p.config_help_text(options_summary = False)

# Defaults.
p.config('rev', default = 'HEAD')
p.config('repo_home', default = '.repo')

# Environment variable as an alternative/upstream input.
# This could have been combined with the repo_home config() call above.
p.config('repo_home', env = True)

# The --deep flag will negate shallow=True.
p.config('shallow', negaters = 'deep')

# Alternative inputs via user prompts:
# - Default.
# - With a custom prompt message.
# - Via getpass().
p.config('username', prompt = True)
p.config('email', prompt = 'Enter E-mail')
p.config('password', password = True)

# For Opts with plural nargs, leave their name singular (as set in SPEC)
# but use a plural dest. Also illustrates how to use config() to set
# one attribute across multiple Opts.
p.config(dest = dict(file = 'files', src = 'srcs', dst = 'dsts'))

# One of the Argle utility convert functions.
p.config('files', 'srcs', 'dsts', convert = Path)

opts = p.parse()

####
# Argle help text.
####

'''
Usage:
  repo [<general-options>] clone <src> [<dst>] [--shallow | --deep]
          [--rev <commit>]
  repo [<general-options>] commit [<file>...] [--message <text>]...
  repo [<general-options>] copy [<src>...] <dst> [--force]
  repo [<general-options>] delete [--yes]
  repo [<general-options>] setuser [--username <user>] [--email <address>]
          [--password <pw>]

Repo is a command line tool that showcases how to build complex command line
interfaces with Argle.

This tool is supposed to look like a distributed version control system to show
how something like this can be structured.

Commands:
  clone                  Clones a repository
  commit                 Commits outstanding changes
  copy                   Copies files
  delete                 Deletes a repository
  setuser                Sets the user credentials

General options:
  --repo-home <path>     Changes the repository folder location
  --config <key> <value> Overrides a config key/value pair [repeatable]
  --verbose, -v          Enables verbose mode
  --version              Prints program version and exits
  --help                 Prints help text and exits

Command: clone:

This will clone the repository at <src> into the folder <dst>. If <dst> is not
provided this will automatically use the last path component of <src> and
create that folder.

Arguments:
  <foo>                  Blah blah
  <src>                  Repository source
  <dst>                  Directory path in which to put the cloned repo
  --deep                 Deep checkout [the default]
  --shallow              Shallow checkout
  --rev <commit>, -r     Clone a specific revision instead of HEAD

Command: commit:

Commits outstanding changes.

Commit changes to the given files into the repository. You will need to "repo
push" to push up your changes to other repositories.

If a list of files is omitted, all changes reported by "repo status" will be
committed.

Arguments:
  <file>                 File path
  -m --message <text>    Commit message [if multiple, joined by newline]

Command: copy:

Copies one or multiple files to a new location. This copies all files from
<src> to <dst>.

Arguments:
  <src>                  File path
  <dst>                  Directory path of destination
  --force                Forcibly copy over an existing file

Command: delete:

Deletes a repository.

This will throw away the current repository.

Arguments:
  --yes                  Confirm the action without prompting

Command: setuser:

Sets the user credentials.

This will override the current user config.

Arguments:
  --username <user>      Username
  --email <address>      Email address
  --password <pw>        Login password
'''

####
# Argle help for one variant/section.
####

'''
Usage:
  repo [<general-options>] commit [<file>...] [--message <text>]...

Command: commit:

Commits outstanding changes.

Commit changes to the given files into the repository. You will need to "repo
push" to push up your changes to other repositories.

If a list of files is omitted, all changes reported by "repo status" will be
committed.

Arguments:
  <file>                 File path
  -m --message <text>    Commit message [if multiple, joined by newline]
'''

