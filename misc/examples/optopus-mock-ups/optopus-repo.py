
'''

repo: Optopus vs click.

TODO:

    x Draft SPEC

    - API setup:

        "--repo-home",
        envvar="REPO_HOME",
        default=".repo",

        "--shallow/--deep",
        default=False,

        "--rev", "-r", default="HEAD"

        @click.confirmation_option()   # Done for --yes

        @click.option("--username", prompt=True)

        @click.option("--email", prompt="E-Mail")

        @click.password_option(help="The login password.")

        @click.argument("files", type=click.Path())
        @click.argument("src", type=click.Path())
        @click.argument("dst", type=click.Path())

    - Help text

    - Comparison notes.

'''

####
# Optopus.
####

SPEC = '''

general! : general-options=([--repo-home] [--config]... [--verbose])

clone   : general! <command=clone> <src> [<dest>] [--shallow | --deep] [--rev]
commit  : general! <command=commit> [<file>]... [--message]
copy    : general! <command=copy> [<src>]... <dest> [--force]
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
This will clone the repository at <src> into the folder <dest>. If <dest> is not
provided this will automatically use the last path component of <src> and create
that folder.
```

    <src>               : Repository source
    [<dest>]            : Directory path in which to put the cloned repo
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
<src> to <dest>.
```

    [<src>]... : File path
    <dest>     : Directory path of destination
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

from optopus import Parser

p = Parser(SPEC, version = '1.0')
p.config_help_text(options_summary = False)
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

