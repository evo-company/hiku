"""Testing mypy for links with arbitrary list/required depth"""

import typing as t
from .field import Fieldgen, Link
from .node import node


def identity(ps: list[t.Any], ctx: dict) -> list[t.Any]:
    return ps


def get_name(keys: list[int], ctx: dict) -> list[Link["StrKeyNode"]]:
    return [Link.from_("asdf")]


def get_name_opt(keys: list[int], ctx: dict) -> list[Link["StrKeyNode"] | None]:
    return []


def get_name_list(keys: list[int], ctx: dict) -> list[list[Link["StrKeyNode"]]]:
    return []


def get_name_opt_list(
    keys: list[int],
    ctx: dict,
) -> list[list[Link["StrKeyNode"] | None]]:
    return []


def get_name_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list[Link["StrKeyNode"]] | None]:
    return []


def get_name_opt_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list[Link["StrKeyNode"] | None] | None]:
    return []


def get_name_list_list(
    keys: list[int],
    ctx: dict,
) -> list[list[list[Link["StrKeyNode"]]]]:
    return []


def get_name_all(
    keys: list[int],
    ctx: dict,
) -> list[list[list[Link["StrKeyNode"] | None] | None] | None]:
    return []


@node
class StrKeyNode:
    field: t.ClassVar[Fieldgen[str, dict]] = Fieldgen()

    name: str = field(identity)


@node
class TestObjectsKeys:
    field: t.ClassVar[Fieldgen[int, dict]] = Fieldgen()

    name: Link[StrKeyNode] = field(get_name)
    name_opt_co: Link[StrKeyNode] | None = field(get_name)
    name_opt: Link[StrKeyNode] | None = field(get_name_opt)
    name_list: list[Link[StrKeyNode]] = field(get_name_list)
    name_opt_list: list[Link[StrKeyNode] | None] = field(get_name_opt_list)
    name_list_opt: list[Link[StrKeyNode]] | None = field(get_name_list_opt)
    name_list_list: list[list[Link[StrKeyNode]]] = field(get_name_list_list)
    name_everything: list[list[Link[StrKeyNode] | None] | None] | None = field(
        get_name_all
    )
