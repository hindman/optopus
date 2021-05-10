import io
import json
import pytest
import sys

@pytest.fixture
def tr():
    return TestResource()

class TestResource(object):

    def dump(self, val = None, label = 'dump()'):
        fmt = '\n--------\n{label} =>\n{val}'
        msg = fmt.format(label = label, val = val)
        print(msg)

    def dumpj(self, val = None, label = 'dump()', indent = 4):
        val = json.dumps(val, indent = indent)
        self.dump(val, label)

class StdStreams(object):

    def __init__(self):
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        self.reset()

    def reset(self):
        self.close()
        io1 = io.StringIO()
        io2 = io.StringIO()
        self._stdout = io1
        self._stderr = io2
        sys.stdout = io1
        sys.stderr = io2

    def close(self):
        if hasattr(self, '_stdout'):
            self._stdout.close()
            self._stderr.close()

    def restore(self):
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr

    @property
    def stdout(self):
        return self._stdout.getvalue()

    @property
    def stderr(self):
        return self._stderr.getvalue()

@pytest.fixture(scope = 'function')
def std_streams():
    ss = StdStreams()
    yield ss
    ss.close()
    ss.restore()

