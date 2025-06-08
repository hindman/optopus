
import inspect

from short_con import dc

####
# Utility functions.
####

def get_caller_name(caller_offset):
    # Get the name of a calling function.
    x = inspect.currentframe()
    for _ in range(caller_offset):
        x = x.f_back
    x = x.f_code.co_name
    return x

def fill_to_len(xs, n):
    # Takes a list and a desired length.
    # Returns a list at least that long.
    filler = [None] * (n - len(xs))
    return xs + filler

def get(xs, i, default = None):
    # Like dict.get(), but also works for sequences.
    try:
        return xs[i]
    except (IndexError, KeyError) as e:
        return default

def to_repr(obj, *ks):
    # A helper to mimic dataclass repr().
    cls_name = obj.__class__.__qualname__
    ks = ks or obj.__dict__.keys()
    kws = {
        k : getattr(obj, k)
        for k in ks
    }
    params = ', '.join(
        f'{k}={v!r}'
        for k, v in kws.items()
    )
    return f'{cls_name}({params})'

def distilled(obj, *attrs):
    # Takes an object and some attrs.
    # Returns a new short-con dataclass having the same class name as the
    # original object, but with just the attributes of interest.
    cls_name = obj.__class__.__qualname__
    kws = {
        a : getattr(obj, a)
        for a in attrs
    }
    cls = dc(*kws, cls_name = cls_name)
    return cls(**kws)

def partition(xs, predicate = bool):
    d = {True: [], False: []}
    for x in xs:
        result = bool(predicate(x))
        d[result].append(x)
    return (d[True], d[False])

