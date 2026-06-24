"""Testing typings for option"""

from .field import field
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
    __key__: int

    name: str = field(get_name, options=NameOptions)
