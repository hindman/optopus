#!perl -T

use strict;
use warnings;

use feature qw(say);
use Data::Dumper qw(Dumper);
$Data::Dumper::Indent = 1;
sub xxx { say Dumper(@_) }

use Test::More;
use Test::Exception;

use Getopt::Fullserv::Opt;

my $CLASS_NAME = 'Getopt::Fullserv::Opt';

####
# Run the test methods.
####

can_create_new_object();
check_raw_spec_handling();
done_testing();


####
# Helper methods.
####

sub new_opt {
    return $CLASS_NAME->new(@_);
}


####
# The tests.
####

sub can_create_new_object {
    my $o = new_opt();
    isa_ok $o, $CLASS_NAME;
}

sub check_raw_spec_handling {
    my $o;
    my $msg = "Raw spec handling: ";

    $o = new_opt('--foo|f=s', default => 'bar');
    is $o->name, 'foo',    $msg . 'typical option';
    is $o->default, 'bar', $msg . 'string default';

    $o = new_opt('--quux');
    is $o->name, 'quux',         $msg . 'no short option';
    ok not(defined $o->default), $msg . 'no default';

    $o = new_opt('foo|f=i', default => 123);
    is $o->name, 'foo',  $msg . 'positional arg';
    is $o->default, 123, $msg . 'numeric default';
}

