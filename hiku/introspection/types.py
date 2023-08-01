from collections import namedtuple
from typing import (
    Type,
    Any,
    NamedTuple,
)

from hiku.compat import TypeAlias


# Mark everything that _namedtuple creates as HashedNamedTuple,
# so it will be easier to refactor types later
HashedNamedTuple: TypeAlias = NamedTuple


def _namedtuple(typename: str, field_names: str) -> Type:
    """Fixes hashing for different tuples with same content"""
    base = namedtuple(typename, field_names)  # type: ignore[misc]

    def __hash__(self: Any) -> int:
        return hash((self.__class__, super(base, self).__hash__()))

    return type(
        typename,
        (base,),
        {
            "__slots__": (),
            "__hash__": __hash__,
        },
    )


SCALAR = _namedtuple("SCALAR", "name")
OBJECT = _namedtuple("OBJECT", "name")
UNION = _namedtuple("UNION", "name possible_types")
INTERFACE = _namedtuple("INTERFACE", "name possible_types")
DIRECTIVE = _namedtuple("DIRECTIVE", "name")
INPUT_OBJECT = _namedtuple("INPUT_OBJECT", "name")
LIST = _namedtuple("LIST", "of_type")
NON_NULL = _namedtuple("NON_NULL", "of_type")
ENUM = _namedtuple("ENUM", "name of_types")
EnumValueIdent = _namedtuple("EnumValueIdent", "enum_name value_name")

FieldIdent = _namedtuple("FieldIdent", "node, name")
FieldArgIdent = _namedtuple("FieldArgIdent", "node, field, name")
InputObjectFieldIdent = _namedtuple("InputObjectFieldIdent", "name, key")
DirectiveArgIdent = _namedtuple("DirectiveArgIdent", "name, arg")
