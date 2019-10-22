import sys
import ast as _ast


PY36 = sys.version_info >= (3, 6)
PY38 = sys.version_info >= (3, 8)
try:
    import __pypy__  # noqa
    PYPY = True
except ImportError:
    PYPY = False


class _AST:

    def __getattr__(self, name):
        return getattr(_ast, name)

    if PY36:
        comprehension = _ast.comprehension
    else:
        @staticmethod
        def comprehension(target, iter, ifs, _):
            return _ast.comprehension(target, iter, ifs)

    if PY38:
        arguments = _ast.arguments
    else:
        @staticmethod
        def arguments(_, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults):  # noqa
            return _ast.arguments(args, vararg, kwonlyargs, kw_defaults, kwarg, defaults)  # noqa


ast = _AST()
