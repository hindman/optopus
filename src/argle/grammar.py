
'''


'''

####
# Imports.
####

from dataclasses import dataclass, field, replace as clone
from functools import wraps
from typing import Union

from short_con import cons, constants

from .constants import Chars, Pmodes
from .errors import SpecParseError, ErrKinds, ErrMsgs
from .regex_lexer import RegexLexer
from .tokens import Token, TokDefs
from .utils import get, distilled

####
# Data classes: TreeElem and WalkElem.
####

TreeElemKinds = cons(
    'list',
    'tuple',
    'dict',
    'elem',
)

WalkElemKinds = cons(
    'elem',
    'elem_close',
    'list_open',
    'list_close',
)

@dataclass
class WalkElem:
    level: int
    kind: str = None
    is_end: bool = False
    attr: str = None
    val: object = None

class TreeElem:

    WALKABLE = []

    def traverse(self, include_closing = False):
        # Yields a WalkElem for each TreeElem, in DFS-order.

        stack = [(self, 0, None)]

        while stack:
            e, level, attr = stack.pop()
            yield WalkElem(
                level = level,
                kind = WalkElemKinds.elem,
                attr = attr,
                val = e,
            )

            for attr in e.WALKABLE:
                child = getattr(e, attr, None)
                if isinstance(child, list):
                    if include_closing:
                        yield WalkElem(
                            level = level,
                            kind = WalkElemKinds.list_open,
                            attr = attr,
                        )
                    for c in child:
                        stack.append((c, level + 1, None))
                    if include_closing:
                        yield WalkElem(
                            level = level,
                            kind = WalkElemKinds.list_close,
                        )
                elif child:
                    stack.append((child, level + 1, attr))

            if include_closing:
                yield WalkElem(
                    level = level,
                    kind = WalkElemKinds.elem_close,
                )

    def walk(self, level = 0, attr = None):

        # The elem itself: start.
        we_self = WalkElem(
            level = level,
            kind = TreeElemKinds.elem,
            attr = attr,
            val = self,
        )
        yield we_self

        # Categorize the attributes based on walkability.
        walkability = {True: [], False: []}
        for attr in self.__dict__:
            walkability[attr in self.WALKABLE].append(attr)

        # Non-walkable attributes: yield WalkElem for each.
        for attr in walkability[False]:
            val = getattr(self, attr)
            yield WalkElem(
                level = level + 1,
                attr = attr,
                val = val,
                kind = None,
            )

        # Walkable attributes.
        for attr in walkability[True]:
            val = getattr(self, attr)
            if isinstance(val, list):
                # If val is a list, yield WalkElem(s) for the following:
                # - list-start
                # - yield from a walk of each list item
                # - list-end
                we_seq = WalkElem(
                    level = level + 1,
                    attr = attr,
                    val = val,
                    kind = TreeElemKinds.list,
                )
                yield we_seq
                for e in val:
                    yield from e.walk(level + 2)
                yield clone(we_seq, is_end = True)

            elif val:
                # Otherwise, yield from a walk of the val.
                yield from val.walk(level + 1, attr = attr)

        # The elem itself: end.
        yield clone(we_self, is_end = True)

    def walk_elems(self, *types):
        types = tuple(types or [TreeElem])
        for we in self.walk():
            val = we.val
            emit = (
                we.kind == TreeElemKinds.elem and
                isinstance(val, types) and
                not we.is_end
            )
            if emit:
                yield we.val

    '''

    - Algorithm:

        - Get a WalkElem
        - E = we.val
        - WL = WalkElem.level

        - E itself:
            - no-attr:
                - level = WL * 2
            - has-attr:
                - level = WL * 2 - 1

        - Organize E.attrs into 3 groups:
            - non-walkable
            - walkable-non-list
            - walkable-list

        - non-walkable:
            - level = WL * 2 + 1

        - walkable-non-list:
            - do nothing
            - handled when the elem is encountered later

        - walkable-list:
            - attr + open-bracket
            - ...
            - close-bracket

    SpecAST(                                      | SpecAST, 0    | 0
      elems = [                                   | .             | 1
        OptSpec(                                  | OptSpec, 1    | 2
          scope = None,                           | .             | 3
          text = 'Python regular expression',     | .             | 3
          token = Token(kind='angle_open'),       | .             | 3
          opt = Positional(                       | Positional, 2 | 3
            name = 'rgx',                         | .             | 4
            nargs = None,                         | .             | 4
            elems = [                             | .             | 4
        OptSpec(                                  | OptSpec, 1    | etc
          scope = None,                           | .             | .
          text = 'Path(s) to input',              | .             | .
          token = Token(kind='brack_open'),       | .             | .
          opt = Group(                            | Group, 2      | .
            name = None,                          | .             | .
            ntimes = Quantifier(m=1, n=1),        | .             | .
            required = False,                     | .             | .
            elems = [                             | .             | .
              Positional(                         | Positional, 3 | .
                name = 'path',                    | .             | .
                nargs = Quantifier(m=1, n=None),  | .             | .
                elems = [                         | .             | .
        OptSpec(                                  | OptSpec, 1    | .
          scope = None,                           | .             | .
          text = 'Ignore case',                   | .             | .
          token = Token(kind='brack_open'),       | .             | .
          opt = Group(                            | Group, 2      | .
            name = None,                          | .             | .
            ntimes = Quantifier(m=1, n=1),        | .             | .
            required = False,                     | .             | .
            elems = [                             | .             | .
              Option(                             | Option, 3     | .
                name = 'ignore-case',             | .             | .
                nargs = None,                     | .             | .
                ntimes = None,                    | .             | .
                aliases = [BareOption(name='i')], | .             | .
                elems = [                         | .             | .
        OptSpec(                                  | OptSpec, 1    | .
          scope = None,                           | .             | .
          text = 'Select non-matching lines',     | .             | .
          token = Token(kind='brack_open'),       | .             | .
          opt = Group(                            | Group, 2      | .
            name = None,                          | .             | .
            ntimes = Quantifier(m=1, n=1),        | .             | .
            required = False,                     | .             | .
            elems = [                             | .             | .
              Option(                             | Option, 3     | .
                name = 'invert-match',            | .             | .
                nargs = None,                     | .             | .
                ntimes = None,                    | .             | .
                aliases = [BareOption(name='v')], | .             | .
                elems = [                         | .             | .

    '''


    def pretty(self, indent_size = 4, omit_end = False):
        lines = []
        for we in self.walk():
            indent = Chars.space * indent_size * we.level
            attr_eq = f'{we.attr} = ' if we.attr else ''

            if we.kind == TreeElemKinds.elem:
                if we.is_end:
                    if not omit_end:
                        lines.append(f'{indent}),')
                else:
                    cls_name = we.val.__class__.__name__
                    lines.append(f'{indent}{attr_eq}{cls_name}(')
            elif we.kind == TreeElemKinds.list:
                if we.is_end:
                    if not omit_end:
                        lines.append(f'{indent}],')
                else:
                    lines.append(f'{indent}{attr_eq}[')
            else:
                if isinstance(we.val, Token):
                    val_str = we.val.brief
                else:
                    val_str = f'{we.val!r}'
                lines.append(f'{indent}{attr_eq}{val_str},')

        return Chars.newline.join(lines)

####
# Data classes: GrammarElem.
####

VariantElem = Union['Opt', 'Group', 'Alternative']

@dataclass
class GrammarElem(TreeElem):

    WALKABLE = [
        'variants',
        'elems',
        'parameters',
        'choices',
    ]

    def without_degen_group(self):
        # Must be Group.
        if not isinstance(self, Group):
            return self

        # Group.ntimes must be singular.
        if self.ntimes and not self.ntimes.is_singular:
            return self

        # Must have only 1 child elem.
        if len(self.elems) != 1:
            return self

        # The child must be Group or Option.
        # If so, we will be returning the child, not self.
        child = self.elems[0]
        if not isinstance(child, (Group, Option)):
            return self

        # If the Group is not required, apply that status
        # to the the child's ntimes.
        q = self.ntimes
        if q and q.is_optional:
            if child.ntimes:
                child.ntimes.required = False
            else:
                child.ntimes = Quantifier(m = 1, n = 1, required = False)

        # Return the child -- after applying the process recursively.
        return child.without_degen_group()

    @property
    def pp(self):
        return 'TODO'

@dataclass
class Grammar(GrammarElem):
    variants: list['Variant']

@dataclass
class Variant(GrammarElem):
    name: str
    elems: list[VariantElem]

@dataclass
class Group(GrammarElem):
    name: str = None
    dest: str = None
    elems: list[VariantElem] = field(default_factory = list)
    ntimes: 'Quantifier' = None
    validate: callable = None
    mutex: bool = False

@dataclass
class Alternative(GrammarElem):
    elems: list[VariantElem]

@dataclass
class Opt(GrammarElem):
    pass

@dataclass
class VarInput(GrammarElem):
    pass

@dataclass
class Choice(GrammarElem):
    text: str
    help_text: str = None

@dataclass
class Positional(Opt, VarInput):
    name: str
    dest: str = None
    help_text: str = None
    nargs: 'Quantifier' = None
    choices: list[Choice] = field(default_factory = list)
    hide: bool = False
    anchor: bool = False
    dispatch: list[callable] = field(default_factory = list)
    default: object = None
    factory: callable = None
    convert: callable = None
    validate: callable = None

@dataclass
class Option(Opt):
    name: str
    dest: str = None
    help_text: str = None
    nargs: 'Quantifier' = None
    ntimes: 'Quantifier' = None
    parameters: list[Union['Parameter', Group]] = field(default_factory = list)
    aliases: list[str] = field(default_factory = list)
    hide: bool = False
    anchor: bool = False
    dispatch: list[callable] = None
    priority: bool = False
    negaters: list['Option'] = None

@dataclass
class Alias(GrammarElem):
    name: str

@dataclass
class Literal(Opt):
    text: str

    # Always true.
    anchor = True

@dataclass
class Parameter(VarInput):
    name: str = None
    dest: str = None
    help_text: str = None
    nargs: 'Quantifier' = None
    choices: list[Choice] = field(default_factory = list)
    default: object = None
    factory: callable = None
    convert: callable = None
    validate: callable = None

@dataclass
class Quantifier(GrammarElem):
    m: int = None
    n: int = None
    required: bool = True
    greedy: bool = True

    @property
    def is_singular(self):
        return self.m <= 1 and self.n == 1

    @property
    def is_optional(self):
        return self.m == 0 or not self.required

####
# Data classes: SectionElem.
####

@dataclass
class SectionElem:
    pass

@dataclass
class Section(SectionElem):
    name: str
    title: str
    elems: list[SectionElem]

@dataclass
class Heading(SectionElem):
    title: str

@dataclass
class BlockQuote(SectionElem):
    text: str
    comment: bool
    no_wrap: bool
    token_indent: int

@dataclass
class OptSpec(SectionElem):
    # TODO: not sure what this needs.
    pass

GrammarElems = constants({
    name : obj
    for name, obj in globals().items()
    if (
        isinstance(obj, type) and
        issubclass(obj, (GrammarElem, SectionElem))
    )
})

