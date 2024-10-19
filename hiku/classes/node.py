import dataclasses as dc
import typing
from collections.abc import Hashable
from functools import partial

import hiku.types
from hiku.classes.strings import to_snake_case
from hiku.directives import SchemaDirective

"""
@node(...)
class Human:
    id: int = field(...)
    droid: ref[Droid] = field_link(...)
"""

_T = typing.TypeVar("_T", bound=Hashable)


class NodeProto(typing.Protocol[_T]):
    __key__: _T


_TNode = typing.TypeVar("_TNode", bound=NodeProto)


@dc.dataclass
class HikuNode:
    name: str
    fields: "list[_HikuField] | list[_HikuFieldLink] | list[_HikuField | _HikuFieldLink]"
    description: str | None
    directives: list[SchemaDirective] | None
    implements: list[str] | None


def node(
    cls: type[_TNode] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: list[SchemaDirective] | None = None,
    # TODO(s.kovbasa): handle interfaces from mro
    implements: list[str] | None = None,
) -> typing.Callable[[type[_TNode]], type[_TNode]] | type[_TNode]:
    # TODO(s.kovbasa): add validation and stuff

    def _wrap_cls(
        cls: type[_TNode],
        name: str | None,
        description: str | None,
        directives: list[SchemaDirective] | None,
        implements: list[str] | None,
    ) -> type[_TNode]:
        setattr(
            cls,
            "__hiku_node__",
            HikuNode(
                name=name or cls.__name__,
                fields=_get_fields(cls),
                description=description,
                directives=directives,
                implements=implements,
            ),
        )
        return cls

    _do_wrap = partial(
        _wrap_cls,
        name=name,
        description=description,
        directives=directives,
        implements=implements,
    )

    if cls is None:
        return _do_wrap

    return _do_wrap(cls)


def _get_fields(
    cls: type[_TNode],
) -> "list[_HikuField] | list[_HikuFieldLink] | list[_HikuField | _HikuFieldLink]":
    # TODO(s.kovbasa): handle name and type from annotations
    # TODO(s.kovbasa): first process fields, then links; resolve link requires
    return []


@dc.dataclass
class _HikuField:
    func: typing.Callable
    name: str | None
    typ: type
    options: object | None
    description: str | None
    deprecated: str | None
    directives: typing.Sequence[SchemaDirective] | None


def field(
    func: typing.Callable | None = None,
    *,
    options: object | None = None,
    name: str | None = None,
    description: str | None = None,
    deprecated: str | None = None,
    directives: list | None = None,
) -> typing.Any:
    return _HikuField(
        func=func or resolve_getattr,
        name=name,
        typ=None,  # type: ignore
        options=options,
        description=description,
        deprecated=deprecated,
        directives=directives,
    )


@dc.dataclass
class _HikuFieldLink:
    func: typing.Callable
    name: str | None
    typ: type
    requires_func: typing.Callable[[], tuple] | None
    options: object | None
    description: str | None
    deprecated: str | None
    directives: typing.Sequence[SchemaDirective] | None


def field_link(
    func: typing.Callable | None = None,
    *,
    options: object | None = None,
    requires: typing.Callable[[], tuple[typing.Any, ...]] | None,
    name: str | None = None,
    description: str | None = None,
    deprecated: str | None = None,
    directives: list | None = None,
) -> typing.Any:
    return _HikuFieldLink(
        func=func or direct_link,
        name=name,
        typ=None,  # type: ignore
        requires_func=requires,
        options=options,
        description=description,
        deprecated=deprecated,
        directives=directives,
    )


def resolve_getattr(fields, tuples) -> list[list]:
    field_names = [to_snake_case(f.name) for f in fields]
    return [[getattr(t, f_name) for f_name in field_names] for t in tuples]


def direct_link(ids):
    return ids
