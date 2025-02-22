import abc
import dataclasses
import enum

from typing import (
    Any,
    Generic,
    Optional,
    Sequence,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from hiku.graph import AbstractGraphVisitor


@dataclasses.dataclass
class EnumValue:
    name: str
    description: Optional[str] = None
    deprecation_reason: Optional[str] = None


class BaseEnum(abc.ABC):
    def __init__(
        self,
        name: str,
        values: Sequence[Union[str, EnumValue]],
        description: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.values = [
            EnumValue(v) if isinstance(v, str) else v for v in values
        ]
        self.values_map = {v.name: v for v in self.values}

    @abc.abstractmethod
    def parse(self, value: Any) -> Any:
        raise NotImplementedError

    @abc.abstractmethod
    def serialize(self, value: Any) -> str:
        raise NotImplementedError

    def __contains__(self, item: str) -> bool:
        return item in self.values_map

    def accept(self, visitor: "AbstractGraphVisitor") -> Any:
        return visitor.visit_enum(self)


EM = TypeVar("EM", bound=enum.EnumMeta)
E = TypeVar("E", bound=enum.Enum)


class Enum(BaseEnum):
    def parse(self, value: Any) -> str:
        if value not in self:
            raise TypeError(
                "Enum '{}' can not represent value: {!r}".format(
                    self.name, value
                )
            )
        return value

    def serialize(self, value: str) -> str:
        if value not in self:
            raise TypeError(
                "Enum '{}' can not represent value: {!r}".format(
                    self.name, value
                )
            )
        return value

    @classmethod
    def from_builtin(
        cls,
        enum_cls: EM,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "EnumFromBuiltin":
        return EnumFromBuiltin(enum_cls, name or enum_cls.__name__, description)


class EnumFromBuiltin(BaseEnum, Generic[E]):
    """Enum from Python's built-in Enum class.

    When serialized, keys are used to represent possible values of graphql enum.
    When parsed, self.enum_cls[value] is used to get enum value.

    Example with default name::

        class MyEnum(enum.Enum):
            FOO = 1
            BAR = 2

        enum = Enum.from_builtin(MyEnum)

        # is equivalent to graphql enum ``enum MyEnum { FOO BAR }``

        assert enum.parse('FOO') == MyEnum.FOO
        assert enum.serialize(MyEnum.FOO) == 'FOO'

        Graph(..., enums=[enum])

    Example with custom name::

        enum = Enum.from_builtin(MyEnum, "MyCustomEnum")
    """

    def __init__(
        self, enum_cls: EM, name: str, description: Optional[str] = None
    ):
        super().__init__(name, [v for v in enum_cls.__members__], description)
        self.enum_cls = enum_cls

    def parse(self, value: Any) -> E:
        if isinstance(value, self.enum_cls):
            return value

        try:
            return self.enum_cls[value]
        except KeyError:
            raise TypeError(
                "Enum '{}' can not represent value: {!r}.".format(
                    self.name, value
                )
            )

    def serialize(self, value: Any) -> str:
        if not isinstance(value, self.enum_cls):
            raise TypeError(
                "Enum '{}' can not represent value: {!r}".format(
                    self.name, value
                )
            )

        return value.name
