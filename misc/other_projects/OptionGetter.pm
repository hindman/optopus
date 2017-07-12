package OptionGetter;

use strict;
use warnings;
use Getopt::Long qw(GetOptionsFromArray);
use File::Basename;
use Carp;
require Exporter;

our $VERSION   = '1.00';
our @ISA       = qw(Exporter);
our @EXPORT    = qw(Get_options Help);
our @EXPORT_OK = qw();

my(%msg, %validator);

# Define a dispatch table for the validation keywords.
%validator = (
    integer => {
        code => sub { $_[0] =~ /^-?\d+$/ },
        msg  => "integer expected",
    },
    positive => {
        code => sub { $_[0] > 0 },
        msg  => "positive number expected",
    },
    negative => {
        code => sub { $_[0] < 0 },
        msg  => "negative number expected",
    },
    not_positive => {
        code => sub { $_[0] <= 0 },
        msg  => "non-positive number expected",
    },
    not_negative => {
        code => sub { $_[0] <= 0 },
        msg  => "non-negative number expected",
    },
    file => {
        code => sub { -f $_[0] },
        msg  => "file not found",
    },
    'file-' => {
        code => sub { -f $_[0] or $_[0] eq '-' },
        msg  => "file not found",
    },
    directory => {
        code => sub { -d $_[0] },
        msg  => "directory not found",
    },
    not_file => {
        code => sub { ! -f $_[0] },
        msg  => "file already exists",
    },
    not_directory => {
        code => sub { ! -d $_[0] },
        msg  => "directory already exists",
    },
);


sub Get_options {
    my (%param, @table, %default, %option, @getopt_specs, %validation_keywords);

    # Get the parameters.
    #    help    => 'Help message.'
    #    usage   => 'Usage message (just a schematic summary of the arguments and options)'
    #    table   => Array reference to the options table
    #    source  => Array reference. Defaults to \@ARGV.
    #    no_help => If true, the -help option won't be supplied automatically.
    %param = @_;
    $msg{$_} = '' for qw(help usage error);
    for my $m ( qw(usage help) ){
        $msg{$m} = $param{$m} if exists $param{$m};
    }
    @table = @{$param{table}};
    $param{source} = \@ARGV unless exists $param{source};

    # Add the -help option to the table.    
    push @table, {
        opt  => 'help',
        spec => '',
        def  => 0,
    } unless $param{no_help};

    # Process the options table entries. Each entry is a hash reference:
    #                                                                         Example
    #                                                                         -------
    #    opt     => The option.                                               wid
    #    spec    => The option specification, using Getopt::Long syntax.      =i
    #    def     => Default value of option is not supplied.                  1
    #    desc    => Option help text.                                         N
    #    arg     => Option argument help text.                                Record type width (default = 1).
    #    valid   => Space-delimited list of validation keywords.              integer positive
    #    hide    => If true, do not include option in help text.
    #
    #    heading => If present, the entry is an option group (in the          Record type options
    #               help text) rather than an actual option.
    #
    for my $t (@table){
        my ($o);
        croak "Invalid option table item: missing required parameters.\n"
            unless exists $t->{opt}
               and exists $t->{spec}
        ;
        $o = $t->{opt};

        # Create the Getopt::Long specification (e.g., 'wid=i').
        push @getopt_specs, $o . $t->{spec};
        
        # Store the default values.
        $default{$o}  = $t->{def} if exists $t->{def};

        # Store the validation keywords (convert space-delimited to a list).
        $validation_keywords{$o} = [ split /\s+/, $t->{valid} ] if exists $t->{valid};
    }

    # Use Getopt::Long to parse the options.
    {
        local $SIG{__WARN__} = \&Help;
        GetOptionsFromArray($param{source}, \%option, @getopt_specs);
    }

    # Provide help if requested.
    Help() if $option{help};

    # Validate the option values.
    for my $o (keys %validation_keywords){
        next unless exists $option{$o} and defined $option{$o};
        for my $kw ( @{$validation_keywords{$o}} ){
            croak "Invalid option table item: bad validation keyword ($kw).\n"
                unless exists $validator{$kw};
            Help($msg{error}) unless Validate( $kw, $o, $option{$o} );
        } 
    }

    # Merge the default option values with the user-supplied values.
    %option = (%default, %option);

    # Return the options.
    return %option;
}


# Provide help in one of two mode:
#    Error:   print the error and usage messages.
#    General: print the help message.
sub Help {
    if (@_){
        $msg{error} = shift;
        chomp $msg{error};
        $msg{error} .= '.' unless $msg{error} =~ /[.?!]$/;
        die "\n",
            $msg{error}, "\n",
            'Usage: ', basename($0), ' ', $msg{usage}, "\n";
    } else {
        die $msg{help}, "\n";
    }
}


# Validate the option values. Takes three arguments: the validation
# keyword, the option, and the option value(s). Returns true if all
# values are valid. If not, sets the value of $msg{error} and return false.
sub Validate {
    my ($kw, $opt, $r, @vals);
    ($kw, $opt, $r) = @_;
    @vals = (ref($r) eq 'ARRAY' ? @$r : $r);
    for my $v (@vals){
        next if $validator{$kw}{code}->($v);
        $msg{error} = "Value '$v' invalid for option -$opt ($validator{$kw}{msg})";
        return 0;
    }
    return 1;
}


# Module return.
return 1;


__END__

Add args validation
    args => {
        n     => '3+', # 3+ 0+ 1-2
        valid => ['file-', 'integer not_negative']
    }

Do not supply help automatically.

Maybe add later: parameters to support printing of the options and their help.
        arg_desc
        desc
        headings
        hide

    Add this up to determine where to start printing option descriptions.
        4 spaces
        hyphen
        width of widest option
        1 space
        width of widest option_arg description
        2 spaces

        -start X  Record type start column.
                  ^
