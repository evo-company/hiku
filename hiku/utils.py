import sys


class cached_property:

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


def listify(func):
    def wrapper(*args, **kwargs):
        return list(func(*args, **kwargs))
    return wrapper
