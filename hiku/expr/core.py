"""
hiku.expr.core
~~~~~~~~~~~~~~

Expression building blocks

"""

import typing as t

from functools import wraps
from itertools import chain
from collections import namedtuple

from ..compat import ParamSpec

from ..query import Node as QueryNode, Link, Field, Base as QueryBase
from ..types import (
    Record,
    Callable,
    Any,
    GenericMeta,
)

from .nodes import Symbol, Tuple, List, Keyword, Dict, Node


THIS = "this"

_Func = namedtuple("_Func", "expr, args")


class DotHandler:
    def __init__(self, obj: t.Union[Symbol, Tuple]) -> None:
        self.obj = obj

    def __repr__(self) -> str:
        return repr(self.obj)

    def __getattr__(self, name: str) -> "DotHandler":
        return DotHandler(Tuple([Symbol("get"), self.obj, Symbol(name)]))


# for backward compatibility
_DotHandler = DotHandler


class _S:
    def __getattr__(self, name: str) -> DotHandler:
        return DotHandler(Symbol(name))


#: Helper object to represent symbols in expressions. ``S.foo.bar`` in
#: expressions is equivalent to ``foo.bar`` in the regular Python.
S = _S()


def _to_expr(
    obj: t.Union[DotHandler, _Func, t.List, t.Dict, Node],
    fn_reg: t.Set[t.Callable],
) -> Node:
    if isinstance(obj, DotHandler):
        return obj.obj
    elif isinstance(obj, _Func):
        fn_reg.add(obj.expr)
        values: t.List[Node] = [Symbol(obj.expr.__def_name__)]
        values.extend(_to_expr(arg, fn_reg) for arg in obj.args)
        return Tuple(values)
    elif isinstance(obj, list):
        return List([_to_expr(v, fn_reg) for v in obj])
    elif isinstance(obj, dict):
        values = list(
            chain.from_iterable(
                (Keyword(k), _to_expr(v, fn_reg)) for k, v in obj.items()
            )
        )
        return Dict(values)
    else:
        return obj


def to_expr(
    obj: t.Union[DotHandler, _Func]
) -> t.Tuple[Node, t.Tuple[t.Callable, ...]]:
    functions: t.Set[t.Callable] = set([])
    node = _to_expr(obj, functions)
    return node, tuple(functions)


def _query_to_types(
    obj: QueryBase,
) -> t.Union[t.Type[Any], t.Type[Record]]:
    if isinstance(obj, QueryNode):
        return Record[[(f.name, _query_to_types(f)) for f in obj.fields]]
    elif isinstance(obj, Link):
        return _query_to_types(obj.node)
    elif isinstance(obj, Field):
        return Any
    else:
        raise TypeError(type(obj))


T = t.TypeVar("T")
P = ParamSpec("P")


def define(
    *types: GenericMeta, **kwargs: str
) -> t.Callable[[t.Callable[P, T]], t.Callable[P, _Func]]:
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

    def decorator(fn: t.Callable[P, T]) -> t.Callable[P, _Func]:
        _name = kwargs.pop("_name", None)
        assert not kwargs, repr(kwargs)

        name = _name or "{}/{}_{}".format(fn.__module__, fn.__name__, id(fn))

        @wraps(fn)
        def expr(*args: P.args, **kw: P.kwargs) -> _Func:
            return _Func(expr, args)

        expr.__def_name__ = name  # type: ignore[attr-defined]
        expr.__def_body__ = fn  # type: ignore[attr-defined]
        expr.__def_type__ = Callable[types]  # type: ignore[attr-defined]
        return expr

    return decorator


@define(Any, Any, Any, _name="each")
def each(var: DotHandler, col: DotHandler, expr: DotHandler) -> None:
    """Returns a list of the results of the expression evaluation for every
    item of the sequence provided.

    Example:

    .. code-block:: python

        each(S.x, S.collection, S.x.name)

    Equivalent in the regular Python (only for reference):

    .. code-block:: python

        [x.name for x in collection]

    """


@define(Any, Any, Any, _name="if")
def if_(test: t.Any, then: t.Any, else_: t.Any) -> None:
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


@define(Any, Any, Any, _name="if_some")
def if_some(bind: t.List, then: _Func, else_: t.Any) -> None:
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
