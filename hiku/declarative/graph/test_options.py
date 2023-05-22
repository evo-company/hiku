"""Testing mypy for options"""

import typing as t
from .field import Fieldgen
from .node import node
from .option import options, opt


@options
class NameOptions:
    yo: str
    from_: int = opt(name="from")
    lol: str | None = opt(default=None)


def get_name(keys: list[int], ctx: dict, opts: NameOptions) -> list[str]:
    return []


@node
class TestOptions:
    field: t.ClassVar[Fieldgen[int, dict]] = Fieldgen()

    name: str = field(get_name, options=NameOptions)
