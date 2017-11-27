from __future__ import absolute_import, unicode_literals, print_function

import pytest
import sys
import io

@pytest.fixture(scope = 'function')
def std_streams():

    # Setup.
    attrs = ('stdout', 'stderr')
    originals = {}
    mocks = {}

    # Store references to the original streams,
    # and replace them with StringIO instances.
    for a in attrs:
        originals[a] = getattr(sys, a)
        mocks[a] = io.StringIO()
        setattr(sys, a, mocks[a])

    # Yield the dict of StringIO instances to caller.
    yield mocks

    # Restore the original streams after the test function completes.
    for a in attrs:
        mocks[a].close()
        setattr(sys, a, originals[a])

