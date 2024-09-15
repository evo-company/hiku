from typing import Any, Callable, List, Type

from hiku.scalar import Scalar, scalar


def federation_version(versions: List[int]) -> Callable[[Type], Type]:
    def decorator(cls: Type[_Scalar]) -> Type[_Scalar]:
        cls.__federation_versions__ = versions
        return cls

    return decorator


class _Scalar(Scalar):
    """Implements dummy `parse` and `serialize` methods for scalars."""

    __federation_versions__: List[int]

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
