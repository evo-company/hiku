"""Resolver typing magic"""

import typing

from .node import NodeProto
from .option import TOpts, TOptsVar


_T = typing.TypeVar("_T")
_T_contra = typing.TypeVar("_T_contra", contravariant=True)
_TI = typing.TypeVar("_TI")
_TContext = typing.TypeVar("_TContext", bound=dict)


class Field(typing.Generic[_T_contra]):
    name: str
    typ: type[_T_contra]
    options: TOpts | None = None
    description: str | None = None
    directives: list | None = None

    def accept(self, visitor: typing.Any) -> typing.Any:
        return visitor.visit_field_decl(self)


class Link(typing.Generic[_T_contra]):
    """
    contravariant to support following:

    a: Link[NodeProto[_T]] = ...

    class Company(NodeProto[int]):
        ...

    class Product:
        company: Link[Company] = a

    """

    @classmethod
    def from_(cls, val: _TI) -> "Link[NodeProto[_TI, typing.Any]]":
        ...


class Fieldgen(typing.Generic[_TI, _TContext]):
    @typing.overload
    def __call__(
        self,
        resolve: typing.Callable[[list[_TI], _TContext], list[_T]],
        options: None = None,
        description: str | None = None,
        directives: list | None = None,
        name: str | None = None,
        preload: None = None,
    ) -> _T:
        ...

    @typing.overload
    def __call__(
        self,
        resolve: typing.Callable[[list[_TI], _TContext, TOptsVar], list[_T]],
        options: type[TOptsVar],
        description: str | None = None,
        directives: list | None = None,
        name: str | None = None,
        preload: None = None,
    ) -> _T:
        ...

    @typing.overload
    def __call__(
        self,
        resolve: None = None,
        options: None = None,
        description: str | None = None,
        directives: list | None = None,
        name: str | None = None,
        preload: typing.Callable[[list[_TI], _TContext], list] | None = None,
    ) -> typing.Any:
        ...

    def __call__(
        self,
        resolve: typing.Callable[[list[_TI], _TContext, TOptsVar], list]
        | typing.Callable[[list[_TI], _TContext], list]
        | None = None,
        options: type[TOptsVar] | None = None,
        description: str | None = None,
        directives: list | None = None,
        name: str | None = None,
        preload: typing.Callable[[list[_TI], _TContext], list] | None = None,
    ) -> typing.Any:
        return ...
