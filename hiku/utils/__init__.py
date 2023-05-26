from functools import wraps
from typing import (
    Callable,
    TypeVar,
    List,
    Iterator,
)

from hiku.compat import ParamSpec

from .immutable import ImmutableDict, to_immutable_dict
from .cached_property import cached_property
from .const import const, Const


T = TypeVar("T")
P = ParamSpec("P")


def listify(func: Callable[P, Iterator[T]]) -> Callable[P, List[T]]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> List[T]:
        return list(func(*args, **kwargs))

    return wrapper


__all__ = [
    "ImmutableDict",
    "to_immutable_dict",
    "cached_property",
    "const",
    "Const",
]
