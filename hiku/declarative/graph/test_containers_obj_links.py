"""Testing mypy for links with arbitrary list/required depth"""

import typing
from .field import field, link
from .node import node


def identity(ps: list[typing.Any], ctx: dict) -> list[typing.Any]:
    return ps


def get_name(keys: list[int], ctx: dict) -> list[link["StrKeyNode"]]:
    return [link.from_("asdf")]


def get_name_opt(keys: list[int], ctx: dict) -> list[link["StrKeyNode"] | None]:
    return []


def get_name_list(keys: list[int], ctx: dict) -> list[list[link["StrKeyNode"]]]:
    return []


def get_name_opt_list(
    keys: list[int],
    ctx: dict,
) -> list[list[link["StrKeyNode"] | None]]:
    return []


def get_name_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list[link["StrKeyNode"]] | None]:
    return []


def get_name_opt_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list[link["StrKeyNode"] | None] | None]:
    return []


def get_name_list_list(
    keys: list[int],
    ctx: dict,
) -> list[list[list[link["StrKeyNode"]]]]:
    return []


def get_name_all(
    keys: list[int],
    ctx: dict,
) -> list[list[list[link["StrKeyNode"] | None] | None] | None]:
    return []


@node
class StrKeyNode:
    __key__: str

    name: str = field(identity)


@node
class TestObjectsKeys:
    __key__: int

    name: link[StrKeyNode] = field(get_name)
    name_opt_co: link[StrKeyNode] | None = field(get_name)
    name_opt: link[StrKeyNode] | None = field(get_name_opt)
    name_list: list[link[StrKeyNode]] = field(get_name_list)
    name_opt_list: list[link[StrKeyNode] | None] = field(get_name_opt_list)
    name_list_opt: list[link[StrKeyNode]] | None = field(get_name_list_opt)
    name_list_list: list[list[link[StrKeyNode]]] = field(get_name_list_list)
    name_everything: list[list[link[StrKeyNode] | None] | None] | None = field(
        get_name_all
    )
