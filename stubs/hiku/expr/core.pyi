from ..edn import loads as loads
from ..query import Field as Field, Link as Link, Node as Node
from ..readers.simple import transform as transform
from ..types import Any as Any, Callable as Callable, Record as Record
from .nodes import Dict as Dict, Keyword as Keyword, List as List, Symbol as Symbol, Tuple as Tuple
from _typeshed import Incomplete
from typing import NamedTuple

THIS: str

class _Func(NamedTuple):
    expr: Incomplete
    args: Incomplete

class _DotHandler:
    obj: Incomplete
    def __init__(self, obj) -> None: ...
    def __getattr__(self, name): ...

class _S:
    def __getattr__(self, name): ...

S: Incomplete

def to_expr(obj): ...
def define(*types, **kwargs): ...
def each(var, col, expr) -> None: ...
def if_(test, then, else_) -> None: ...
def if_some(bind, then, else_) -> None: ...
