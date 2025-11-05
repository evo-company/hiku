from functools import wraps
from typing import (
    Any,
    Callable,
    TYPE_CHECKING,
    TypeVar,
    Iterator,
)


from hiku.compat import ParamSpec

from .immutable import ImmutableDict, to_immutable_dict
from .const import const, Const

if TYPE_CHECKING:
    from hiku.query import Field


T = TypeVar("T")
P = ParamSpec("P")


def listify(func: Callable[P, Iterator[T]]) -> Callable[P, list[T]]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[T]:
        return list(func(*args, **kwargs))

    return wrapper


def empty_field(fields: list["Field"], ids: Any) -> Any:
    return [[None]] * len(ids)


__all__ = [
    "ImmutableDict",
    "to_immutable_dict",
    "const",
    "Const",
]
