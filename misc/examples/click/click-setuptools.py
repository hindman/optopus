import click

'''

From Click documentation:
    - An example when discussing Multi Command Chaining

The generated help text:

    Usage: ex3-setuptools.py [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

    Options:
      --help  Show this message and exit.

    Commands:
      bdist_wheel
      sdist

'''

@click.group(chain=True)
def cli():
    pass

@cli.command('sdist')
def sdist():
    click.echo('sdist called')

@cli.command('bdist_wheel')
def bdist_wheel():
    click.echo('bdist_wheel called')

if __name__ == '__main__':
    cli()

