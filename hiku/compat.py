import sys
import ast as _ast


PY3 = sys.version_info[0] == 3


class _AST(object):

    def __getattr__(self, name):
        return getattr(_ast, name)

    if not PY3:
        @staticmethod
        def Name(id, ctx):
            return _ast.Name(str(id), ctx)

        @staticmethod
        def Attribute(value, attr, ctx):
            return _ast.Attribute(value, str(attr), ctx)


ast = _AST()


if PY3:
    texttype = str

else:
    texttype = unicode
