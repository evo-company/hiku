import sys
import ast as _ast
import inspect


PY3 = sys.version_info[0] == 3
PY35 = sys.version_info >= (3, 5)
PY36 = sys.version_info >= (3, 6)


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class metaclass(meta):

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


class _AST(object):

    def __getattr__(self, name):
        return getattr(_ast, name)

    if PY3:
        @staticmethod
        def arguments(args, vararg, kwarg, defaults):
            return _ast.arguments(args, vararg, [], [], kwarg, defaults)

        @staticmethod
        def arg(arg):
            return _ast.arg(arg, None)

        if PY35:
            @staticmethod
            def Call(func, args, keywords, starargs, kwargs):
                return _ast.Call(func, args, keywords)
        else:
            Call = _ast.Call

    else:
        @staticmethod
        def Name(id, ctx):
            return _ast.Name(str(id), ctx)

        @staticmethod
        def Attribute(value, attr, ctx):
            return _ast.Attribute(value, str(attr), ctx)

        @staticmethod
        def arguments(args, vararg, kwarg, defaults):
            return _ast.arguments(args, vararg, kwarg, defaults)

        @staticmethod
        def arg(arg):
            return _ast.Name(str(arg), _ast.Param())

        Call = _ast.Call


ast = _AST()


if PY3:
    text_type = str
    string_types = str,

    def qualname(fn):
        if inspect.ismethod(fn):
            return fn.__func__.__qualname__
        else:
            return fn.__qualname__

else:
    text_type = unicode  # noqa
    string_types = basestring,  # noqa

    def qualname(fn):
        if inspect.ismethod(fn):
            return '{}.{}'.format(fn.im_class.__name__, fn.im_func.__name__)
        else:
            return fn.__name__


if PY35:
    from ._compat import async_wrapper

    async_wrapper = async_wrapper
else:
    def async_wrapper(func):
        raise RuntimeError('Can not use async/await in Python < 3.5')
