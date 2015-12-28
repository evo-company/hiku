from itertools import chain

from hiku.nodes import Symbol, Tuple, List, Keyword, Dict


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
        return List(arg)
    elif isinstance(arg, dict):
        values = chain.from_iterable((Keyword(k), v)
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
        expr.__requires__ = requires
        return expr
    return decorator


@define('each', None, None, None, _name='each')
def each(var, col, expr):
    pass


@define(None, None, None, _name='if')
def if_(test, then, else_):
    pass
