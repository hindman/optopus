import sys

SPEC = '''

TODO:
    --help
    --version
    prompt

general! : general-options=([--repo-home] [--config] [--verbose])

clone    : general! <command=clone> [--shallow | --deep] [--rev] <src> [<dest>]
commit   : general! <command=commit> [--message] <file>...
copy     : general! <command=copy> [--force] [<src>]... <dest>
delete   : general! <command=delete> [--yes]
setuser  : general! <command=setuser> [--username] [--email] [--password]

```
Repo is a command line tool that showcases how to build complex command line
interfaces with Optopus.

This tool is supposed to look like a distributed version control system to
show how something like this can be structured.

Commands:
```
    <cmd=clone>   : Clones a repository.
    <cmd=commit>  : Commits outstanding changes.
    <cmd=copy>    : Copies files.
    <cmd=delete>  : Deletes a repository.
    <cmd=setuser> : Sets the user credentials.

```
General options:
```
    [--repo-home <path>]     : Changes the repository folder location.
    [--config <key> <value>] : Overrides a config key/value pair.
    [-v --verbose]           : Enables verbose mode.

Command: clone ::

```
This will clone the repository at SRC into the folder DEST.  If DEST is not
provided this will automatically use the last path component of SRC and create
that folder.
```

Arguments:

    

Options:
    --shallow / --deep  Makes a checkout shallow or deep.  Deep by default.
    -r, --rev TEXT      Clone a specific revision instead of HEAD.
    --help              Show this message and exit.

====================================

Commits outstanding changes.

Commit changes to the given files into the repository.  You will need to
"repo push" to push up your changes to other repositories.

If a list of files is omitted, all changes reported by "repo status" will be
committed.

Options:
    -m, --message TEXT  The commit message.  If provided multiple times
                        each argument gets converted into a new line.

====================================

Usage: ex4-repo.py copy [OPTIONS] [SRC]... DST

Copies one or multiple files to a new location.  This copies all files from
SRC to DST.

Options:
    --force  forcibly copy over an existing managed file

====================================

Deletes a repository.

This will throw away the current repository.

Options:
    --yes   Confirm the action without prompting.

====================================

Sets the user credentials.

This will override the current user config.

Options:
    --username TEXT  The developer's shown username.
    --email TEXT     The developer's email address
    --password TEXT  The login password.

====================================

'''

def main(args):
    print(args)

if __name__ == '__main__':
    main(sys.argv[1:])
    
