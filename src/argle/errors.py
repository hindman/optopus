
from kwexception import Kwexception
from short_con import cons

ErrKinds = cons(
    incomplete_spec_parse = 'Failed to parse the full spec',
    empty_variant = 'Variant cannot be empty',
    unnamed_positional = 'Positional requires a name: <>',
    assign_without_choices = 'Var-input assignment without choices: eg <foo=>',
    assign_without_name = 'Var-input assignment without a name: eg, <=x|y>',
    unclosed_bracketed_expression = 'Failed to reach closing bracket of bracketed expression',
    empty_group = 'Group cannot be empty',
)

class ArgleError(Kwexception):

    def isa(self, *xs):
        return any(self.error_kind == x.error_kind for x in xs)

