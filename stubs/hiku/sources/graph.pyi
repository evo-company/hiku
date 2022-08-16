from .. import query as query
from ..engine import Context as Context, FieldGroup as FieldGroup, Query as Query
from ..executors.queue import Queue as Queue, TaskSet as TaskSet
from ..expr.checker import check as check, fn_types as fn_types
from ..expr.compiler import ExpressionCompiler as ExpressionCompiler
from ..expr.core import S as S, THIS as THIS, to_expr as to_expr, _DotHandler as _DotHandler, _Func as _Func
from ..expr.refs import RequirementsExtractor as RequirementsExtractor
from ..graph import Field as Field, Graph as Graph, Link as Link, Nothing as Nothing
from ..query import Node as Node, merge as merge
from ..types import Any as Any, Sequence as Sequence, TypeRef as TypeRef
from _typeshed import Incomplete
from typing import (
    Callable,
    List,
    NoReturn,
    Tuple,
    Union,
)
from typing_extensions import TypeAlias

Expr: TypeAlias = Union[_Func, _DotHandler]

class BoundExpr:
    sub_graph: Incomplete
    expr: Incomplete
    def __init__(self, sub_graph: SubGraph, expr: Expr) -> None: ...
    def __postprocess__(self, field: Field) -> None: ...
    def __call__(self, *args: Any, **kwargs: Any) -> NoReturn: ...

class CheckedExpr:
    sub_graph: Incomplete
    expr: Incomplete
    reqs: Incomplete
    proc: Incomplete
    def __init__(self, sub_graph: SubGraph, expr: Tuple, reqs: Node, proc: Callable) -> None: ...
    @property
    def __subquery__(self) -> SubGraph: ...

class SubGraph:
    graph: Incomplete
    node: Incomplete
    types: Incomplete
    def __init__(self, graph: Graph, node: str) -> None: ...
    @property
    def __subquery__(self) -> SubGraph: ...
    def __postprocess__(self, field: Field) -> None: ...
    def __call__(self, fields: List[FieldGroup], ids: List, queue: Queue, ctx: Context, task_set: TaskSet) -> Callable[[], List[List]]: ...
    def compile(self, expr: Expr) -> BoundExpr: ...
    def c(self, expr: Expr) -> BoundExpr: ...
