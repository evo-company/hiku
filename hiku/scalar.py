import uuid

from datetime import date, datetime
from typing import Any, Callable, Optional, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from hiku.graph import AbstractGraphVisitor


def scalar(
    name: Optional[str] = None, description: Optional[str] = None
) -> Callable[[Type["Scalar"]], Type["Scalar"]]:
    """
    Use @scalar decorator to set custom name and description for
    the scalar type.

    It is not mandatory to use this decorator, as long as
    you do not need to set custom name and description for the scalar type.
    """

    def _scalar(cls: Type["Scalar"]) -> Type["Scalar"]:
        cls.__type_name__ = name or cls.__name__
        cls.__description__ = description
        return cls

    return _scalar


class ScalarMeta(type):
    """Metaclass for scalar types.
    Handles `__type_name__` attribute.
    """

    __type_name__: str
    __description__: Optional[str]

    def __new__(cls, *args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
        instance = super().__new__(cls, *args, **kwargs)
        instance.__type_name__ = instance.__name__
        return instance


class Scalar(metaclass=ScalarMeta):
    """
    Base class for scalar types.

    To implement custom scalar type, subclass this class and
    implement `parse` and `serialize` class methods.

    ScalarMeta metaclass sets `__type_name__` attribute during class creation.
    """

    @classmethod
    def parse(cls, value: Any) -> Any:
        return value

    @classmethod
    def serialize(cls, value: Any) -> Any:
        return value

    @classmethod
    def accept(cls, visitor: "AbstractGraphVisitor") -> Any:
        return visitor.visit_scalar(cls)


class DateTime(Scalar):
    """
    The `DateTime` scalar type represents a datetime.datetime as UTC string.
    """

    @classmethod
    def parse(cls, value: str) -> datetime:
        return datetime.fromisoformat(value)

    @classmethod
    def serialize(cls, value: datetime) -> str:
        return value.isoformat()


class Date(Scalar):
    @classmethod
    def parse(cls, value: str) -> date:
        return date.fromisoformat(value)

    @classmethod
    def serialize(cls, value: date) -> str:
        return value.isoformat()


@scalar(description="The `UUID` scalar type represents a UUID. ")
class UUID(Scalar):
    @classmethod
    def parse(cls, value: str) -> uuid.UUID:
        return uuid.UUID(value)

    @classmethod
    def serialize(cls, value: uuid.UUID) -> str:
        return str(value)
