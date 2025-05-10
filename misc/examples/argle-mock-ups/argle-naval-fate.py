#! /usr/bin/env python

'''

naval-fate: Argle vs Docopt vs Click.

Configuration of the parser:

    - Docopt and Argle are both compact and intuitive:
        - Docopt is slightly better on that front.
        - But at the cost having almost no features beyond the core.
        - The small increment of added complexity in the Argle configuration
          exists precisely to rememdy a core weakness of Docopt: it's poor
          structuring of returned data.

    - Click configuration:
        - Much more verbose and repetitive.
        - A sea of API calls.
        - The code provides no easy way to see the program's usage at a glance.
        - The model is not readily amenable to putting the parser configuration
          in a data structure. Instead, the configuration must be spread across
          separate decorators.

Help text:

    - Readable and intutive:
        - Yes: Argle and Docopt.
        - No: Click.
        - Click's help is convoluted:
            - User never gets a complete view.
            - Must invoke --help in several ways to see everything.

    - User control over structure, content, details:
        - High: Argle.
        - Moderately high, but with a hard cap: Docopt.
        - Very little: Click.

    - Dynamic with terminal:
        - Yes: Argle and Click.
        - No: Docopt: it's static.

    - Only Argle gives both:
        - High degree of user control [Argle, Docopt].
        - Delegation of help-text convention adherence [Argle, Click].

Parsed data:

    - Docopt:
        - Strange, hyper-flatted data.
        - User would have to convert it to something usable.

    - Click:
        - Reasonable.
        - But hyper-localized to the values relevant to the current command.

    - Argle:
        - Usable and holistic data out of the gate.

Size: 
    108% vs Docopt
    44% vs Click

Help size:
    127% vs Docopt
    26% vs Click

'''

####
# Argle.
####

SPEC = '''
<weapon=ship>        <action=new>        <name>...
<weapon=ship> <name> <action=move>       <x> <y> [--speed <kn>]
<weapon=ship>        <action=shoot>      <x> <y>
<weapon=mine>        <action=set|remove> <x> <y> [--moored | --drifting]

<name>       : Ship name
<x>          : X coordinate
<y>          : Y coordinate
--speed <kn> : Speed in knots [default: 10]
--moored     : Moored (anchored) mine
--drifting   : Drifting mine
'''

from argle import Parser

p = Parser(SPEC, version = '2.0')
p.config_help_text(options_summary = False)
opts = p.parse()

####
# Argle help text.
####

'''
Usage:
  naval-fate ship new <name>...
  naval-fate ship <name> move <x> <y> [--speed <kn>]
  naval-fate ship shoot <x> <y>
  naval-fate mine <set|remove> <x> <y> [--moored | --drifting]

Arguments:
  <name>                 Ship name
  <x>                    X coordinate
  <y>                    Y coordinate
  --speed <kn>           Speed in knots [default: 10]
  --moored               Moored (anchored) mine
  --drifting             Drifting mine
  --version              Print program version and exit
  --help, -h             Print help text and exit
'''

