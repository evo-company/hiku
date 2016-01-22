from itertools import chain

from hiku.edn import loads
from hiku.nodes import Symbol, Tuple, List, Keyword, Dict
from hiku.compat import text_type, string_types
from hiku.readers.simple import transform


class _DotHandler(object):

    def __init__(self, obj):
        self.obj = obj

    def __getattr__(self, name):
        return _DotHandler(Tuple([Symbol('get'), self.obj, Symbol(name)]))


class _S(object):

    def __getattr__(self, name):
        return _DotHandler(Symbol(name))


S = _S()


def to_expr(arg):
    if isinstance(arg, _DotHandler):
        return arg.obj
    elif isinstance(arg, list):
        return List(to_expr(v) for v in arg)
    elif isinstance(arg, dict):
        values = chain.from_iterable((Keyword(k), to_expr(v))
                                     for k, v in arg.items())
        return Dict(values)
    else:
        return arg


def define(*requires, **kwargs):
    def decorator(fn):
        name = kwargs.pop('_name', None)
        name = name or '{}/{}'.format(fn.__module__, fn.__name__)
        assert not kwargs, 'Unknown keyword arguments: {!r}'.format(kwargs)

        def expr(*args):
            return Tuple([Symbol(name)] + [to_expr(arg) for arg in args])

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
