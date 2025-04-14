
'''

repo: Optopus vs click.

TODO:

    x Draft SPEC
    x API config

    - Help text

    - Help dispatch:
        - Previous help-dispatch mockup returned a Section.
        - But what about usage-text?
        - eg, subcommand style program might want to return both a Section and
          a Variant, the latter to build usage-test relevant to the Section.

    - Comparison notes.

        - This mockup does not support --yes automatically. Not
          sure Optopus will ever do that.

'''

####
# Optopus.
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
interfaces with Optopus.

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
    [--config <key> <value>]... : Overrides a config key/value pair
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

from optopus import Parser, Path

p = Parser(SPEC, version = '1.0')
p.config_help_text(options_summary = False)

p.config('rev', default = 'HEAD')
p.config('repo_home', default = '.repo', env = True)

p.config('shallow', negaters = 'deep')

p.config('username', 'password', prompt = True)
p.config('email', prompt = 'Enter E-mail')

p.config(dest = dict(file = 'files', src = 'srcs', dst = 'dsts'))
p.config('files', 'srcs', 'dsts', convert = Path)

opts = p.parse()

####
# Optopus help text.
####

'''
Usage:
  repo __

Arguments:
  <foo>                  Foo ...
'''

