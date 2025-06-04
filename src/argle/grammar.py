
####
# Imports.
####

from dataclasses import dataclass, field
from functools import wraps
from typing import Union

from short_con import cons, constants

from .constants import Chars, Pmodes
from .errors import SpecParseError, ErrKinds, ErrMsgs
from .regex_lexer import RegexLexer
from .tokens import Token, TokDefs
from .utils import get, distilled

####
# Data classes: __
####

@dataclass
class GrammarElem:

    @property
    def pp(self):
        return 'TODO'

@dataclass
class Grammar(GrammarElem):
    variants: list['Variant']

@dataclass
class Variant(GrammarElem):
    name: str
    elems: list[Union['Group', 'Opt']]
    ntimes: 'Quantifier'

@dataclass
class Group(GrammarElem):
    name: str
    dest: str
    elems: list[Union['Group', 'Opt']]
    ntimes: 'Quantifier'
    validate: callable
    mutex: bool

@dataclass
class Opt(GrammarElem):
    pass

@dataclass
class Arg(GrammarElem):
    pass

@dataclass
class Choice(GrammarElem):
    text: str

@dataclass
class Positional(Opt):
    name: str
    dest: str
    help_text: str
    arguments: list['Argument']
    nargs: 'Quantifier'
    ntimes: 'Quantifier'
    hide: bool
    anchor: bool
    dispatch: list[callable]

@dataclass
class Option(Opt):
    name: str
    dest: str
    help_text: str
    parameters: list[Union['Parameter', Group]]
    nargs: 'Quantifier'
    ntimes: 'Quantifier'
    hide: bool
    anchor: bool
    dispatch: list[callable]
    aliases: list[str]
    priority: bool
    negaters: list['Option']

@dataclass
class Literal(Opt):
    text: str

    # Always true.
    anchor = True

@dataclass
class Argument(Arg):
    help_text: str
    ntimes: 'Quantifier'
    choices: list[Choice]
    default: object
    factory: callable
    convert: callable
    validate: callable

@dataclass
class Parameter(Arg):
    name: str
    dest: str
    help_text: str
    ntimes: 'Quantifier'
    choices: list[Choice]
    default: object
    factory: callable
    convert: callable
    validate: callable

@dataclass
class Quantifier(Arg):
    m: int = None
    n: int = None
    greedy: bool = True

