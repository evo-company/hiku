from _typeshed import Incomplete
from typing import Any, Callable, Iterator, List, TypeVar
from typing_extensions import ParamSpec

Const: Incomplete

class cached_property:
    __doc__: Incomplete
    func: Incomplete
    def __init__(self, func: Callable) -> None: ...
    def __get__(self, obj: Any, cls: Any) -> Any: ...

def const(name: str) -> Const: ...
T = TypeVar('T')
P = ParamSpec('P')

def listify(func: Callable[P, Iterator[T]]) -> Callable[P, List[T]]: ...
