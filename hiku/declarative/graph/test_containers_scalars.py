"""Testing mypy for scalars"""

from .field import field
from .node import node


def get_name(keys: list[int], ctx: dict) -> list[str]:
    return []


def get_name_opt(keys: list[int], ctx: dict) -> list[str | None]:
    return []


def get_name_list(keys: list[int], ctx: dict) -> list[list[str]]:
    return []


def get_name_opt_list(
    keys: list[int],
    ctx: dict,
) -> list[list[str | None]]:
    return []


def get_name_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list[str] | None]:
    return []


def get_name_opt_list_opt(
    keys: list[int],
    ctx: dict,
) -> list[list[str | None] | None]:
    return []


def get_name_list_list(
    keys: list[int],
    ctx: dict,
) -> list[list[list[str]]]:
    return []


def get_name_all(
    keys: list[int],
    ctx: dict,
) -> list[list[list[str | None] | None] | None]:
    return []


@node
class TestScalars:
    __key__: int

    name: str = field(get_name)
    name_opt_co: str | None = field(get_name)
    name_opt: str | None = field(get_name_opt)
    name_list: list[str] = field(get_name_list)
    name_opt_list: list[str | None] = field(get_name_opt_list)
    name_list_opt: list[str] | None = field(get_name_list_opt)
    name_list_list: list[list[str]] = field(get_name_list_list)
    name_everything: list[list[str | None] | None] | None = field(get_name_all)
