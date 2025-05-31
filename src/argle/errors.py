
from kwexception import Kwexception
from short_con import cons, constants

ErrMsgs = cons(
    incomplete_spec_parse = 'Failed to parse the full spec',
    empty_variant = 'Variant cannot be empty',
    unnamed_positional = 'Positional requires a name: <>',
    assign_without_choices = 'Var-input assignment without choices: eg <foo=>',
    assign_without_name = 'Var-input assignment without a name: eg, <=x|y>',
    unclosed_bracketed_expression = 'Failed to reach closing bracket of bracketed expression',
    empty_group = 'Group cannot be empty',
)

ErrKinds = constants(ErrMsgs.keys())

class ArgleError(Kwexception):

    def isa(self, *kinds):
        return self.params['error_kind'] in kinds

class SpecParseError(ArgleError):

    def __str__(self):
        return super().__str__() + self.parse_context

