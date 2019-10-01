"""
    hiku.expr.core
    ~~~~~~~~~~~~~~

    Expression building blocks

"""
from functools import wraps
from itertools import chain
from collections import namedtuple

from ..edn import loads
from ..query import Node, Link, Field
from ..types import Record, Callable, Any
from ..readers.simple import transform

from .nodes import Symbol, Tuple, List, Keyword, Dict


THIS = 'this'

_Func = namedtuple('__func__', 'expr, args')


class _DotHandler:

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return repr(self.obj)

    def __getattr__(self, name):
        return _DotHandler(Tuple([Symbol('get'), self.obj, Symbol(name)]))


class _S:

    def __getattr__(self, name):
        return _DotHandler(Symbol(name))


#: Helper object to represent symbols in expressions. ``S.foo.bar`` in
#: expressions is equivalent to ``foo.bar`` in the regular Python.
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
        return Any
    else:
        raise TypeError(type(obj))


def define(*types, **kwargs):
    """Annotates function arguments with types.

    These annotations are used to type-check expressions and to analyze,
    which data is used from provided arguments.

    Example:

    .. code-block:: python

        @define(Record[{'id': Integer, 'name': String}])
        def image_url(image):
            return 'http://example.com/{id}-{name}'.format(id=image['id'],
                                                           name=image['name'])

    Here ``image_url`` function accepts an object as argument, and is using two
    of it's fields: ``id`` field of type ``Integer`` and ``name`` field of type
    ``String``. Hiku will check that this function will be used only with
    objects having at least such two fields.

    This annotation also gives ability for Hiku to build a query for low-level
    graph.
    """
    def decorator(fn):
        _name = kwargs.pop('_name', None)
        assert not kwargs, repr(kwargs)

        name = _name or '{}/{}_{}'.format(fn.__module__, fn.__name__, id(fn))

        @wraps(fn)
        def expr(*args):
            return _Func(expr, args)

        expr.__def_name__ = name
        expr.__def_body__ = fn

        if len(types) == 1 and isinstance(types[0], str):
            reqs_list = loads(str(types[0]))
            expr.__def_type__ = Callable[[(_query_to_types(transform(r))
                                           if r is not None else Any)
                                          for r in reqs_list]]
        else:
            expr.__def_type__ = Callable[types]

        return expr
    return decorator


@define(Any, Any, Any, _name='each')
def each(var, col, expr):
    """Returns a list of the results of the expression evaluation for every
    item of the sequence provided.

    Example:

    .. code-block:: python

        each(S.x, S.collection, S.x.name)

    Equivalent in the regular Python (only for reference):

    .. code-block:: python

        [x.name for x in collection]

    """


@define(Any, Any, Any, _name='if')
def if_(test, then, else_):
    """Checks condition and continues to evaluate one of the two expressions
    provided.

    Example:

    .. code-block:: python

        if_(S.value, 'truish', 'falsish')

    Equivalent in the regular Python (only for reference):

    .. code-block:: python

        if value:
            return 'truish'
        else:
            return 'falsish'

    """


@define(Any, Any, Any, _name='if_some')
def if_some(bind, then, else_):
    """Used to unpack values with ``Optional`` types and using them safely in
    expressions.

    Example:

    .. code-block:: python

        if_some([S.img, S.this.image],
                image_url(S.img),
                'http://example.com/no-photo.jpg')

    Equivalent in the regular Python (only for reference):

    .. code-block:: python

        if this.image is not None:
            img = this.image
            return image_url(img)
        else:
            return 'http://example.com/no-photo.jpg'

    If ``S.this.image`` has a type ``Optional[TypeRef['Image']]``, ``S.img``
    variable will have a type ``TypeRef['Image']`` and it will be available only
    in "then"-expression, which will be evaluated only if ``S.this.image``
    wouldn't be ``None``. Otherwise "else"-expression will be
    evaluated.
    """
