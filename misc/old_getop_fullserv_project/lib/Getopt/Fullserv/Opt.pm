package Getopt::Fullserv::Opt;

use 5.006;
use strict;
use warnings;

use Carp qw(croak);
require Exporter;

our $VERSION   = '0.01';
our @ISA       = qw(Exporter);
our @EXPORT    = qw();
our @EXPORT_OK = qw();


####
# Debugging stuff.
####

use feature qw(say);
use Data::Dumper qw(Dumper);
$Data::Dumper::Indent = 1;
sub xxx { say Dumper(@_) }


####
# Constructor.
####

sub new {
    my ($class, $gspec, %spec) = @_;
    my $self = {
        getopt_long_spec => $gspec,
        default => undef,
        name => undef,
    };
    bless $self, $class;
    my $name = $self->get_opt_name_from_spec($gspec);
    $self->name($name);
    $self->default($spec{default}) if exists $spec{default};
    return $self;
}

sub get_opt_name_from_spec {
    # Takes a Getopt::Long spec and returns just the option name.
    # For example: '--foo|f=s' => 'foo'.
    my ($self, $gspec) = @_;
    return unless defined $gspec;
    my ($prefix, $name, $the_rest) = $gspec =~ /\A (-{0,2}) ([\w-]+) (.*) \z/ix;
    return $name;
}


####
# Getters and setters.
####

sub getset {
    # General purpose getter-setter.
    my ($self, $key, $val) = @_;
    $self->{$key} = $val if @_ > 2;
    return $self->{$key};
}

sub getopt_long_spec { shift->getset('getopt_long_spec', @_) }
sub default          { shift->getset('default',          @_) }
sub name             { shift->getset('name',             @_) }

1;

