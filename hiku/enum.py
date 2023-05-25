import dataclasses
from enum import EnumMeta
from typing import Any, List, Optional, TypeVar

EnumType = TypeVar("EnumType", bound=EnumMeta)


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any


@dataclasses.dataclass
class EnumInfo:
    wrapped_cls: EnumMeta
    name: str
    values: List[EnumValue]


def _process_enum(
    cls: EnumType,
    name: Optional[str] = None,
) -> EnumType:
    if not isinstance(cls, EnumMeta):
        raise TypeError(f"{cls} is not an Enum")

    if not name:
        name = cls.__name__

    values = []
    for item in cls:  # type: ignore
        value = EnumValue(
            item.name,
            item.value,
        )
        values.append(value)

    cls.__enum_info__ = EnumInfo(  # type: ignore
        wrapped_cls=cls,
        name=name,
        values=values,
    )

    return cls


def enum(
    _cls: Optional[EnumType] = None,
    *,
    name: Optional[str] = None,
) -> Any:
    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name)

    if not _cls:
        return wrap

    return wrap(_cls)
