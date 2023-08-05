from typing import Any

from hiku.scalar import Scalar, scalar


class _Scalar(Scalar):
    """Implements dummy `parse` and `serialize` methods for scalars."""

    @classmethod
    def parse(cls, value: str) -> Any:
        return value

    @classmethod
    def serialize(cls, value: str) -> Any:
        return value


class _Any(_Scalar):
    ...


@scalar(name="_FieldSet")
class FieldSet(_Scalar):
    ...


@scalar(name="link__Import")
class LinkImport(_Scalar):
    ...
