import sys
import ast as _ast


PY3 = sys.version_info[0] == 3


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


ast = _AST()


if PY3:
    text_type = str
    string_types = str,

else:
    text_type = unicode  # noqa
    string_types = basestring,  # noqa
