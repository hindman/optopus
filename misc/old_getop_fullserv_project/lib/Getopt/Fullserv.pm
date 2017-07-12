package Getopt::Fullserv;

use 5.006;
use strict;
use warnings;

use Getopt::Fullserv::Opt qw();
use Getopt::Long qw(GetOptionsFromArray);
use Pod::Usage qw(pod2usage);
use Carp qw(croak);
use File::Basename qw(basename);
require Exporter;

our $VERSION   = '0.01';
our @ISA       = qw(Exporter);
our @EXPORT    = qw();
our @EXPORT_OK = qw();

my %POD_VERBOSITIES = (
    usage => 0,
    help  => 1,
    man   => 2,
);


####
# Debugging stuff.
####

use feature qw(say);
use Data::Dumper qw(Dumper);
$Data::Dumper::Indent = 1;
sub xxx { say Dumper(@_) }


####
# Parser constructor.
####

sub new {
    my ($class, @raw_specs) = @_;
    my $param = {};
    $param = pop @raw_specs if @raw_specs and ref($raw_specs[-1]) eq ref({});
    my $self = {
        # Default parameters for the parser.
        original_args => [],
        unparsed_args => [],
        parse_succeeded => 0,
        options => {},
        opt_hash => {},
        auto_help => 1,
        auto_help_opts => [qw(usage help man)],
        usage_text => sprintf('Usage: %s [ARGUMENTS] [OPTIONS]', basename $0),
        help_text => '',
        man_text => '',
        # User's parameters will override defaults.
        %$param,
    };
    bless $self, $class;
    $self->process_raw_specs(@raw_specs);
    $self->set_auto_help_options( @{$self->auto_help_opts} ) if $self->auto_help;
    return $self;
}

sub process_raw_specs {
    # Convert the raw option specs that the caller passed to the constructor
    # into a hash of Opt objects.
    my ($self, @raw_specs) = @_;
    my %options;
    for my $rs (@raw_specs){
        my $o = Getopt::Fullserv::Opt->new(@$rs);
        $options{$o->name} = $o;
    }
    $self->options( \%options );
}


####
# Option parsing.
####

sub parse {
    # Parse options from the given array, defaulting to @ARGV;
    my ($self, $args) = @_;
    $args = \@ARGV unless defined $args;
    $self->original_args([@$args]);

    # Parse the options and collect info about the outcome.
    my ($parse_ok, @warnings) = $self->get_options_from_array($args);
    $self->parse_succeeded($parse_ok);
    $self->unparsed_args([@$args]);

    # Issue warnings from Getopt::Long.
    $self->quit(
        $self->cleaned_warning(@warnings), "\n\n",
        $self->usage_text, "\n",
    ) if @warnings;

    # Set defaults and handle help options.
    $self->set_defaults;
    $self->handle_help_opts if $self->auto_help;

    return $self->opt_hash;
}

sub get_options_from_array {
    # Takes an array ref of the args to be parsed. Parses the
    # arguments, trapping any warnings emitted by Getopt::Long.
    # Returns overall status of the parse and the warnings, if any.
    #
    # Inside the signal handler block, we just store the warnings.
    # If we try to issue the warning at that point, it interferes with our
    # ability to unit test the code, which also depends on trapping
    # warnings. Since __WARN__ hooks are not called within other
    # __WARN__ hooks, our unit test would not perceive the warning.
    my ($self, $args) = @_;
    my @specs = map $_->getopt_long_spec, values %{$self->options};
    my @warnings;
    local $SIG{__WARN__} = sub { @warnings = @_ };
    my $parse_ok = GetOptionsFromArray($args, $self->opt_hash, @specs);
    return $parse_ok, @warnings;
}

sub cleaned_warning {
    # Basic text cleanup up the warnings from Getopt::Long.
    my $self = shift;
    my $warning = join ' ', @_;
    rtrim($warning);
    $warning .= '.' unless $warning =~ /[.!?]\z/;
    return $warning;
}

sub set_defaults {
    # Optionally takes a hash ref, but usually works with the hash ref
    # populated by the call to GetOptionsFromArray(). Populates that
    # hash with the option defaults known by the parser, skipping any
    # keys that already have a value.
    my ($self, $hr) = @_;
    $hr = $self->opt_hash unless defined $hr;
    my $os = $self->options;
    for my $k (keys %$os){
        $hr->{$k} = $os->{$k}{default} unless exists $hr->{$k};
    }
}


####
# Intra-module methods to deal with help options and meta text.
####

sub set_auto_help_options {
    # Takes a list of 0+ auto_help options: usage, help, man.
    # First removes all existing auto_help options (Opt objects)
    # from the parser and add new options based on the list passed.
    my ($self, @help_opts) = @_;
    my $options = $self->options;
    delete $options->{$_} for @{$self->auto_help_opts};
    for my $ho (@help_opts){
        my $o = Getopt::Fullserv::Opt->new($ho);
        $options->{$o->name} = $o;
    }
    # Must also set the status of auto_help. We can't use
    # the setter, otherwise we would create an endless loop.
    $self->getset('auto_help', @help_opts ? 1 : 0);
}

sub handle_help_opts {
    # This method is called immediately after parsing.
    # If the user requested any of the available auto_help
    # options, the method prints the help text and exits.
    my $self = shift;
    my %oh = %{$self->opt_hash};
    for my $k ( @{$self->auto_help_opts} ){
        $self->quit($self->get_meta_text($k)) if $oh{$k};
    }
}

sub print_meta_text {
    # Takes a auto_help key (usage, help, man) and an optional message.
    # Prints the message and the meta text.
    my ($self, $k, @msg) = @_;
    rtrim(@msg);
    print @msg, "\n\n" if @msg;
    print $self->get_meta_text($k);
}

sub get_meta_text {
    # Takes an auto_help key (usage, help, man) and returns the requested
    # meta text. The search for applicable text proceeds in this order:
    #   - Meta text provided by the caller.
    #   - POD.
    #   - A generic message.
    my ($self, $k) = @_;
    my $txt = $self->{$k . '_text'};
    $txt = $self->get_pod_text($k) unless $txt;
    $txt = "No text is available for the --$k option." unless $txt;
    rtrim($txt);
    return $txt . "\n";
}

sub get_pod_text {
    # Takes an auto_help key (usage, help, man) and returns the requested
    # meta text as obtained by pod2usage.
    my ($self, $k) = @_;
    my $v = $POD_VERBOSITIES{$k};
    open(my $fh, '>', \my $txt) or die $!;
    pod2usage(-verbose => $v, -output => $fh, -exitval => 'NOEXIT');
    return $txt;
}


####
# Interface for meta functions.
# These method allow the caller to print meta text, issue warnings, or quit.
# In all cases, the caller to include a message that will precede the meta text.
####

sub warn {
    my ($self, @msg) = @_;
    rtrim(@msg);
    warn @msg, "\n";
}

sub quit {
    my ($self, @msg) = @_;
    rtrim(@msg);
    die @msg, "\n";
}

sub usage { shift->print_meta_text('usage', @_) }
sub help  { shift->print_meta_text('help', @_) }
sub man   { shift->print_meta_text('man', @_) }


####
# Utilities.
####

sub rtrim {
    # Removes trailing whitespace from the last arg.
    $_[-1] =~ s/\s+\z// if @_;
}


####
# Getters and setters.
####

sub opt {
    # Takes an option name and returns the corresponding Opt object.
    my ($self, $opt_name) = @_;
    my $os = $self->options;
    return $os->{$opt_name} if exists $os->{$opt_name};
    croak "Invalid option name: $opt_name:";
}

sub getset {
    # General purpose getter-setter.
    my ($self, $key, $val) = @_;
    $self->{$key} = $val if @_ > 2;
    return $self->{$key};
}

sub original_args   { shift->getset('original_args', @_) }
sub unparsed_args   { shift->getset('unparsed_args', @_) }
sub parse_succeeded { shift->getset('parse_succeeded', @_) }
sub options         { shift->getset('options', @_) }
sub opt_hash        { shift->getset('opt_hash', @_) }
sub auto_help_opts  { shift->getset('auto_help_opts', @_) }
sub usage_text      { shift->getset('usage_text', @_) }
sub help_text       { shift->getset('help_text', @_) }
sub man_text        { shift->getset('man_text', @_) }

sub auto_help {
    # This attribute requires a special setter because
    # we need to manage the parser's auto_help Opt objects.
    my ($self, $val) = @_;
    # First the basic get-set functionality.
    return $self->{auto_help} unless @_ > 1;
    $self->{auto_help} = $val;
    # Create or delete the auto_help Opt objects.
    $self->set_auto_help_options( $val ? @{$self->auto_help_opts} : () );
}

1;

