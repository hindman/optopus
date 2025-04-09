
'''
See the optopus implementation for notes.
'''

####
# Click.
####

import click

@click.group()
@click.version_option()
def cli():
    """Naval Fate.

    This is the docopt example adopted to Click but with some actual
    commands implemented and not just the empty parsing which really
    is not all that interesting.
    """

@cli.group()
def ship():
    """Manages ships."""

@ship.command("new")
@click.argument("name")
def ship_new(name):
    """Creates a new ship."""
    click.echo(f"Created ship {name}")

@ship.command("move")
@click.argument("ship")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option("--speed", metavar="KN", default=10, help="Speed in knots.")
def ship_move(ship, x, y, speed):
    """Moves SHIP to the new location X,Y."""
    click.echo(f"Moving ship {ship} to {x},{y} with speed {speed}")

@ship.command("shoot")
@click.argument("ship")
@click.argument("x", type=float)
@click.argument("y", type=float)
def ship_shoot(ship, x, y):
    """Makes SHIP fire to X,Y."""
    click.echo(f"Ship {ship} fires to {x},{y}")

@cli.group("mine")
def mine():
    """Manages mines."""

@mine.command("set")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option(
    "ty",
    "--moored",
    flag_value="moored",
    default=True,
    help="Moored (anchored) mine. Default.",
)
@click.option("ty", "--drifting", flag_value="drifting", help="Drifting mine.")
def mine_set(x, y, ty):
    """Sets a mine at a specific coordinate."""
    click.echo(f"Set {ty} mine at {x},{y}")

@mine.command("remove")
@click.argument("x", type=float)
@click.argument("y", type=float)
def mine_remove(x, y):
    """Removes a mine at a specific coordinate."""
    click.echo(f"Removed mine at {x},{y}")

if __name__ == '__main__':
    cli()

####
# Click help texts.
####

'''

naval-fate --help

    Usage: naval-fate [OPTIONS] COMMAND [ARGS]...

      Naval Fate.

      This is the docopt example adopted to Click but with some actual commands
      implemented and not just the empty parsing which really is not all that
      interesting.

    Options:
      --version  Show the version and exit.
      --help     Show this message and exit.

    Commands:
      mine  Manages mines.
      ship  Manages ships.

naval-fate mine --help

    Usage: naval-fate mine [OPTIONS] COMMAND [ARGS]...

      Manages mines.

    Options:
      --help  Show this message and exit.

    Commands:
      remove  Removes a mine at a specific coordinate.
      set     Sets a mine at a specific coordinate.

naval-fate mine remove --help

    Usage: naval-fate mine remove [OPTIONS] X Y

      Removes a mine at a specific coordinate.

    Options:
      --help  Show this message and exit.

naval-fate mine set --help

    Usage: naval-fate mine set [OPTIONS] X Y

      Sets a mine at a specific coordinate.

    Options:
      --moored    Moored (anchored) mine. Default.
      --drifting  Drifting mine.
      --help      Show this message and exit.

naval-fate ship --help

    Usage: naval-fate ship [OPTIONS] COMMAND [ARGS]...

      Manages ships.

    Options:
      --help  Show this message and exit.

    Commands:
      move   Moves SHIP to the new location X,Y.
      new    Creates a new ship.
      shoot  Makes SHIP fire to X,Y.

naval-fate ship move --help

    Usage: naval-fate ship move [OPTIONS] SHIP X Y

      Moves SHIP to the new location X,Y.

    Options:
      --speed KN  Speed in knots.
      --help      Show this message and exit.

naval-fate ship move new --help

    Usage: naval-fate ship move [OPTIONS] SHIP X Y

      Moves SHIP to the new location X,Y.

    Options:
      --speed KN  Speed in knots.
      --help      Show this message and exit.

naval-fate ship move new shoot --help

    Usage: naval-fate ship move [OPTIONS] SHIP X Y

      Moves SHIP to the new location X,Y.

    Options:
      --speed KN  Speed in knots.
      --help      Show this message and exit.

'''

