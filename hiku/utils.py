import sys


_undefined = object()


def kw_only(mapping, required, optional=None):
    d = mapping.copy()
    result = []
    for arg in required:
        value = d.pop(arg, _undefined)
        if value is _undefined:
            raise TypeError('Required keyword argument {!r} not specified'
                            .format(arg))
        result.append(value)
    if optional is not None:
        for key in optional:
            value = d.pop(key, None)
            result.append(value)
    if d:
        raise TypeError('Unknown keyword arguments: {}'
                        .format(', '.join(d.keys())))
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
