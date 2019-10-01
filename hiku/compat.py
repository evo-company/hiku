import sys
import ast as _ast
import inspect


PY3 = sys.version_info[0] == 3
PY35 = sys.version_info >= (3, 5)
PY36 = sys.version_info >= (3, 6)
try:
    import __pypy__  # noqa
    PYPY = True
except ImportError:
    PYPY = False


class _AST:

    def __getattr__(self, name):
        return getattr(_ast, name)

    if PY36:
        @staticmethod
        def comprehension(target, iter, ifs, is_async=0):
            return _ast.comprehension(target, iter, ifs, is_async)
    else:
        comprehension = _ast.comprehension


ast = _AST()


if PY3:
    import collections.abc as collections_abc

    text_type = str
    string_types = str,
    integer_types = int,

    def qualname(fn):
        if inspect.ismethod(fn):
            return fn.__func__.__qualname__
        else:
            return fn.__qualname__

else:
    import collections as collections_abc

    text_type = unicode  # noqa
    string_types = basestring,  # noqa
    integer_types = int, long  # noqa

    def qualname(fn):
        if inspect.ismethod(fn):
            return '{}.{}'.format(fn.im_class.__name__, fn.im_func.__name__)
        else:
            return fn.__name__


Sequence = collections_abc.Sequence
