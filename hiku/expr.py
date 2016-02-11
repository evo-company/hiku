from itertools import chain
from collections import namedtuple

from .edn import loads
from .nodes import Symbol, Tuple, List, Keyword, Dict
from .utils import kw_only
from .compat import text_type, string_types
from .readers.simple import transform


class Expr(object):

    def __init__(self, name, *other, **kwargs):
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            type_, expr = None, other[0]
        elif len(other) == 2:
            type_, expr = other
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other)))

        doc, = kw_only(['doc'], kwargs)

        functions = {}
        node = to_expr(expr, functions)

        self.name = name
        self.type = type_
        self.node = node
        self.functions = functions
        self.doc = doc


_Func = namedtuple('__func__', 'expr, args')


class _DotHandler(object):

    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        return _DotHandler(Tuple([Symbol('get'), self.obj, Symbol(name)]))


class _S(object):

    def __getattr__(self, name):
        return _DotHandler(Symbol(name))


S = _S()


def to_expr(obj, fn_reg):
    if isinstance(obj, _DotHandler):
        return obj.obj
    elif isinstance(obj, _Func):
        fn_reg[obj.expr.__fn_name__] = obj.expr
        return Tuple([Symbol(obj.expr.__fn_name__)] +
                     [to_expr(arg, fn_reg) for arg in obj.args])
    elif isinstance(obj, list):
        return List(to_expr(v, fn_reg) for v in obj)
    elif isinstance(obj, dict):
        values = chain.from_iterable((Keyword(k), to_expr(v, fn_reg))
                                     for k, v in obj.items())
        return Dict(values)
    else:
        return obj


def define(*requires, **kwargs):
    def decorator(fn):
        name = kwargs.pop('_name', None)
        name = name or '{}/{}_{}'.format(fn.__module__, fn.__name__, id(fn))
        assert not kwargs, 'Unknown keyword arguments: {!r}'.format(kwargs)

        def expr(*args):
            return _Func(expr, args)

        expr.fn = fn
        expr.__fn_name__ = name

        if len(requires) == 1 and isinstance(requires[0], string_types):
            reqs_list = loads(text_type(requires[0]))
            expr.__requires__ = [transform(reqs) for reqs in reqs_list]
        else:
            expr.__requires__ = requires

        return expr
    return decorator


@define(None, None, None, _name='each')
def each(var, col, expr):
    pass


@define(None, None, None, _name='if')
def if_(test, then, else_):
    pass
