import sys
import ast as _ast
import inspect


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


def qualname(fn):
    if inspect.ismethod(fn):
        return fn.__func__.__qualname__
    else:
        return fn.__qualname__
