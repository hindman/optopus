#!perl -T

use Test::More tests => 1;

BEGIN {
    use_ok( 'Getopt::Fullserv' ) || print "Bail out!\n";
}

diag( "Testing Getopt::Fullserv $Getopt::Fullserv::VERSION, Perl $], $^X" );
