"""Testing mypy for dataclasses, idea was to check __init__ and stuff iirc"""

import typing as t
from .field import Fieldgen, Link
from .node import node


def identity(keys: list[int], ctx: dict) -> list[int]:
    return keys


def get_name(
    keys: list["DataclassNode"],
    ctx: dict,
) -> list[str]:
    return [k.name for k in keys]


def get_data(
    keys: list[None],
    ctx: dict,
) -> list["DataclassNode"]:
    return [
        DataclassNode(
            id=3,
            name="asdf",
            name_with_description="ghjk",
            some_obj=ObjNode(name="asdf"),
            some_linked_obj=Link.from_(1),
        )
    ]


def get_data_with_defaults(
    keys: list[None],
    ctx: dict,
) -> list["DataclassNode"]:
    return [DataclassNode(id=3, name="asdf", name_resolved="asdf")]


@node
class ObjNode:
    field: t.ClassVar[Fieldgen["ObjNode", dict]] = Fieldgen()

    name: str


@node
class LinkedNode:
    field: t.ClassVar[Fieldgen[int, dict]] = Fieldgen()

    id: int = field(identity)


@node
class DataclassNode:
    field: t.ClassVar[Fieldgen["DataclassNode", dict]] = Fieldgen()

    id: int
    name: str
    name_with_description: str = field(description="asdf")
    name_resolved: str = field(get_name)
    some_obj: ObjNode = field()
    some_linked_obj: Link[LinkedNode] = field()


@node
class MainNode:
    field: t.ClassVar[Fieldgen[None, dict]] = Fieldgen()

    data_full: DataclassNode = field(get_data)
    data_with_defaults: DataclassNode = field(get_data_with_defaults)
