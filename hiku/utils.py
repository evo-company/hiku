import sys

from .compat import qualname


def kw_only(fn, mapping, required, optional=None):
    d = mapping.copy()

    missing = [a for a in required if a not in d]
    if len(missing) == 1:
        raise TypeError('{}() missing 1 required keyword-only argument: {!r}'
                        .format(qualname(fn), missing[0]))
    elif missing:
        names = ', '.join(map(repr, missing[:-1]))
        raise TypeError('{}() missing {} required keyword-only arguments: {} '
                        'and {}'.format(qualname(fn), len(missing), names,
                                        repr(missing[-1])))

    result = [d.pop(key) for key in required]
    result.extend(d.pop(key, default) for key, default in (optional or ()))

    unexpected = sorted(d)
    if len(unexpected) == 1:
        name, = d
        raise TypeError('{}() got 1 unexpected keyword argument: {!r}'
                        .format(qualname(fn), name))
    elif unexpected:
        names = ', '.join(map(repr, unexpected[:-1]))
        raise TypeError('{}() got {} unexpected keyword arguments: {} and {}'
                        .format(qualname(fn), len(unexpected), names,
                                repr(unexpected[-1])))

    return result


class cached_property(object):

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def const(name):
    t = type(name, (object,), {})
    t.__module__ = sys._getframe(1).f_globals.get('__name__', '__main__')
    return t
