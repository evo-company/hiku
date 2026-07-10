"""Resolver typing magic"""

import typing

from .node import NodeProto
from .option import TOptsVar
import hiku.query


_T = typing.TypeVar("_T")
_T_contra = typing.TypeVar("_T_contra", contravariant=True)
_TI = typing.TypeVar("_TI")
_TContext = typing.TypeVar("_TContext", bound=dict)


class link(typing.Generic[_T_contra]):
    """
    contravariant to support following:

    a: link[NodeProto[_T]] = ...

    class Company(NodeProto[int]):
        ...

    class Product:
        company: link[Company] = a

    """

    @classmethod
    def from_(cls, val: _T_contra) -> "link[NodeProto[_T_contra]]":
        ...


_TPreresolver = typing.Callable[
    [list[hiku.query.Field], list[_TI], _TContext],
    list[typing.Any],
]


@typing.overload
def field(
    resolve: None = None,
    options: None = None,
    description: str | None = None,
    directives: list | None = None,
    name: str | None = None,
    preresolve: _TPreresolver | None = None,
) -> typing.Any:
    ...


@typing.overload
def field(
    resolve: typing.Callable[[list, _TContext], list[_T]],
    options: None = None,
    description: str | None = None,
    directives: list | None = None,
    name: str | None = None,
    preresolve: _TPreresolver | None = None,
) -> _T:
    ...


@typing.overload
def field(
    resolve: typing.Callable[[list, _TContext, TOptsVar], list[_T]],
    options: type[TOptsVar],
    description: str | None = None,
    directives: list | None = None,
    name: str | None = None,
    preresolve: _TPreresolver | None = None,
) -> _T:
    ...


def field(
    resolve: typing.Callable[[list[_TI], _TContext, TOptsVar], list]
    | typing.Callable[[list[_TI], _TContext], list]
    | None = None,
    options: type[TOptsVar] | None = None,
    description: str | None = None,
    directives: list | None = None,
    name: str | None = None,
    preresolve: _TPreresolver | None = None,
) -> typing.Any:
    return ...
