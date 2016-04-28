from itertools import chain
from collections import namedtuple

from .edn import loads
from .nodes import Symbol, Tuple, List, Keyword, Dict
from .compat import text_type, string_types
from .readers.simple import transform


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


def _to_expr(obj, fn_reg):
    if isinstance(obj, _DotHandler):
        return obj.obj
    elif isinstance(obj, _Func):
        fn_reg.add(obj.expr)
        return Tuple([Symbol(obj.expr.__fn_name__)] +
                     [_to_expr(arg, fn_reg) for arg in obj.args])
    elif isinstance(obj, list):
        return List(_to_expr(v, fn_reg) for v in obj)
    elif isinstance(obj, dict):
        values = chain.from_iterable((Keyword(k), _to_expr(v, fn_reg))
                                     for k, v in obj.items())
        return Dict(values)
    else:
        return obj


def to_expr(obj):
    functions = set([])
    node = _to_expr(obj, functions)
    return node, tuple(functions)


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
            expr.__requires__ = [transform(reqs) if reqs is not None else None
                                 for reqs in reqs_list]
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
