#! /usr/bin/env python

from optopus import Parser

p = Parser()
opts = p.parse()

# Check out the returned data object:

print(opts)
print(opts.bar)               # Attribute access.
print(opts['x'])              # Key access.
print('positionals' in opts)  # Membership testing.
for dest, val in opts:        # Direct iteration.
    print((dest, val))

