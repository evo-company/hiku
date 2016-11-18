from functools import wraps
from itertools import chain
from collections import namedtuple

from ..edn import loads
from ..query import Node, Link, Field
from ..types import Record, Callable, Unknown
from ..compat import text_type, string_types
from ..readers.simple import transform

from .nodes import Symbol, Tuple, List, Keyword, Dict


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
        return Tuple([Symbol(obj.expr.__def_name__)] +
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


def _query_to_types(obj):
    if isinstance(obj, Node):
        return Record[[(f.name, _query_to_types(f)) for f in obj.fields]]
    elif isinstance(obj, Link):
        return _query_to_types(obj.node)
    elif isinstance(obj, Field):
        return Unknown
    else:
        raise TypeError(type(obj))


def define(*requires, **kwargs):
    def decorator(fn):
        _name = kwargs.pop('_name', None)
        assert not kwargs, repr(kwargs)

        name = _name or '{}/{}_{}'.format(fn.__module__, fn.__name__, id(fn))

        @wraps(fn)
        def expr(*args):
            return _Func(expr, args)

        expr.__def_name__ = name
        expr.__def_body__ = fn

        if len(requires) == 1 and isinstance(requires[0], string_types):
            reqs_list = loads(text_type(requires[0]))
            expr.__def_type__ = Callable[[(_query_to_types(transform(r))
                                           if r is not None else Unknown)
                                          for r in reqs_list]]
        else:
            expr.__def_type__ = Callable[requires]

        return expr
    return decorator


@define(Unknown, Unknown, Unknown, _name='each')
def each(var, col, expr):
    pass


@define(Unknown, Unknown, Unknown, _name='if')
def if_(test, then, else_):
    pass


@define(Unknown, Unknown, Unknown, _name='if_some')
def if_some(bind, then, else_):
    pass
