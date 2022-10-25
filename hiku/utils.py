import sys
from functools import wraps
from typing import (
    NewType,
    cast,
    Callable,
    Any,
    TypeVar,
    List,
    Iterator,
    Dict,
    Generic,
    NoReturn,
)

from hiku.compat import ParamSpec

Const = NewType('Const', object)


class cached_property:

    def __init__(self, func: Callable) -> None:
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj: Any, cls: Any) -> Any:
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def const(name: str) -> Const:
    t = type(name, (object,), {})
    t.__module__ = sys._getframe(1).f_globals.get('__name__', '__main__')
    return cast(Const, t)


T = TypeVar('T')
P = ParamSpec('P')


def listify(func: Callable[P, Iterator[T]]) -> Callable[P, List[T]]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> List[T]:
        return list(func(*args, **kwargs))
    return wrapper


K = TypeVar('K')
V = TypeVar('V')


class ImmutableDict(Dict, Generic[K, V]):
    _hash = None

    def __hash__(self) -> int:  # type: ignore
        if self._hash is None:
            self._hash = hash(frozenset(self.items()))
        return self._hash

    def _immutable(self) -> NoReturn:
        raise TypeError("{} object is immutable"
                        .format(self.__class__.__name__))

    __delitem__ = __setitem__ = _immutable  # type: ignore
    clear = pop = popitem = setdefault = update = _immutable  # type: ignore
