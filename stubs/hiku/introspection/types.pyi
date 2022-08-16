from typing import NamedTuple
from typing_extensions import TypeAlias

HashedNamedTuple: TypeAlias = NamedTuple

class SCALAR(NamedTuple):
    name: str

class OBJECT(NamedTuple):
    name: str

class DIRECTIVE(NamedTuple):
    name: str

class INPUT_OBJECT(NamedTuple):
    name: str

class LIST(NamedTuple):
    of_type: NamedTuple

class NON_NULL(NamedTuple):
    of_type: NamedTuple

class FieldIdent(NamedTuple):
    node: str
    name: str

class FieldArgIdent(NamedTuple):
    node: str
    field: str
    name: str

class InputObjectFieldIdent(NamedTuple):
    name: str
    key: str

class DirectiveArgIdent(NamedTuple):
    name: str
    arg: str
