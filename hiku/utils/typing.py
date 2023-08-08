import sys

from enum import EnumMeta
from typing import Any, Type, Union

from hiku.introspection import types as int_types
from hiku.scalar import Scalar


def is_union(annotation: object) -> bool:
    # this check is needed because unions declared with the new syntax `A | B`
    # don't have a `__origin__` property on them, but they are instances of
    # `UnionType`, which is only available in Python 3.10+
    if sys.version_info >= (3, 10):
        from types import UnionType

        if isinstance(annotation, UnionType):
            return True

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == Union


def is_optional(annotation: Type) -> bool:
    """Returns True if the annotation is Optional[SomeType]"""

    # Optionals are represented as unions

    if not is_union(annotation):
        return False

    types_ = annotation.__args__

    # A Union to be optional needs to have at least one None type
    return any(x == None.__class__ for x in types_)  # noqa: E711


def is_list(annotation: object) -> bool:
    """Returns True if annotation is a List"""

    annotation_origin = getattr(annotation, "__origin__", None)

    return annotation_origin == list


def builtin_to_introspection_type(typ: Any) -> Any:
    def convert(typ_: Any) -> Any:  # SCALAR
        if typ_ is int:
            return int_types.SCALAR("Int")
        elif typ_ is str:
            return int_types.SCALAR("String")
        elif typ_ is bool:
            return int_types.SCALAR("Boolean")
        elif typ_ is float:
            return int_types.SCALAR("Float")
        elif is_optional(typ_):
            return convert(typ_.__args__[0])
        elif is_list(typ_):
            return int_types.LIST(convert(typ_.__args__[0]))
        elif issubclass(typ_, Scalar):
            return int_types.SCALAR(typ_.__type_name__)
        elif isinstance(typ_, EnumMeta):
            return int_types.ENUM(
                typ_.__name__,
                [v for v in typ_.__members__],
            )
        else:
            raise TypeError(f"Unknown type: {typ_}")

    optional = False
    if is_optional(typ):
        optional = True

    intr_type = convert(typ)

    if optional:
        return intr_type

    return int_types.NON_NULL(intr_type)
