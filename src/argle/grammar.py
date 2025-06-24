
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

    def traverse(self, *wanted_types, level = 0, attr = None, structured = False):
        #
        # Yields a WalkElem for self and for all of its TreeElem children, in
        # DFS-order.
        #
        # - wanted_types: request only specific types of TreeElem.
        #
        # - structured: if true, also yields WalkElem to convey list start,
        #   list end, and elem end. For this use case, the logic to compute level
        #   for recursive calls is different.
        #
        # - attr: relevent only for some recursive calls.
        #
        # This method can be used reliably in contexts where the parent TreeElem
        # is modified by the caller during traversal. This works because none
        # of the parent's WALKABLE attributes holding children are checked until
        # after the WalkElem for self has already been yielded and mutated.
        #

        # Setup.
        wanted_types = wanted_types or (TreeElem,)
        WEK = WalkElemKinds

        # Helper to calculate level, either for a WalkElem or a recursive call.
        def calc_level(d1, d2):
            return level + (d2 if structured else (d1 or 0))

        # Helpers to yield a WalkElem conditionally.
        def elem_yielder(**kws):
            if isinstance(kws.get('val'), wanted_types):
                yield WalkElem(**kws)

        def structure_yielder(**kws):
            if structured:
                yield WalkElem(**kws)

        # A WalkElem for self.
        yield from elem_yielder(
            level = calc_level(0, 0),
            kind = WEK.elem,
            attr = attr,
            val = self,
        )

        # Process its WALKABLE attributes.
        for attr in self.WALKABLE:
            children = getattr(self, attr, None)
            if isinstance(children, list):
                # If the WALKABLE attribute holds a list of chidren:
                # - Yield WalkElem for list open.
                # - Yield from a recursive call of each child.
                # - Yield WalkElem for list close.
                yield from structure_yielder(
                    level = calc_level(None, 1),
                    kind = WEK.list_open,
                    attr = attr,
                )
                for c in children:
                    yield from c.traverse(
                        *wanted_types,
                        level = calc_level(1, 2),
                        structured = structured,
                    )
                yield from structure_yielder(
                    level = calc_level(None, 1),
                    kind = WEK.list_close,
                )
            elif children is not None:
                # If the WALKABLE attributes hold a single child,
                # yield from a recursive call on it.
                c = children
                yield from c.traverse(
                    *wanted_types,
                    level = calc_level(1, 1),
                    attr = attr,
                    structured = structured,
                )

        # Yield WalkElem for list close.
        yield from structure_yielder(
            level = calc_level(None, 0),
            kind = WEK.elem_close,
        )

    def pretty(self, indent_size = 4, omit_closing = False):
        # Return a pretty-printable blob of text to represent
        # the structure of a TreeElem and its children.

        # Setup: lines, one level of indentation, etc.
        lines = []
        indent = Chars.space * indent_size
        WEK = WalkElemKinds

        # Traverse the TreeElem so that we get both the elements
        # and other structural information.
        for we in self.traverse(structured = True):
            # Setup for the current WalkElem.
            level_indent = indent * we.level
            attr_eq = f'{we.attr} = ' if we.attr else ''

            # Handle each kind of WalkElem.
            if we.kind == WEK.elem:
                # A line for the TreeElem class.
                elem = we.val
                cls_name = elem.__class__.__name__
                lines.append(f'{level_indent}{attr_eq}{cls_name}(')

                # One line per non-WALKABLE attribute.
                for a, val in elem.__dict__.items():
                    if a not in elem.WALKABLE:
                        if isinstance(val, Token):
                            val_str = val.brief
                        else:
                            val_str = f'{val!r}'
                        lines.append(f'{level_indent + indent}{a} = {val_str},')

            elif we.kind == WEK.list_open:
                # List open line.
                lines.append(f'{level_indent}{attr_eq}[')

            elif not omit_closing:
                # List or elem closing lines.
                if we.kind == WEK.elem_close:
                    lines.append(f'{level_indent}),')
                elif we.kind == WEK.list_close:
                    lines.append(f'{level_indent}],')

        # Return as text.
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
        # First we decide whether self is a degenerate Group.

        # Must be Group.
        if not isinstance(self, Group):
            return self

        # Must have only 1 child elem.
        if len(self.elems) != 1:
            return self

        # The child must be Group or Option.
        #
        # The other things a Group can hold (Alternative, Positional, Literal)
        # lack ntimes. Group cannot be treated as degenerate in such cases.
        child = self.elems[0]
        if not isinstance(child, (Group, Option)):
            return self

        # Get or create quantifiers for the parent and the child.
        qp = self.ntimes or Quantifier(m = 1, n = 1)
        qc = self.ntimes or Quantifier(m = 1, n = 1)

        # At least one of the ntimes-quantifiers must be singular.
        # If not, the parent Group cannot be dropped as degenerate.
        if not (qp.is_singular or qc.is_singular):
            return self

        # TODO: merge qp and qc.

        # TODO: this code uses the old (incorrect) logic.
        #
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

