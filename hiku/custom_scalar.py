from dataclasses import dataclass
from typing import Any, Optional, Type


@dataclass
class ScalarInfo:
    name: str
    typ: Any


def _process_scalar(
    cls: Type,
    *,
    name: Optional[str] = None,
) -> Type:
    cls.__scalar_info__ = ScalarInfo(
        name=name or cls.__name__,
        typ=cls,
    )

    return cls


def scalar(
    cls: Optional[Type] = None,
    *,
    name: Optional[str] = None,
) -> Any:
    def wrap(cls: Type) -> Type:
        return _process_scalar(
            cls,
            name=name,
        )

    if cls is None:
        return wrap

    return wrap(cls)
