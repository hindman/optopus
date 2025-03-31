#! /usr/bin/env python

# The docopt naval-fate example

ORIGINAL = '''
Naval Fate.

Usage:
  naval-fate ship new <name>...
  naval-fate ship <name> move <x> <y> [--speed=<kn>]
  naval-fate ship shoot <x> <y>
  naval-fate mine (set|remove) <x> <y> [--moored|--drifting]
  naval-fate -h | --help
  naval-fate --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.

'''

SPEC = '''

<weapon=ship>        <action=new>        <name>...
<weapon=ship> <name> <action=move>       <x> <y> [--speed <kn>]
<weapon=ship>        <action=shoot>      <x> <y>
<weapon=mine>        <action=set|remove> <x> <y> [--moored | --drifting]

'''

