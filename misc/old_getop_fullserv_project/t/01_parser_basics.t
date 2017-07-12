#!perl -T

use strict;
use warnings;

use feature qw(say);
use Data::Dumper qw(Dumper);
$Data::Dumper::Indent = 1;
sub xxx { say Dumper(@_) }

use Test::More;
use Test::Exception;

use Getopt::Fullserv;

my $CLASS_NAME = 'Getopt::Fullserv';

my @OPT_SPECS = (
    [ 'files|f=s@{,}', default => [] ],
    [ 'max|m=i',       default => 999 ],
    [ 'zero_pad|z' ],
);


####
# Run the test methods.
####

can_create_new_object();
check_some_opts();
should_croak_on_invalid_opt();
parse_works_as_expected();
can_specify_usage_text();
can_specify_help_text();
can_specify_man_text();
check_cleaned_warning();
check_failed_parses();
can_disabled_auto_help();
can_set_parameters_in_constructor();
help_options_are_present();
check_get_options_from_array();

done_testing();


####
# Helper methods.
####

sub new_parser {
    return $CLASS_NAME->new(@_);
}


####
# The tests.
####

sub can_create_new_object {
    my $gf = new_parser();
    isa_ok $gf, $CLASS_NAME;
}

sub check_some_opts {
    my $gf = new_parser(@OPT_SPECS);
    my ($o, $nm);
    my $msg = 'can create basic options: test ';
    my $N = 0;

    $nm = 'max';
    $o = $gf->opt($nm);
    isa_ok $o, 'Getopt::Fullserv::Opt';
    is $o->name, $nm, $msg . $N ++;
    is $o->default, 999, $msg . $N ++;

    $nm = 'zero_pad';
    $o = $gf->opt($nm);
    is $o->name, $nm, $msg . $N ++;

    $nm = 'files';
    $o = $gf->opt($nm);
    is $o->name, $nm, $msg . $N ++;
}

sub should_croak_on_invalid_opt {
    my $gf = new_parser();
    my $exp = qr/invalid option name/i;
    my $msg = 'croaks if invalid option is requested';
    throws_ok { $gf->opt('xxx') } $exp, $msg;
}

sub parse_works_as_expected {
    my @tests = (
        {
            args => [ qw(a b c --files xx yy zz --max 125 -z d e f) ],
            exp  => { zero_pad => 1, files => [qw(xx yy zz)], max => 125 },
        },
        {
            args => [ qw(a b c --files xx yy zz -z d e f) ],
            exp  => { zero_pad => 1, files => [qw(xx yy zz)], max => 999 },
        },
        {
            args => [ qw(a b c -z d e f) ],
            exp  => { zero_pad => 1, files => [], max => 999 },
        },
        {
            args => [ qw(a b c d e f) ],
            exp  => { zero_pad => undef, files => [], max => 999 },
        },
    );
    my ($msg, $N, $upa);

    # Add the help options to all exp hashes.
    $_->{exp} = { 
        %{$_->{exp}}, 
        usage => undef,
        help => undef, 
        man => undef,
    } for @tests;

    $msg = 'parse() works: ';
    $N = 0;
    $upa = [qw(a b c d e f)];
    for my $t (@tests){
        my $gf   = new_parser(@OPT_SPECS);
        my $args = [ @{$t->{args}} ]; # Needed to prevent @tests from being altered.
        my @orig = @$args;
        my $exp  = $t->{exp};
        my $opt  = $gf->parse($args);
        is_deeply $gf->original_args, \@orig, "$msg original args:   test $N";
        is_deeply $opt,               $exp,   "$msg options:         test $N";
        is_deeply $gf->unparsed_args, $upa,   "$msg unparsed args:   test $N";
        ok        $gf->parse_succeeded,       "$msg parse_succeeded: test $N";
        $N ++;
    }

    $msg = 'parse(@ARGV) works: ';
    $N = 0;
    for my $t (@tests){
        my $gf      = new_parser(@OPT_SPECS);
        local @ARGV = @{$t->{args}};
        my @orig    = @{$t->{args}};
        my $exp     = $t->{exp};
        my $opt     = $gf->parse();
        is_deeply $gf->original_args, \@orig, "$msg original args:   test $N";
        is_deeply $opt,               $exp,   "$msg options:         test $N";
        is_deeply $gf->unparsed_args, \@ARGV, "$msg unparsed args:   test $N";
        ok        $gf->parse_succeeded,       "$msg parse_succeeded: test $N";
        $N ++;
    }
}

sub can_specify_usage_text {
    my $gf = new_parser(@OPT_SPECS);
    like $gf->usage_text, qr/^Usage: /, 'default usage text is present';
    my $u = 'Usage: foo.pl [OPTIONS]';
    $gf->usage_text($u);
    is $gf->usage_text, $u, 'user can set usage text';
}

sub can_specify_help_text {
    my $gf = new_parser(@OPT_SPECS);
    is $gf->help_text, '', 'default help text is empty';
    my $h = 'Some awesome help text...';
    $gf->help_text($h);
    is $gf->help_text, $h, 'user can set help text';
}

sub can_specify_man_text {
    my $gf = new_parser(@OPT_SPECS);
    is $gf->man_text, '', 'default man text is empty';
    my $m = 'Some awesome man text...';
    $gf->man_text($m);
    is $gf->man_text, $m, 'user can set man text';
}

sub check_cleaned_warning {
    my $gf = new_parser(@OPT_SPECS);
    my @tests = (
        ["foo",  'foo.'],
        ["foo.", 'foo.'],
        ["foo!", 'foo!'],
        ["foo?", 'foo?'],
        ["foo  ",     'foo.'],
        ["foo. \t",   'foo.'],
        ["foo! \t\n", 'foo!'],
        ["foo?\n\n",  'foo?'],
    );
    my $msg = 'cleaned_warning() works as expected: test ';
    my $N = 0;
    for my $t (@tests){
       is $gf->cleaned_warning($t->[0]), $t->[1], $msg . $N ++;  
    }
}

sub check_failed_parses {
    my $gf = new_parser(@OPT_SPECS);
    my $msg = 'check failed parses';
    my $N = 0;
    my $opt;
    my @tests = (
        [ [qw(a b --FUBB)],    qr/\AUnknown option/ ],
        [ [qw(a b --max XXX)], qr/\AValue .+ invalid for option/ ],
        [ [qw(a b --files)],   qr/\AOption .+ requires an arg/ ],
    );
    for my $t (@tests){
        my ($args, $regex) = @$t;
        throws_ok { $opt = $gf->parse($args) } $regex, "$msg: dies:                     $N";
        ok not($gf->parse_succeeded),                  "$msg: parse_succeeded is false: $N";
        is_deeply $gf->unparsed_args, $args,           "$msg: args are unchanged:       $N";
        $N ++;
    }
}

sub can_disabled_auto_help {
    my $gf = new_parser(@OPT_SPECS);
    ok $gf->auto_help, 'auto_help is on by default';
    $gf->auto_help(0);
    ok not($gf->auto_help), 'can disable auto_help';
}

sub can_set_parameters_in_constructor {
    my $param = { auto_help => 0, help_text => 'foobar' };
    my $gf = new_parser(@OPT_SPECS, $param);
    my $msg = 'set param param in constructor';
    ok not($gf->auto_help),      "$msg: auto_help";
    is $gf->help_text, 'foobar', "$msg: help_text";
}

sub help_options_are_present {
    my $gf = new_parser(@OPT_SPECS);
    my $msg = 'can create basic options: test ';
    for my $nm ( qw(usage help man) ){
        my $o = $gf->opt($nm);
        isa_ok $o, 'Getopt::Fullserv::Opt', "The --$nm option:";
    }
}

sub check_get_options_from_array {
    my @tests = (
        {
            args => [ qw(a b c --files xx yy zz --max 125 -z d e f) ],
            exp  => [ 1, qr/\A\z/ ],
        },
        {
            args => [ qw(a b c --xyz) ],
            exp  => [ '', qr/\AUnknown option/ ],
        },
    );
    my $N = 0;
    my $gf = new_parser(@OPT_SPECS);
    my $msg = 'get_options_from_array() returns expected info';
    for my $t (@tests){
        my ($exp_ps, $exp_warn) = @{$t->{exp}};
        my ($parse_succeeded, @warning) = $gf->get_options_from_array($t->{args});
        is $parse_succeeded, $exp_ps, "$msg: parse_succeeded: test $N";
        like "@warning", $exp_warn,   "$msg: warning:         test $N";
        $N ++;
    }
}

