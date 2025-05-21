
import io
import pytest

from pathlib import Path

from short_con import cons, constants

from argle.new_grammar import (
    SpecParser,
    TokDefs,
    Grammar,
)

####
# A StringIO you can print directly, without fuss.
####

class Sio(io.StringIO):

    def __str__(self):
        return self.getvalue()

####
# Example specs.
####

SPECS = constants('ex01 ex02 ex03 ex04 ex05 ex06', frozen = False)

SPECS.ex01 = '''
[-i] [-v] <rgx> <path>
'''

SPECS.ex02 = '''
<rgx> : Python regular expression
[<path>...] : Path(s) to input
[-i --ignore-case] : Ignore case
[-v --invert-match] : Select non-matching lines
'''

SPECS.ex03 = '''
<task=grep>   [-i] [-v] [-m] [-C]
              [--color <red|green|blue>]
              <rgx> [<path>...]
<task=sub>    [-i] [-n] <rgx> <rep> [<path>...]
<task=search> [-i] [-g] [-d | -p] <rgx> [<path>...]

<task>             : Task to perform
<task=grep>        : Emit lines matching pattern
<task=sub>         : Search for pattern and replace
<task=search>      : Emit text matching pattern
<rgx>              : Python regular expression
<path>             : Path(s) to input
<rep>              : Replacement text
-i --ignore-case   : Ignore case
-v --invert-match  : Select non-matching lines
-m --max-count <n> : Stop searching after N matches
-C --context <n>   : Print N lines of before/after context
--color <>         : Highlight matching text
-n --nsubs <n>     : N of substitutions
-g --group <n>     : Emit just capture group N [0 for all]
-d --delim <s>     : Delimeter for capture groups [tab]
-p --para          : Emit capture groups one-per-line, paragraph-style
'''

SPECS.ex04 = '''
[-i] [-v]
    <rgx> <path>
[--foo] <blort>
'''

SPECS.ex05 = '''
<rgx> : Python
        regular
        expression
[<path>...] : Path(s) to
              input
[-i --ignore-case] : Ignore case
[-v 
      --invert-match] : Select non-matching
                        lines
'''

SPECS.ex06 = '''
  [-i]? [-v]...
       <rgx> <path>{1,7}?
  [--foo] <blort>?

Positionals needed ::

```
Positionals blorty blorty blort blort
foo bar fubb.
```

    <rgx> : Regular
            expression
    <path> : Path to
             the
             file

Options::

```
Positionals blorty blorty blort blort
foo bar fubb.
```

    -i  : Ignore case
          during search
    -v  : Ivert: emit non-matched
          lines
'''

def test_ex1(tr):
    # [-i] [-v] <rgx> <path>
    spec = SPECS.ex01
    sp = SpecParser(spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp, label = 'ex01')

# @pytest.mark.skip(reason = 'spec-parsing-overhaul')
def test_ex2(tr):
    # <rgx> : Python regular expression
    # [<path>...] : Path(s) to input
    # [-i --ignore-case] : Ignore case
    # [-v --invert-match] : Select non-matching lines
    spec = SPECS.ex02
    sp = SpecParser(spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp, label = 'ex02')

# @pytest.mark.skip(reason = 'spec-parsing-overhaul')
def test_ex3(tr):
    spec = SPECS.ex03
    sp = SpecParser(spec, debug = False)
    g = sp.parse()
    # tr.dump(g.pp, label = 'ex03')

@pytest.mark.skip(reason = 'spec-parsing-overhaul')
def test_examples(tr):

    for exkey, spec in SPECS.items():
        fh = None
        sp = SpecParser(spec, debug = Sio())
        grammar = sp.parse()
        parser_debug = str(sp.debug_fh)

        got_text = '\n'.join([
            '\n# SPEC',
            spec,
            '\n# PARSER_DEBUG',
            parser_debug,
            '\n# GRAMMAR',
            grammar.pp,
            '',
        ])

        paths = example_paths(exkey)

        # Write the text we got.
        write_file(paths.got, got_text)

        # Read the text we expect, if possible.
        # Otherwise, write it for next time.
        if paths.exp.is_file():
            exp_text = read_file(paths.exp)
        else:
            write_file(paths.exp, got_text)
            exp_text = got_text

        # Assert.
        ok = got_text == exp_text
        assert ok, f'diff {paths.exp} {paths.got}'

####
# Helpers.
####

def example_paths(exkey):
    return cons(
        got = Path('tests') / 'ex_diff' / 'got' / exkey,
        exp = Path('tests') / 'ex_diff' / 'exp' / exkey,
    )

def read_file(path):
    with open(path) as fh:
        return fh.read()

def write_file(path, text):
    with open(path, 'w') as fh:
        fh.write(text)

'''

parse()
  variant()
    eat(wanted = 'variant_def')
    get_next_token(lexed = 'angle_open')
    variant_elems()
      quoted_literal()
        eat(wanted = 'quoted_literal')
        get_next_token(lexed = 'angle_open')
        quoted_literal(RESULT = '∅')
      choice_sep()
        eat(wanted = 'choice_sep')
        get_next_token(lexed = 'angle_open')
        choice_sep(RESULT = '∅')
      partial_usage()
        eat(wanted = 'partial_usage')
        get_next_token(lexed = 'angle_open')
        partial_usage(RESULT = '∅')
      any_group()
        eat(wanted = 'paren_open|paren_open_named')
        get_next_token(lexed = 'angle_open')
        eat(wanted = 'brack_open|brack_open_named')
        get_next_token(lexed = 'angle_open')
        any_group(RESULT = '∅')
      positional()
        eat(wanted = 'angle_open')
        get_next_token(lexed = 'angle_open')
        taste(ok = True, is_first = True)
        get_next_token(returned = 'angle_open')
        eat(eaten = 'angle_open', text = '<', pos = 1, line = 2, col = 1)
        var_input_elems()
          eat(wanted = 'valid_name')
          get_next_token(lexed = 'valid_name')
          taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
          get_next_token(returned = 'valid_name')
          eat(eaten = 'valid_name', text = 'rgx', pos = 2, line = 2, col = 2)
          eat(wanted = 'assign')
          get_next_token(lexed = 'angle_close')
          next_choice()
            eat(wanted = 'choice_sep')
            get_next_token(lexed = 'angle_close')
            next_choice(RESULT = '∅')
          var_input_elems(RESULT = 'tuple')
        eat(wanted = 'angle_close')
        get_next_token(lexed = 'angle_close')
        taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
        get_next_token(returned = 'angle_close')
        eat(eaten = 'angle_close', text = '>', pos = 5, line = 2, col = 5)
        positional(RESULT = 'Positional')
      add_quantifer_to()
        quantifier()
          eat(wanted = 'triple_dot')
          get_next_token(lexed = 'opt_spec_sep')
          eat(wanted = 'quant_range')
          get_next_token(lexed = 'opt_spec_sep')
          eat(wanted = 'question')
          get_next_token(lexed = 'opt_spec_sep')
          quantifier(RESULT = '∅')
        add_quantifer_to(RESULT = '∅')
      quoted_literal()
        eat(wanted = 'quoted_literal')
        get_next_token(lexed = 'opt_spec_sep')
        quoted_literal(RESULT = '∅')
      choice_sep()
        eat(wanted = 'choice_sep')
        get_next_token(lexed = 'opt_spec_sep')
        choice_sep(RESULT = '∅')
      partial_usage()
        eat(wanted = 'partial_usage')
        get_next_token(lexed = 'opt_spec_sep')
        partial_usage(RESULT = '∅')
      any_group()
        eat(wanted = 'paren_open|paren_open_named')
        get_next_token(lexed = 'opt_spec_sep')
        eat(wanted = 'brack_open|brack_open_named')
        get_next_token(lexed = 'opt_spec_sep')
        any_group(RESULT = '∅')
      positional()
        eat(wanted = 'angle_open')
        get_next_token(lexed = 'opt_spec_sep')
        positional(RESULT = '∅')
      option()
        bare_option()
          eat(wanted = 'long_option|short_option')
          get_next_token(lexed = 'opt_spec_sep')
          bare_option(RESULT = '∅')
        option(RESULT = '∅')
      variant_elems(RESULT = 'list')
    variant(RESULT = '∅')
  collect_section_elem()
    any_section_title()
      eat(wanted = 'scoped_section_title|section_title')
      get_next_token(lexed = 'angle_open')
      any_section_title(RESULT = '∅')
    section_content_elem()
      heading()
        eat(wanted = 'heading')
        get_next_token(lexed = 'angle_open')
        heading(RESULT = '∅')
      block_quote()
        eat(wanted = 'quoted_block')
        get_next_token(lexed = 'angle_open')
        block_quote(RESULT = '∅')
      opt_spec()
        opt_spec_scope()
          eat(wanted = 'opt_spec_scope|opt_spec_scope_empty')
          get_next_token(lexed = 'angle_open')
          opt_spec_scope(RESULT = '∅')
        opt_spec_def()
          opt_spec_group()
            eat(wanted = 'paren_open|paren_open_named')
            get_next_token(lexed = 'angle_open')
            eat(wanted = 'brack_open|brack_open_named')
            get_next_token(lexed = 'angle_open')
            opt_spec_group(RESULT = '∅')
          opt_spec_elem()
            positional()
              eat(wanted = 'angle_open')
              get_next_token(lexed = 'angle_open')
              taste(ok = True, is_first = True)
              get_next_token(returned = 'angle_open')
              eat(eaten = 'angle_open', text = '<', pos = 1, line = 2, col = 1)
              var_input_elems()
                eat(wanted = 'valid_name')
                get_next_token(lexed = 'valid_name')
                taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
                get_next_token(returned = 'valid_name')
                eat(eaten = 'valid_name', text = 'rgx', pos = 2, line = 2, col = 2)
                eat(wanted = 'assign')
                get_next_token(lexed = 'angle_close')
                next_choice()
                  eat(wanted = 'choice_sep')
                  get_next_token(lexed = 'angle_close')
                  next_choice(RESULT = '∅')
                var_input_elems(RESULT = 'tuple')
              eat(wanted = 'angle_close')
              get_next_token(lexed = 'angle_close')
              taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
              get_next_token(returned = 'angle_close')
              eat(eaten = 'angle_close', text = '>', pos = 5, line = 2, col = 5)
              positional(RESULT = 'Positional')
            opt_spec_elem(RESULT = 'Positional')
          opt_spec_def(RESULT = 'Positional')
        opt_help_text()
          eat(wanted = 'opt_spec_sep')
          get_next_token(lexed = 'opt_spec_sep')
          taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
          get_next_token(returned = 'opt_spec_sep')
          eat(eaten = 'opt_spec_sep', text = ':', pos = 7, line = 2, col = 7)
          rest_of_line()
            eat(wanted = 'rest_of_line')
            get_next_token(lexed = 'rest_of_line')
            taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
            get_next_token(returned = 'rest_of_line')
            eat(eaten = 'rest_of_line', text = 'Python regular expression', pos = 9, line = 2, col = 9)
            rest_of_line(RESULT = 'str')
          rest_of_line()
            eat(wanted = 'rest_of_line')
            get_next_token(lexed = 'rest_of_line')
            taste(ok = False, indent_reason = False, self_indent = 0, tok_indent = 0)
            rest_of_line(RESULT = '∅')
          opt_help_text(RESULT = 'str')
        opt_spec(RESULT = 'OptSpec')
      section_content_elem(RESULT = 'OptSpec')
    any_section_title()
      eat(wanted = 'scoped_section_title|section_title')
      get_next_token(lexed = 'brack_open')
      any_section_title(RESULT = '∅')
    section_content_elem()
      heading()
        eat(wanted = 'heading')
        get_next_token(lexed = 'brack_open')
        heading(RESULT = '∅')
      block_quote()
        eat(wanted = 'quoted_block')
        get_next_token(lexed = 'brack_open')
        block_quote(RESULT = '∅')
      opt_spec()
        opt_spec_scope()
          eat(wanted = 'opt_spec_scope|opt_spec_scope_empty')
          get_next_token(lexed = 'brack_open')
          opt_spec_scope(RESULT = '∅')
        opt_spec_def()
          opt_spec_group()
            eat(wanted = 'paren_open|paren_open_named')
            get_next_token(lexed = 'brack_open')
            eat(wanted = 'brack_open|brack_open_named')
            get_next_token(lexed = 'brack_open')
            taste(ok = True, is_first = True)
            get_next_token(returned = 'brack_open')
            eat(eaten = 'brack_open', text = '[', pos = 35, line = 3, col = 1)
            opt_spec_elem()
              positional()
                eat(wanted = 'angle_open')
                get_next_token(lexed = 'angle_open')
                taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
                get_next_token(returned = 'angle_open')
                eat(eaten = 'angle_open', text = '<', pos = 36, line = 3, col = 2)
                var_input_elems()
                  eat(wanted = 'valid_name')
                  get_next_token(lexed = 'valid_name')
                  taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
                  get_next_token(returned = 'valid_name')
                  eat(eaten = 'valid_name', text = 'path', pos = 37, line = 3, col = 3)
                  eat(wanted = 'assign')
                  get_next_token(lexed = 'angle_close')
                  next_choice()
                    eat(wanted = 'choice_sep')
                    get_next_token(lexed = 'angle_close')
                    next_choice(RESULT = '∅')
                  var_input_elems(RESULT = 'tuple')
                eat(wanted = 'angle_close')
                get_next_token(lexed = 'angle_close')
                taste(ok = True, indent_reason = 'line', self_indent = 0, tok_indent = 0)
                get_next_token(returned = 'angle_close')
                eat(eaten = 'angle_close', text = '>', pos = 41, line = 3, col = 7)
                positional(RESULT = 'Positional')
              opt_spec_elem(RESULT = 'Positional')
            eat(wanted = 'brack_close')
            get_next_token(lexed = 'triple_dot')


'''

