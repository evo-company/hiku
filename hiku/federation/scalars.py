from typing import Any, Callable

from hiku.scalar import Scalar, scalar


def federation_version(versions: list[int]) -> Callable[[type], type]:
    def decorator(cls: type[_Scalar]) -> type[_Scalar]:
        cls.__federation_versions__ = versions
        return cls

    return decorator


class _Scalar(Scalar):
    """Implements dummy `parse` and `serialize` methods for scalars."""

    __federation_versions__: list[int]

    @classmethod
    def parse(cls, value: str) -> Any:
        return value

    @classmethod
    def serialize(cls, value: str) -> Any:
        return value


@federation_version([2])
class _Any(_Scalar): ...


@federation_version([1, 2])
@scalar(name="_FieldSet")
class FieldSet(_Scalar): ...


@federation_version([2])
@scalar(name="link__Import")
class LinkImport(_Scalar): ...
