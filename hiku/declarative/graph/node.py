"""Node concept and some code from strawberry :D"""

import typing

from collections.abc import Sequence


_T = typing.TypeVar("_T")


class NodeProto(typing.Protocol[_T]):
    __key__: _T


_TNode = typing.TypeVar("_TNode", bound=NodeProto)


def node(
    cls: type[_TNode] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] = (),
) -> type[_TNode]:
    return ...  # type: ignore
