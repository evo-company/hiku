"""Testing mypy for dataclass nodes"""

import typing as t
from .field import Fieldgen
from .node import node


def get_obj(keys: list[int], ctx: dict) -> list["ObjNode"]:
    return []


def get_obj_opt(
    keys: list[int],
    ctx: dict,
) -> list["ObjNode" | None]:
    return []


def get_obj_list(
    keys: list[int],
    ctx: dict,
) -> list[list["ObjNode"]]:
    return []


def get_obj_opt_list(
    keys: list[int],
    ctx: dict,
) -> list[list["ObjNode" | None]]:
    return []


def get_obj_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list["ObjNode"] | None]:
    return []


def get_obj_opt_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list["ObjNode" | None] | None]:
    return []


def get_obj_list_list(
    keys: list[int],
    ctx: dict,
) -> list[list[list["ObjNode"]]]:
    return []


def get_obj_all(
    keys: list[int],
    ctx: dict,
) -> list[list[list["ObjNode" | None] | None] | None]:
    return []


@node
class ObjNode:
    field: t.ClassVar[Fieldgen["ObjNode", dict]] = Fieldgen()

    name: str


@node
class TestScalars:
    field: t.ClassVar[Fieldgen[int, dict]] = Fieldgen()

    name: "ObjNode" = field(get_obj)
    name_opt_co: "ObjNode | None" = field(get_obj)
    name_opt: "ObjNode | None" = field(get_obj_opt)
    name_list: "list[ObjNode]" = field(get_obj_list)
    name_opt_list: "list[ObjNode | None]" = field(get_obj_opt_list)
    name_list_opt: "list[ObjNode] | None" = field(get_obj_list_opt)
    name_list_list: "list[list[ObjNode]]" = field(get_obj_list_list)
    name_everything: "list[list[ObjNode | None] | None] | None" = field(
        get_obj_all
    )
