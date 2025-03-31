import click

'''

From Click documentation:
    - An example when discussing Multi Command Chaining

The generated help text:

    Usage: blort [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

    Options:
      --help  Show this message and exit.

    Commands:
      bdist_wheel
      sdist

The Optopus configuration is simultaneously:
    - Simpler configuration.
    - Simpler, and less generic, help text.

    - The spec:

        (sdist | bdist_wheel)...

    - The help text:

        Usage:
          blort (sdist | bdist_wheel)...

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

