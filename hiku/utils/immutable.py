from typing import Any, Generic, NoReturn, TypeVar, cast

K = TypeVar("K")
V = TypeVar("V")


class ImmutableDict(dict, Generic[K, V]):
    _hash = None

    def __hash__(self) -> int:  # type: ignore
        if self._hash is None:
            self._hash = hash(frozenset(self.items()))
        return self._hash

    def _immutable(self) -> NoReturn:
        raise TypeError(
            "{} object is immutable".format(self.__class__.__name__)
        )

    __delitem__ = __setitem__ = _immutable  # type: ignore
    clear = pop = popitem = setdefault = update = _immutable  # type: ignore


def to_immutable_dict(
    data: dict[K, V],
    exclude_keys: set[str] | None = None,
) -> ImmutableDict[K, V]:
    immutable: dict[Any, Any] = dict()
    for key in data:
        if exclude_keys and key in exclude_keys:
            continue

        if isinstance(data[key], dict):
            immutable[key] = to_immutable_dict(cast(dict[K, V], data[key]))
        else:
            immutable[key] = data[key]

    return ImmutableDict(immutable)
