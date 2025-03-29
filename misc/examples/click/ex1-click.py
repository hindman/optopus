import click

@click.command()
@click.argument("fubb", required = True)
@click.argument("blort", required = False)
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

class CustomCommand(click.Command):

    def format_usage(self, ctx, formatter):
        super().format_usage(ctx, formatter)
        options = " ".join(
            opt.opts[0]
            for opt in self.params
            if isinstance(opt, click.Option)
        )
        formatter.write(formatter.getvalue().replace("[OPTIONS]", options))

# @click.command()
@click.command(cls = CustomCommand)
@click.argument('x')
@click.argument('y', required = False)
@click.option('-a', default = 1, help = 'Number of greetings.')
@click.option('-b', help = 'The person to greet.')
def blort(x, y = None, a = None, b = None):
    '''
    Prints [X, Y, A, B].
    '''
    print([x, y, a, b])

if __name__ == '__main__':
    # hello()
    blort()

