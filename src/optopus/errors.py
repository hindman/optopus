
class Kwexception(Exception):

    def __init__(self, msg = '', **kws):
        kws['msg'] = msg
        super(Kwexception, self).__init__(kws)

    def __str__(self):
        return '{}\n'.format(self.params)

    @property
    def params(self):
        return self.args[0]

    @classmethod
    def make_error(cls, error, **kws):
        # Takes an Exception and keyword arguments. If the error is already an
        # OptopusError, update its params. Otherwise, return a new error.
        if isinstance(error, OptopusError):
            for k, v in kwargs.items():
                error.params.setdefault(k, v)
            return error
        else:
            return cls(**kwargs)

class OptopusError(Kwexception):
    pass

