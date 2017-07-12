use 5.006;
use strict;
use warnings;
use ExtUtils::MakeMaker;

WriteMakefile(
    NAME                => 'Getopt::Fullserv',
    AUTHOR              => q{Monty Hindman <montyhindman@gmail.com>},
    VERSION_FROM        => 'lib/Getopt/Fullserv.pm',
    ABSTRACT_FROM       => 'lib/Getopt/Fullserv.pm',
    ($ExtUtils::MakeMaker::VERSION >= 6.3002
      ? ('LICENSE'=> 'perl')
      : ()),
    PL_FILES            => {},
    PREREQ_PM => {
        'Test::More' => 0,
    },
    dist                => { COMPRESS => 'gzip -9f', SUFFIX => 'gz', },
    clean               => { FILES => 'Getopt-Fullserv-*' },
);
